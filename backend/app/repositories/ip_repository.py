from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.ip_address import IPAddressCreate, IPAddressUpdate
import ipaddress


class IPRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, ip_data: IPAddressCreate) -> IPAddress:
        """创建新IP地址记录"""
        db_ip = IPAddress(
            ip_address=ip_data.ip_address,
            subnet_id=ip_data.subnet_id,
            status=ip_data.status or IPStatus.AVAILABLE,
            mac_address=ip_data.mac_address,
            hostname=ip_data.hostname,
            device_type=ip_data.device_type,
            location=ip_data.location,
            assigned_to=ip_data.assigned_to,
            description=ip_data.description
        )
        self.db.add(db_ip)
        self.db.commit()
        self.db.refresh(db_ip)
        return db_ip

    def bulk_create(self, ip_data_list: List[IPAddressCreate]) -> List[IPAddress]:
        """批量创建IP地址记录"""
        db_ips = []
        for ip_data in ip_data_list:
            db_ip = IPAddress(
                ip_address=ip_data.ip_address,
                subnet_id=ip_data.subnet_id,
                status=ip_data.status or IPStatus.AVAILABLE,
                mac_address=ip_data.mac_address,
                hostname=ip_data.hostname,
                device_type=ip_data.device_type,
                location=ip_data.location,
                assigned_to=ip_data.assigned_to,
                description=ip_data.description
            )
            db_ips.append(db_ip)
        
        self.db.add_all(db_ips)
        self.db.commit()
        
        # 刷新所有对象以获取生成的ID
        for db_ip in db_ips:
            self.db.refresh(db_ip)
        
        return db_ips

    def get_by_id(self, ip_id: int) -> Optional[IPAddress]:
        """根据ID获取IP地址"""
        return (
            self.db.query(IPAddress)
            .options(joinedload(IPAddress.subnet))
            .filter(IPAddress.id == ip_id)
            .first()
        )

    def get_by_ip_address(self, ip_address: str) -> Optional[IPAddress]:
        """根据IP地址获取记录"""
        return (
            self.db.query(IPAddress)
            .options(joinedload(IPAddress.subnet))
            .filter(IPAddress.ip_address == ip_address)
            .first()
        )

    def get_by_subnet(self, subnet_id: int, skip: int = 0, limit: int = 100) -> List[IPAddress]:
        """获取网段下的所有IP地址"""
        return (
            self.db.query(IPAddress)
            .filter(IPAddress.subnet_id == subnet_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_available_ips(self, subnet_id: int, limit: int = 10) -> List[IPAddress]:
        """获取网段中可用的IP地址"""
        return (
            self.db.query(IPAddress)
            .filter(
                and_(
                    IPAddress.subnet_id == subnet_id,
                    IPAddress.status == IPStatus.AVAILABLE
                )
            )
            .limit(limit)
            .all()
        )

    def update(self, ip_id: int, ip_data: IPAddressUpdate) -> Optional[IPAddress]:
        """更新IP地址记录"""
        db_ip = self.get_by_id(ip_id)
        if not db_ip:
            return None

        update_data = ip_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_ip, field, value)

        self.db.commit()
        self.db.refresh(db_ip)
        return db_ip

    def delete(self, ip_id: int) -> bool:
        """删除IP地址记录"""
        db_ip = self.get_by_id(ip_id)
        if not db_ip:
            return False

        self.db.delete(db_ip)
        self.db.commit()
        return True

    def delete_by_subnet(self, subnet_id: int, status_filter: Optional[IPStatus] = None) -> int:
        """删除网段下的IP地址记录"""
        query = self.db.query(IPAddress).filter(IPAddress.subnet_id == subnet_id)
        
        if status_filter:
            query = query.filter(IPAddress.status == status_filter)
        
        deleted_count = query.count()
        query.delete()
        self.db.commit()
        return deleted_count

    def check_ip_conflicts(self, subnet_id: int) -> List[IPAddress]:
        """检查网段中的IP地址冲突"""
        # 查找重复的IP地址
        duplicate_ips = (
            self.db.query(IPAddress.ip_address)
            .filter(IPAddress.subnet_id == subnet_id)
            .group_by(IPAddress.ip_address)
            .having(func.count(IPAddress.id) > 1)
            .all()
        )
        
        if not duplicate_ips:
            return []
        
        duplicate_ip_list = [ip[0] for ip in duplicate_ips]
        
        return (
            self.db.query(IPAddress)
            .filter(
                and_(
                    IPAddress.subnet_id == subnet_id,
                    IPAddress.ip_address.in_(duplicate_ip_list)
                )
            )
            .all()
        )

    def mark_conflicts(self, ip_addresses: List[str]) -> int:
        """将指定的IP地址标记为冲突状态"""
        updated_count = (
            self.db.query(IPAddress)
            .filter(IPAddress.ip_address.in_(ip_addresses))
            .update(
                {IPAddress.status: IPStatus.CONFLICT},
                synchronize_session=False
            )
        )
        self.db.commit()
        return updated_count

    def get_ip_statistics(self, subnet_id: Optional[int] = None) -> Dict[str, int]:
        """获取IP地址统计信息"""
        query = self.db.query(
            IPAddress.status,
            func.count(IPAddress.id).label('count')
        )
        
        if subnet_id:
            query = query.filter(IPAddress.subnet_id == subnet_id)
        
        query = query.group_by(IPAddress.status)
        
        stats = {status.value: 0 for status in IPStatus}
        
        for status, count in query.all():
            stats[status] = count
        
        stats['total'] = sum(stats.values())
        return stats

    def search(self, query: Optional[str] = None, subnet_id: Optional[int] = None, 
               status: Optional[IPStatus] = None, skip: int = 0, limit: int = 100) -> List[IPAddress]:
        """搜索IP地址 - 保持向后兼容"""
        from app.schemas.ip_address import IPSearchRequest
        from app.services.query_builder import IPQueryBuilder
        
        # 构建搜索请求
        search_request = IPSearchRequest(
            query=query,
            subnet_id=subnet_id,
            status=status,
            skip=skip,
            limit=limit
        )
        
        # 使用查询构建器
        query_builder = IPQueryBuilder(self.db)
        search_query, _ = query_builder.build_search_query(search_request)
        
        return search_query.all()
    
    def advanced_search(self, search_request) -> Tuple[List[IPAddress], int]:
        """高级搜索IP地址"""
        from app.services.query_builder import IPQueryBuilder
        
        query_builder = IPQueryBuilder(self.db)
        search_query, count_query = query_builder.build_search_query(search_request)
        
        # 执行查询
        results = search_query.all()
        total = count_query.scalar()
        
        return results, total

    def count_by_subnet(self, subnet_id: int) -> int:
        """统计网段中的IP地址数量"""
        return self.db.query(IPAddress).filter(IPAddress.subnet_id == subnet_id).count()

    def get_ip_range_status(self, start_ip: str, end_ip: str) -> List[Dict[str, Any]]:
        """获取IP地址范围的状态信息"""
        try:
            start_addr = ipaddress.ip_address(start_ip)
            end_addr = ipaddress.ip_address(end_ip)
        except ValueError:
            return []
        
        # 生成IP地址范围
        ip_range = []
        current = start_addr
        while current <= end_addr:
            ip_range.append(str(current))
            current += 1
        
        # 查询数据库中的IP状态
        db_ips = (
            self.db.query(IPAddress)
            .filter(IPAddress.ip_address.in_(ip_range))
            .all()
        )
        
        # 创建IP状态映射
        ip_status_map = {ip.ip_address: ip for ip in db_ips}
        
        # 构建结果
        result = []
        for ip_str in ip_range:
            if ip_str in ip_status_map:
                ip_obj = ip_status_map[ip_str]
                result.append({
                    'ip_address': ip_str,
                    'status': ip_obj.status,
                    'hostname': ip_obj.hostname,
                    'mac_address': ip_obj.mac_address,
                    'assigned_to': ip_obj.assigned_to
                })
            else:
                result.append({
                    'ip_address': ip_str,
                    'status': 'not_managed',
                    'hostname': None,
                    'mac_address': None,
                    'assigned_to': None
                })
        
        return result

    def sync_subnet_ips(self, subnet_id: int, network: str) -> Dict[str, int]:
        """同步网段的IP地址列表"""
        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError:
            raise ValueError(f"无效的网段格式: {network}")
        
        # 获取当前网段中的所有IP地址
        existing_ips = self.get_by_subnet(subnet_id, skip=0, limit=10000)
        existing_ip_set = {ip.ip_address for ip in existing_ips}
        
        # 生成网段中应该存在的所有IP地址
        expected_ips = {str(ip) for ip in net.hosts()}
        
        # 找出需要添加和删除的IP地址
        ips_to_add = expected_ips - existing_ip_set
        ips_to_remove = existing_ip_set - expected_ips
        
        stats = {
            'added': 0,
            'removed': 0,
            'kept': len(existing_ip_set & expected_ips)
        }
        
        # 删除不再属于网段的IP地址（只删除未分配的）
        if ips_to_remove:
            removed_count = (
                self.db.query(IPAddress)
                .filter(
                    and_(
                        IPAddress.subnet_id == subnet_id,
                        IPAddress.ip_address.in_(list(ips_to_remove)),
                        IPAddress.status == IPStatus.AVAILABLE
                    )
                )
                .delete(synchronize_session=False)
            )
            stats['removed'] = removed_count
        
        # 添加新的IP地址
        if ips_to_add:
            new_ips = []
            for ip_str in ips_to_add:
                new_ip = IPAddress(
                    ip_address=ip_str,
                    subnet_id=subnet_id,
                    status=IPStatus.AVAILABLE
                )
                new_ips.append(new_ip)
            
            self.db.add_all(new_ips)
            stats['added'] = len(new_ips)
        
        self.db.commit()
        return stats