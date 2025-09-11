"""
优化的IP地址服务
集成缓存、性能监控和查询优化功能
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, text
from datetime import datetime, timedelta
from app.core.timezone_config import now_beijing
import logging

from app.repositories.ip_repository import IPRepository
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.ip_address import (
    IPAddressCreate, IPAddressUpdate, IPAddressResponse,
    IPAllocationRequest, IPReservationRequest, IPReleaseRequest,
    IPSearchRequest, IPStatisticsResponse
)
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
from app.core.cache_manager import cache_manager, cached, invalidate_cache
from app.core.query_optimizer import query_optimizer, monitor_query_performance
from app.core.redis_client import DistributedLock

logger = logging.getLogger(__name__)


class OptimizedIPService:
    """优化的IP地址服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ip_repo = IPRepository(db)
    
    @cached("ip_list", ttl=180)
    @monitor_query_performance
    def get_ip_list(
        self, 
        page: int = 1, 
        size: int = 50, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取IP地址列表（带缓存）"""
        try:
            filters = filters or {}
            
            # 使用优化的查询
            query = query_optimizer.optimize_ip_list_query(
                self.db, filters, page, size
            )
            
            # 执行查询
            ip_addresses = query.all()
            
            # 获取总数（使用缓存）
            total_count = self._get_ip_count_cached(filters)
            
            # 转换为响应格式
            ip_list = [
                IPAddressResponse.from_orm(ip).dict() 
                for ip in ip_addresses
            ]
            
            return {
                "items": ip_list,
                "total": total_count,
                "page": page,
                "size": size,
                "pages": (total_count + size - 1) // size
            }
            
        except Exception as e:
            logger.error(f"Failed to get IP list: {e}")
            raise
    
    @cached("ip_detail", ttl=600)
    def get_ip_by_id(self, ip_id: int) -> Optional[IPAddressResponse]:
        """根据ID获取IP地址详情（带缓存）"""
        try:
            ip_address = self.ip_repo.get_by_id(ip_id)
            if not ip_address:
                return None
            
            return IPAddressResponse.from_orm(ip_address)
            
        except Exception as e:
            logger.error(f"Failed to get IP by ID {ip_id}: {e}")
            raise
    
    @cached("ip_detail", ttl=600)
    def get_ip_by_address(self, ip_address: str) -> Optional[IPAddressResponse]:
        """根据IP地址获取详情（带缓存）"""
        try:
            ip = self.ip_repo.get_by_ip_address(ip_address)
            if not ip:
                return None
            
            return IPAddressResponse.from_orm(ip)
            
        except Exception as e:
            logger.error(f"Failed to get IP by address {ip_address}: {e}")
            raise
    
    @invalidate_cache("ip_updated")
    @monitor_query_performance
    def allocate_ip(self, request: IPAllocationRequest, user_id: int) -> IPAddressResponse:
        """分配IP地址"""
        lock_key = f"ip_allocation:{request.ip_address or request.subnet_id}"
        
        with DistributedLock(lock_key, timeout=30):
            try:
                if request.ip_address:
                    # 分配指定IP地址
                    ip = self._allocate_specific_ip(request, user_id)
                else:
                    # 自动分配IP地址
                    ip = self._allocate_auto_ip(request, user_id)
                
                self.db.commit()
                
                # 清除相关缓存
                cache_manager.invalidate("ip_updated", ip_id=ip.id)
                
                return IPAddressResponse.from_orm(ip)
                
            except Exception as e:
                self.db.rollback()
                logger.error(f"Failed to allocate IP: {e}")
                raise
    
    @invalidate_cache("ip_updated")
    def reserve_ip(self, request: IPReservationRequest, user_id: int) -> IPAddressResponse:
        """保留IP地址"""
        try:
            ip = self.ip_repo.get_by_ip_address(request.ip_address)
            if not ip:
                raise NotFoundError(f"IP地址不存在: {request.ip_address}")
            
            if ip.status != IPStatus.AVAILABLE:
                raise ConflictError(f"IP地址状态不允许保留: {ip.status}")
            
            # 更新IP状态
            ip.status = IPStatus.RESERVED
            ip.description = request.reason
            ip.allocated_by = user_id
            ip.allocated_at = now_beijing()
            
            self.db.commit()
            
            return IPAddressResponse.from_orm(ip)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to reserve IP {request.ip_address}: {e}")
            raise
    
    @invalidate_cache("ip_updated")
    def release_ip(self, request: IPReleaseRequest, user_id: int) -> IPAddressResponse:
        """释放IP地址"""
        try:
            ip = self.ip_repo.get_by_ip_address(request.ip_address)
            if not ip:
                raise NotFoundError(f"IP地址不存在: {request.ip_address}")
            
            if ip.status not in [IPStatus.ALLOCATED, IPStatus.RESERVED]:
                raise ConflictError(f"IP地址状态不允许释放: {ip.status}")
            
            # 更新IP状态
            ip.status = IPStatus.AVAILABLE
            ip.mac_address = None
            ip.hostname = None
            ip.device_type = None
            ip.assigned_to = None
            ip.description = None
            ip.allocated_by = None
            ip.allocated_at = None
            
            self.db.commit()
            
            return IPAddressResponse.from_orm(ip)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to release IP {request.ip_address}: {e}")
            raise
    
    @cached("ip_search_results", ttl=300)
    @monitor_query_performance
    def search_ips(self, request: IPSearchRequest) -> Dict[str, Any]:
        """搜索IP地址（带缓存）"""
        try:
            # 构建搜索过滤器
            filters = {
                "search": request.query,
                "subnet_id": request.subnet_id,
                "status": request.status,
                "sort": request.sort_field,
                "order": request.sort_order
            }
            
            # 移除空值
            filters = {k: v for k, v in filters.items() if v is not None}
            
            return self.get_ip_list(
                page=request.page,
                size=request.size,
                filters=filters
            )
            
        except Exception as e:
            logger.error(f"Failed to search IPs: {e}")
            raise
    
    @cached("ip_statistics", ttl=60)
    @monitor_query_performance
    def get_ip_statistics(self, subnet_id: Optional[int] = None) -> IPStatisticsResponse:
        """获取IP地址统计信息（带缓存）"""
        try:
            # 基础查询
            query = self.db.query(
                IPAddress.status,
                func.count(IPAddress.id).label('count')
            )
            
            if subnet_id:
                query = query.filter(IPAddress.subnet_id == subnet_id)
            
            # 按状态分组统计
            stats = query.group_by(IPAddress.status).all()
            
            # 转换为字典
            status_counts = {stat.status: stat.count for stat in stats}
            
            # 计算总数和使用率
            total = sum(status_counts.values())
            allocated = status_counts.get(IPStatus.ALLOCATED, 0)
            reserved = status_counts.get(IPStatus.RESERVED, 0)
            available = status_counts.get(IPStatus.AVAILABLE, 0)
            
            utilization_rate = (allocated + reserved) / total if total > 0 else 0
            
            return IPStatisticsResponse(
                total=total,
                allocated=allocated,
                reserved=reserved,
                available=available,
                utilization_rate=utilization_rate,
                subnet_id=subnet_id
            )
            
        except Exception as e:
            logger.error(f"Failed to get IP statistics: {e}")
            raise
    
    @monitor_query_performance
    def get_recent_allocations(self, hours: int = 24, limit: int = 10) -> List[IPAddressResponse]:
        """获取最近分配的IP地址"""
        try:
            cutoff_time = now_beijing() - timedelta(hours=hours)
            
            recent_ips = self.db.query(IPAddress).filter(
                IPAddress.allocated_at >= cutoff_time,
                IPAddress.status == IPStatus.ALLOCATED
            ).order_by(
                IPAddress.allocated_at.desc()
            ).limit(limit).all()
            
            return [IPAddressResponse.from_orm(ip) for ip in recent_ips]
            
        except Exception as e:
            logger.error(f"Failed to get recent allocations: {e}")
            raise
    
    @monitor_query_performance
    def detect_ip_conflicts(self) -> List[Dict[str, Any]]:
        """检测IP地址冲突"""
        try:
            # 查找重复的IP地址
            conflicts = self.db.query(
                IPAddress.ip_address,
                func.count(IPAddress.id).label('count'),
                func.group_concat(IPAddress.id).label('ip_ids')
            ).group_by(
                IPAddress.ip_address
            ).having(
                func.count(IPAddress.id) > 1
            ).all()
            
            conflict_list = []
            for conflict in conflicts:
                ip_ids = [int(id_str) for id_str in conflict.ip_ids.split(',')]
                ips = self.db.query(IPAddress).filter(
                    IPAddress.id.in_(ip_ids)
                ).all()
                
                conflict_list.append({
                    "ip_address": conflict.ip_address,
                    "count": conflict.count,
                    "conflicting_ips": [
                        IPAddressResponse.from_orm(ip).dict() for ip in ips
                    ]
                })
            
            return conflict_list
            
        except Exception as e:
            logger.error(f"Failed to detect IP conflicts: {e}")
            raise
    
    def _allocate_specific_ip(self, request: IPAllocationRequest, user_id: int) -> IPAddress:
        """分配指定的IP地址"""
        ip = self.ip_repo.get_by_ip_address(request.ip_address)
        if not ip:
            raise NotFoundError(f"IP地址不存在: {request.ip_address}")
        
        if ip.status != IPStatus.AVAILABLE:
            raise ConflictError(f"IP地址不可用: {ip.status}")
        
        # 更新IP信息
        ip.status = IPStatus.ALLOCATED
        ip.mac_address = request.mac_address
        ip.hostname = request.hostname
        ip.device_type = request.device_type
        ip.assigned_to = request.assigned_to
        ip.description = request.description
        ip.allocated_by = user_id
        ip.allocated_at = now_beijing()
        
        return ip
    
    def _allocate_auto_ip(self, request: IPAllocationRequest, user_id: int) -> IPAddress:
        """自动分配IP地址"""
        # 查找指定网段中的可用IP
        available_ip = self.db.query(IPAddress).filter(
            IPAddress.subnet_id == request.subnet_id,
            IPAddress.status == IPStatus.AVAILABLE
        ).order_by(
            text("INET_ATON(ip_address)")  # 按IP地址数值排序
        ).first()
        
        if not available_ip:
            raise ConflictError(f"网段中没有可用的IP地址")
        
        # 更新IP信息
        available_ip.status = IPStatus.ALLOCATED
        available_ip.mac_address = request.mac_address
        available_ip.hostname = request.hostname
        available_ip.device_type = request.device_type
        available_ip.assigned_to = request.assigned_to
        available_ip.description = request.description
        available_ip.allocated_by = user_id
        available_ip.allocated_at = now_beijing()
        
        return available_ip
    
    @cached("ip_count", ttl=300)
    def _get_ip_count_cached(self, filters: Dict[str, Any]) -> int:
        """获取IP地址总数（带缓存）"""
        try:
            query = self.db.query(IPAddress)
            
            # 应用过滤器
            if filters.get("subnet_id"):
                query = query.filter(IPAddress.subnet_id == filters["subnet_id"])
            
            if filters.get("status"):
                if isinstance(filters["status"], list):
                    query = query.filter(IPAddress.status.in_(filters["status"]))
                else:
                    query = query.filter(IPAddress.status == filters["status"])
            
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    IPAddress.ip_address.like(search_term) |
                    IPAddress.hostname.like(search_term) |
                    IPAddress.mac_address.like(search_term) |
                    IPAddress.description.like(search_term)
                )
            
            return query.count()
            
        except Exception as e:
            logger.error(f"Failed to get IP count: {e}")
            return 0