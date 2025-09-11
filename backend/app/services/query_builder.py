from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, Query, joinedload
from sqlalchemy import and_, or_, func, text, desc, asc
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.tag import Tag
from app.schemas.ip_address import IPSearchRequest
import ipaddress
from datetime import datetime


class IPQueryBuilder:
    """IP地址搜索查询构建器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_query = db.query(IPAddress).join(Subnet, IPAddress.subnet_id == Subnet.id).options(joinedload(IPAddress.subnet))
    
    def build_search_query(self, search_request: IPSearchRequest) -> Tuple[Query, Query]:
        """构建搜索查询和计数查询"""
        query = self.base_query
        # 确保count_query也包含必要的联接
        count_query = self.db.query(func.count(IPAddress.id)).join(Subnet, IPAddress.subnet_id == Subnet.id)
        
        # 应用过滤条件
        filters = self._build_filters(search_request)
        if filters:
            query = query.filter(and_(*filters))
            count_query = count_query.filter(and_(*filters))
        
        # 应用排序
        query = self._apply_sorting(query, search_request)
        
        # 应用分页
        query = self._apply_pagination(query, search_request)
        
        return query, count_query
    
    def _build_filters(self, search_request: IPSearchRequest) -> List:
        """构建过滤条件"""
        filters = []
        
        # 文本搜索 - 支持多字段模糊匹配
        if search_request.query:
            text_filters = self._build_text_search_filters(search_request.query)
            if text_filters:
                filters.append(or_(*text_filters))
        
        # 网段过滤
        if search_request.subnet_id:
            filters.append(IPAddress.subnet_id == search_request.subnet_id)
        
        # 状态过滤
        if search_request.status:
            filters.append(IPAddress.status == search_request.status)
        
        # 设备类型过滤
        if search_request.device_type:
            filters.append(IPAddress.device_type.ilike(f"%{search_request.device_type}%"))
        
        # 位置过滤
        if search_request.location:
            filters.append(IPAddress.location.ilike(f"%{search_request.location}%"))
        
        # 分配部门过滤（精确匹配）
        if search_request.assigned_to:
            filters.append(IPAddress.assigned_to == search_request.assigned_to)
        
        # MAC地址过滤
        if search_request.mac_address:
            filters.append(IPAddress.mac_address.ilike(f"%{search_request.mac_address}%"))
        
        # 使用人过滤
        if search_request.user_name:
            filters.append(IPAddress.user_name.ilike(f"%{search_request.user_name}%"))
        
        # IP地址范围过滤
        if search_request.ip_range_start and search_request.ip_range_end:
            ip_range_filter = self._build_ip_range_filter(
                search_request.ip_range_start, 
                search_request.ip_range_end
            )
            if ip_range_filter is not None:
                filters.append(ip_range_filter)
        
        # 分配日期范围过滤
        if search_request.allocated_date_start or search_request.allocated_date_end:
            date_filter = self._build_date_range_filter(
                search_request.allocated_date_start,
                search_request.allocated_date_end
            )
            if date_filter is not None:
                filters.append(date_filter)
        
        # 标签过滤
        if search_request.tags:
            tag_filter = self._build_tag_filter(search_request.tags)
            if tag_filter:
                filters.append(tag_filter)
        
        return filters
    
    def _build_text_search_filters(self, query: str) -> List:
        """构建文本搜索过滤条件"""
        search_terms = query.strip().split()
        filters = []
        
        for term in search_terms:
            term_filters = [
                IPAddress.ip_address.ilike(f"%{term}%"),
                IPAddress.user_name.ilike(f"%{term}%"),
                IPAddress.mac_address.ilike(f"%{term}%"),
                IPAddress.device_type.ilike(f"%{term}%"),
                # 对于部门字段，优先精确匹配，然后模糊匹配
                or_(
                    IPAddress.assigned_to == term,  # 精确匹配
                    IPAddress.assigned_to.ilike(f"%{term}%")  # 模糊匹配作为备选
                ),
                IPAddress.location.ilike(f"%{term}%"),
                IPAddress.description.ilike(f"%{term}%"),
                # 支持网段搜索
                Subnet.network.ilike(f"%{term}%"),
                Subnet.description.ilike(f"%{term}%")
            ]
            filters.append(or_(*term_filters))
        
        return filters
    
    def _build_ip_range_filter(self, start_ip: str, end_ip: str):
        """构建IP地址范围过滤条件"""
        try:
            start_addr = ipaddress.ip_address(start_ip)
            end_addr = ipaddress.ip_address(end_ip)
            
            # 使用INET_ATON函数进行IP地址范围比较（MySQL）
            return and_(
                func.inet_aton(IPAddress.ip_address) >= func.inet_aton(start_ip),
                func.inet_aton(IPAddress.ip_address) <= func.inet_aton(end_ip)
            )
        except ValueError:
            return None
    
    def _build_date_range_filter(self, start_date: Optional[str], end_date: Optional[str]):
        """构建日期范围过滤条件"""
        filters = []
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                filters.append(IPAddress.allocated_at >= start_dt)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                filters.append(IPAddress.allocated_at <= end_dt)
            except ValueError:
                pass
        
        return and_(*filters) if filters else None
    
    def _build_tag_filter(self, tags: List[str]):
        """构建标签过滤条件"""
        # 查找包含指定标签的IP地址
        return IPAddress.id.in_(
            self.db.query(IPAddress.id)
            .join(IPAddress.tags)
            .filter(Tag.name.in_(tags))
            .subquery()
        )
    
    def _apply_sorting(self, query: Query, search_request: IPSearchRequest) -> Query:
        """应用排序"""
        sort_field = getattr(IPAddress, search_request.sort_by, IPAddress.ip_address)
        
        if search_request.sort_by == "ip_address":
            # IP地址特殊排序 - 按数值排序而非字符串排序
            if search_request.sort_order == "desc":
                query = query.order_by(desc(func.inet_aton(IPAddress.ip_address)))
            else:
                query = query.order_by(func.inet_aton(IPAddress.ip_address))
        else:
            # 其他字段正常排序
            if search_request.sort_order == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))
        
        return query
    
    def _apply_pagination(self, query: Query, search_request: IPSearchRequest) -> Query:
        """应用分页"""
        return query.offset(search_request.skip).limit(search_request.limit)


class SearchHistoryService:
    """搜索历史服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_search(self, user_id: int, search_params: dict, search_name: Optional[str] = None) -> int:
        """保存搜索历史"""
        from app.models.search_history import SearchHistory
        
        # 检查是否已存在相同的搜索
        existing = (
            self.db.query(SearchHistory)
            .filter(
                and_(
                    SearchHistory.user_id == user_id,
                    SearchHistory.search_params == search_params
                )
            )
            .first()
        )
        
        if existing:
            # 更新使用次数
            existing.used_count += 1
            existing.updated_at = func.now()
            self.db.commit()
            return existing.id
        else:
            # 创建新的搜索历史
            search_history = SearchHistory(
                user_id=user_id,
                search_name=search_name,
                search_params=search_params,
                used_count=1
            )
            self.db.add(search_history)
            self.db.commit()
            self.db.refresh(search_history)
            return search_history.id
    
    def get_user_search_history(self, user_id: int, limit: int = 20) -> List:
        """获取用户搜索历史"""
        from app.models.search_history import SearchHistory
        
        return (
            self.db.query(SearchHistory)
            .filter(SearchHistory.user_id == user_id)
            .order_by(desc(SearchHistory.updated_at))
            .limit(limit)
            .all()
        )
    
    def get_user_favorite_searches(self, user_id: int) -> List:
        """获取用户收藏的搜索"""
        from app.models.search_history import SearchHistory
        
        return (
            self.db.query(SearchHistory)
            .filter(
                and_(
                    SearchHistory.user_id == user_id,
                    SearchHistory.is_favorite == True
                )
            )
            .order_by(desc(SearchHistory.used_count))
            .all()
        )
    
    def toggle_favorite(self, user_id: int, search_id: int) -> bool:
        """切换搜索收藏状态"""
        from app.models.search_history import SearchHistory
        
        search = (
            self.db.query(SearchHistory)
            .filter(
                and_(
                    SearchHistory.id == search_id,
                    SearchHistory.user_id == user_id
                )
            )
            .first()
        )
        
        if search:
            search.is_favorite = not search.is_favorite
            self.db.commit()
            return search.is_favorite
        
        return False
    
    def update_search_name(self, user_id: int, search_id: int, search_name: str) -> bool:
        """更新搜索名称"""
        from app.models.search_history import SearchHistory
        
        search = (
            self.db.query(SearchHistory)
            .filter(
                and_(
                    SearchHistory.id == search_id,
                    SearchHistory.user_id == user_id
                )
            )
            .first()
        )
        
        if search:
            search.search_name = search_name
            self.db.commit()
            return True
        
        return False
    
    def delete_search(self, user_id: int, search_id: int) -> bool:
        """删除搜索历史"""
        from app.models.search_history import SearchHistory
        
        search = (
            self.db.query(SearchHistory)
            .filter(
                and_(
                    SearchHistory.id == search_id,
                    SearchHistory.user_id == user_id
                )
            )
            .first()
        )
        
        if search:
            self.db.delete(search)
            self.db.commit()
            return True
        
        return False