from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.repositories.ip_repository import IPRepository
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.ip_address import (
    IPAddressCreate, IPAddressUpdate, IPAddressResponse,
    IPAllocationRequest, IPReservationRequest, IPReleaseRequest,
    IPSearchRequest, IPStatisticsResponse, IPSyncResponse,
    IPConflictResponse, IPRangeStatusRequest, IPRangeStatusResponse,
    BulkIPOperationRequest, BulkIPOperationResponse, IPDeleteRequest
)
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
import ipaddress
from datetime import datetime
from app.core.timezone_config import now_beijing


class IPService:
    def __init__(self, db: Session):
        self.db = db
        self.ip_repo = IPRepository(db)

    def generate_ips_for_subnet(self, subnet_id: int, network: str) -> List[IPAddress]:
        """为网段生成IP地址列表"""
        try:
            net = ipaddress.ip_network(network, strict=False)
        except ValueError:
            raise ValueError(f"无效的网段格式: {network}")

        # 获取网段信息
        subnet = self.db.query(Subnet).filter(Subnet.id == subnet_id).first()
        if not subnet:
            raise ValueError(f"网段不存在: {subnet_id}")

        # 检查网段大小，避免生成过多IP地址
        if net.num_addresses > 65536:  # /16网段
            raise ValidationError("网段过大，无法自动生成所有IP地址")

        # 批量创建IP地址数据
        ip_data_list = []
        for ip in net.hosts():
            # 检查IP是否已存在于其他网段
            existing_ip = self.ip_repo.get_by_ip_address(str(ip))
            if existing_ip and existing_ip.subnet_id != subnet_id:
                # 如果IP已存在于其他网段，跳过
                continue
            
            if not existing_ip:
                ip_data = IPAddressCreate(
                    ip_address=str(ip),
                    subnet_id=subnet_id,
                    status=IPStatus.AVAILABLE
                )
                ip_data_list.append(ip_data)

        # 批量插入IP地址
        if ip_data_list:
            return self.ip_repo.bulk_create(ip_data_list)
        
        return []

    def sync_subnet_ips(self, subnet_id: int, network: str) -> IPSyncResponse:
        """同步网段的IP地址列表"""
        try:
            stats = self.ip_repo.sync_subnet_ips(subnet_id, network)
            
            # 检查并处理冲突
            conflicts = self.detect_ip_conflicts(subnet_id)
            if conflicts:
                self.resolve_ip_conflicts(conflicts)
            
            return IPSyncResponse(
                subnet_id=subnet_id,
                network=network,
                added=stats['added'],
                removed=stats['removed'],
                kept=stats['kept'],
                message=f"同步完成：新增{stats['added']}个，删除{stats['removed']}个，保持{stats['kept']}个IP地址"
            )
        except Exception as e:
            raise ValidationError(f"同步IP地址失败: {str(e)}")

    def cleanup_unallocated_ips(self, subnet_id: int) -> int:
        """清理网段中未分配的IP地址"""
        return self.ip_repo.delete_by_subnet(subnet_id, IPStatus.AVAILABLE)

    def allocate_ip(self, request: IPAllocationRequest, allocated_by: int) -> IPAddressResponse:
        """分配IP地址"""
        print(f"[DEBUG] 开始分配IP，请求数据: {request}")
        print(f"[DEBUG] 分配时间: {request.allocated_at}")
        print(f"[DEBUG] 分配人ID: {allocated_by}")
        
        # 如果指定了首选IP，尝试分配
        if request.preferred_ip:
            preferred_ip = self.ip_repo.get_by_ip_address(request.preferred_ip)
            if preferred_ip:
                if preferred_ip.subnet_id != request.subnet_id:
                    raise ValidationError("指定的IP地址不属于目标网段")
                if preferred_ip.status != IPStatus.AVAILABLE:
                    raise ConflictError(f"IP地址 {request.preferred_ip} 不可用，当前状态: {preferred_ip.status}")
                
                # 分配指定IP
                allocated_time = request.allocated_at if request.allocated_at else now_beijing()
                
                update_data = IPAddressUpdate(
                    mac_address=request.mac_address,
                    user_name=request.user_name,
                    device_type=request.device_type,
                    location=request.location,
                    assigned_to=request.assigned_to,
                    description=request.description,
                    status=IPStatus.ALLOCATED,
                    allocated_at=allocated_time,
                    allocated_by=allocated_by
                )
                
                print(f"[DEBUG] 更新数据: {update_data}")
                updated_ip = self.ip_repo.update(preferred_ip.id, update_data)
                print(f"[DEBUG] 更新后的IP对象: {updated_ip}")
                print(f"[DEBUG] 更新后的分配时间: {updated_ip.allocated_at}")
                result = self._ip_to_response(updated_ip)
                print(f"[DEBUG] 响应数据: {result}")
                return result
        
        # 自动分配可用IP
        available_ips = self.ip_repo.get_available_ips(request.subnet_id, limit=1)
        if not available_ips:
            raise NotFoundError("网段中没有可用的IP地址")
        
        ip_to_allocate = available_ips[0]
        
        # 更新分配信息
        allocated_time = request.allocated_at if request.allocated_at else now_beijing()
        
        update_data = IPAddressUpdate(
            mac_address=request.mac_address,
            user_name=request.user_name,
            device_type=request.device_type,
            location=request.location,
            assigned_to=request.assigned_to,
            description=request.description,
            status=IPStatus.ALLOCATED,
            allocated_at=allocated_time,
            allocated_by=allocated_by
        )
        
        updated_ip = self.ip_repo.update(ip_to_allocate.id, update_data)
        return self._ip_to_response(updated_ip)

    def reserve_ip(self, request: IPReservationRequest, reserved_by: int) -> IPAddressResponse:
        """保留IP地址"""
        ip_record = self.ip_repo.get_by_ip_address(request.ip_address)
        if not ip_record:
            raise NotFoundError(f"IP地址 {request.ip_address} 不存在")
        
        if ip_record.status != IPStatus.AVAILABLE:
            raise ConflictError(f"IP地址 {request.ip_address} 不可用，当前状态: {ip_record.status}")
        
        # 检查保留IP地址的分配限制
        self._check_reservation_limits(ip_record.subnet_id, reserved_by)
        
        update_data = IPAddressUpdate(
            status=IPStatus.RESERVED,
            description=request.reason,
            assigned_to=f"保留 - {request.reason}" if request.reason else "保留"
        )
        
        # 更新保留信息
        ip_record.allocated_at = now_beijing()
        ip_record.allocated_by = reserved_by
        
        updated_ip = self.ip_repo.update(ip_record.id, update_data)
        return self._ip_to_response(updated_ip)

    def release_ip(self, request: IPReleaseRequest, released_by: int) -> IPAddressResponse:
        """释放IP地址"""
        ip_record = self.ip_repo.get_by_ip_address(request.ip_address)
        if not ip_record:
            raise NotFoundError(f"IP地址 {request.ip_address} 不存在")
        
        if ip_record.status not in [IPStatus.ALLOCATED, IPStatus.RESERVED]:
            raise ValidationError(f"IP地址 {request.ip_address} 无法释放，当前状态: {ip_record.status}")
        
        update_data = IPAddressUpdate(
            status=IPStatus.AVAILABLE,
            mac_address=None,
            user_name=None,
            device_type=None,
            assigned_to=None,
            description=request.reason
        )
        
        # 清除分配信息
        ip_record.allocated_at = None
        ip_record.allocated_by = None
        
        updated_ip = self.ip_repo.update(ip_record.id, update_data)
        return self._ip_to_response(updated_ip)

    def delete_ip(self, request: IPDeleteRequest, deleted_by: int) -> dict:
        """删除IP地址"""
        ip_record = self.ip_repo.get_by_ip_address(request.ip_address)
        if not ip_record:
            raise NotFoundError(f"IP地址 {request.ip_address} 不存在")
        
        # 检查IP地址是否可以删除
        if ip_record.status == IPStatus.ALLOCATED:
            raise ValidationError(f"IP地址 {request.ip_address} 已分配，无法删除。请先释放该IP地址")
        
        # 删除IP地址记录
        success = self.ip_repo.delete(ip_record.id)
        if not success:
            raise ValidationError(f"删除IP地址 {request.ip_address} 失败")
        
        return {
            "ip_address": request.ip_address,
            "message": f"IP地址 {request.ip_address} 删除成功",
            "reason": request.reason
        }

    def detect_ip_conflicts(self, subnet_id: Optional[int] = None) -> List[IPConflictResponse]:
        """检测IP地址冲突"""
        if subnet_id:
            conflicts = self.ip_repo.check_ip_conflicts(subnet_id)
        else:
            # 检查所有网段的冲突
            conflicts = []
            subnets = self.db.query(Subnet).all()
            for subnet in subnets:
                subnet_conflicts = self.ip_repo.check_ip_conflicts(subnet.id)
                conflicts.extend(subnet_conflicts)
        
        # 按IP地址分组冲突记录
        conflict_groups = {}
        for ip in conflicts:
            if ip.ip_address not in conflict_groups:
                conflict_groups[ip.ip_address] = []
            conflict_groups[ip.ip_address].append(ip)
        
        # 构建冲突响应
        conflict_responses = []
        for ip_address, conflicted_ips in conflict_groups.items():
            if len(conflicted_ips) > 1:
                conflict_response = IPConflictResponse(
                    ip_address=ip_address,
                    conflict_count=len(conflicted_ips),
                    conflicted_records=[self._ip_to_response(ip) for ip in conflicted_ips]
                )
                conflict_responses.append(conflict_response)
        
        return conflict_responses

    def resolve_ip_conflicts(self, conflicts: List[IPConflictResponse]) -> Dict[str, int]:
        """解决IP地址冲突"""
        resolved_count = 0
        marked_count = 0
        
        for conflict in conflicts:
            # 将冲突的IP地址标记为冲突状态
            ip_addresses = [record.ip_address for record in conflict.conflicted_records]
            marked = self.ip_repo.mark_conflicts(ip_addresses)
            marked_count += marked
            resolved_count += 1
        
        return {
            'resolved_conflicts': resolved_count,
            'marked_ips': marked_count
        }

    def get_ip_statistics(self, subnet_id: Optional[int] = None) -> IPStatisticsResponse:
        """获取IP地址统计信息"""
        stats = self.ip_repo.get_ip_statistics(subnet_id)
        
        total = stats['total']
        allocated = stats.get(IPStatus.ALLOCATED, 0)
        
        utilization_rate = (allocated / total * 100) if total > 0 else 0
        
        return IPStatisticsResponse(
            total=total,
            available=stats.get(IPStatus.AVAILABLE, 0),
            allocated=allocated,
            reserved=stats.get(IPStatus.RESERVED, 0),
            conflict=stats.get(IPStatus.CONFLICT, 0),
            utilization_rate=round(utilization_rate, 2)
        )

    def search_ips(self, request: IPSearchRequest) -> Tuple[List[IPAddressResponse], int]:
        """搜索IP地址"""
        # 使用高级搜索功能
        ips, total = self.ip_repo.advanced_search(request)
        
        ip_responses = [self._ip_to_response(ip) for ip in ips]
        return ip_responses, total
    
    def advanced_search_ips(self, request: IPSearchRequest, user_id: int) -> Dict[str, Any]:
        """高级搜索IP地址并保存搜索历史"""
        from app.services.query_builder import SearchHistoryService
        from app.schemas.ip_address import IPSearchResponse
        
        # 执行搜索
        ips, total = self.ip_repo.advanced_search(request)
        
        # 计算分页信息
        page = (request.skip // request.limit) + 1
        total_pages = (total + request.limit - 1) // request.limit
        
        # 保存搜索历史（如果有搜索条件）
        if any([request.query, request.subnet_id, request.status, request.device_type, 
                request.location, request.assigned_to, request.mac_address, request.user_name,
                request.ip_range_start, request.tags]):
            search_history_service = SearchHistoryService(self.db)
            search_params = request.model_dump(exclude_unset=True, exclude={'skip', 'limit'})
            search_history_service.save_search(user_id, search_params)
        
        # 构建响应
        ip_responses = [self._ip_to_response(ip) for ip in ips]
        
        return IPSearchResponse(
            items=ip_responses,
            total=total,
            page=page,
            page_size=request.limit,
            total_pages=total_pages
        )

    def get_ip_range_status(self, request: IPRangeStatusRequest) -> List[IPRangeStatusResponse]:
        """获取IP地址范围状态"""
        range_status = self.ip_repo.get_ip_range_status(request.start_ip, request.end_ip)
        
        return [
            IPRangeStatusResponse(
                ip_address=item['ip_address'],
                status=item['status'],
                user_name=item['hostname'],
                mac_address=item['mac_address'],
                assigned_to=item['assigned_to']
            )
            for item in range_status
        ]

    def bulk_ip_operation(self, request: BulkIPOperationRequest, user_id: int) -> BulkIPOperationResponse:
        """批量IP地址操作"""
        success_ips = []
        failed_ips = []
        
        for ip_address in request.ip_addresses:
            try:
                if request.operation == 'allocate':
                    # 批量分配需要更复杂的逻辑，这里简化处理
                    ip_record = self.ip_repo.get_by_ip_address(ip_address)
                    if ip_record and ip_record.status == IPStatus.AVAILABLE:
                        update_data = IPAddressUpdate(status=IPStatus.ALLOCATED)
                        ip_record.allocated_at = now_beijing()
                        ip_record.allocated_by = user_id
                        self.ip_repo.update(ip_record.id, update_data)
                        success_ips.append(ip_address)
                    else:
                        failed_ips.append({"ip": ip_address, "error": "IP不可用或不存在"})
                
                elif request.operation == 'reserve':
                    reserve_req = IPReservationRequest(ip_address=ip_address, reason=request.reason)
                    self.reserve_ip(reserve_req, user_id)
                    success_ips.append(ip_address)
                
                elif request.operation == 'release':
                    release_req = IPReleaseRequest(ip_address=ip_address, reason=request.reason)
                    self.release_ip(release_req, user_id)
                    success_ips.append(ip_address)
                
                elif request.operation == 'delete':
                    delete_req = IPDeleteRequest(ip_address=ip_address, reason=request.reason)
                    self.delete_ip(delete_req, user_id)
                    success_ips.append(ip_address)
                
            except Exception as e:
                failed_ips.append({"ip": ip_address, "error": str(e)})
        
        return BulkIPOperationResponse(
            success_count=len(success_ips),
            failed_count=len(failed_ips),
            success_ips=success_ips,
            failed_ips=failed_ips,
            message=f"批量操作完成：成功{len(success_ips)}个，失败{len(failed_ips)}个"
        )

    def _check_reservation_limits(self, subnet_id: int, user_id: int) -> None:
        """检查保留IP地址的分配限制"""
        # 获取用户当前保留的IP数量
        reserved_count = (
            self.db.query(IPAddress)
            .filter(
                and_(
                    IPAddress.subnet_id == subnet_id,
                    IPAddress.status == IPStatus.RESERVED,
                    IPAddress.allocated_by == user_id
                )
            )
            .count()
        )
        
        # 获取网段总IP数量
        total_ips = self.ip_repo.count_by_subnet(subnet_id)
        
        # 设置保留限制：单个用户最多保留网段20%的IP地址，且不超过100个
        max_reserved_percentage = 0.2  # 20%
        max_reserved_absolute = 100
        
        max_allowed = min(int(total_ips * max_reserved_percentage), max_reserved_absolute)
        
        if reserved_count >= max_allowed:
            raise ValidationError(
                f"保留IP地址数量已达到限制。当前已保留 {reserved_count} 个，"
                f"最大允许保留 {max_allowed} 个IP地址"
            )

    def get_departments(self) -> List[str]:
        """获取所有分配部门列表"""
        try:
            # 查询所有已分配IP的assigned_to字段
            departments = (
                self.db.query(IPAddress.assigned_to)
                .filter(
                    and_(
                        IPAddress.assigned_to.isnot(None),
                        IPAddress.assigned_to != '',
                        IPAddress.status == IPStatus.ALLOCATED
                    )
                )
                .distinct()
                .all()
            )
            
            # 提取部门名称并排序
            dept_list = [dept[0] for dept in departments if dept[0] and dept[0].strip()]
            dept_list.sort()
            
            return dept_list
            
        except Exception as e:
            # 如果查询失败，返回空列表
            return []

    def _ip_to_response(self, ip: IPAddress) -> IPAddressResponse:
        """将IP模型转换为响应模型"""
        return IPAddressResponse(
            id=ip.id,
            ip_address=ip.ip_address,
            subnet_id=ip.subnet_id,
            status=ip.status,
            mac_address=ip.mac_address,
            user_name=ip.user_name,
            device_type=ip.device_type,
            location=ip.location,
            assigned_to=ip.assigned_to,
            description=ip.description,
            allocated_at=ip.allocated_at,
            allocated_by=ip.allocated_by,
            created_at=ip.created_at,
            updated_at=ip.updated_at
        )