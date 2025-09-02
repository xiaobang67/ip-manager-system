from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.repositories.subnet_repository import SubnetRepository
from app.services.ip_service import IPService
from app.schemas.subnet import SubnetCreate, SubnetUpdate, SubnetResponse, SubnetValidationResponse
from app.models.subnet import Subnet
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
import ipaddress


class SubnetService:
    def __init__(self, db: Session):
        self.db = db
        self.subnet_repo = SubnetRepository(db)
        self.ip_service = IPService(db)

    def create_subnet(self, subnet_data: SubnetCreate, created_by: int) -> SubnetResponse:
        """创建网段"""
        # 检查网段重叠
        overlapping_subnets = self.subnet_repo.check_network_overlap(subnet_data.network)
        if overlapping_subnets:
            overlap_networks = [s.network for s in overlapping_subnets]
            raise ConflictError(f"网段与现有网段重叠: {', '.join(overlap_networks)}")

        # 创建网段
        subnet = self.subnet_repo.create(subnet_data, created_by)
        
        # 自动生成IP地址列表
        try:
            generated_ips = self.ip_service.generate_ips_for_subnet(subnet.id, subnet.network)
            if not generated_ips:
                # 记录警告但不失败
                print(f"警告：网段 {subnet.network} 没有生成任何IP地址")
        except Exception as e:
            # 如果IP生成失败，回滚网段创建
            self.subnet_repo.delete(subnet.id)
            raise ValidationError(f"生成IP地址失败: {str(e)}")

        return self._subnet_to_response(subnet)

    def get_subnet(self, subnet_id: int) -> SubnetResponse:
        """获取单个网段"""
        subnet = self.subnet_repo.get_by_id(subnet_id)
        if not subnet:
            raise NotFoundError("网段不存在")
        
        return self._subnet_to_response(subnet)

    def get_subnets(self, skip: int = 0, limit: int = 100) -> Tuple[List[SubnetResponse], int]:
        """获取网段列表"""
        subnet_stats = self.subnet_repo.get_with_stats(skip, limit)
        total = self.subnet_repo.count()
        
        subnets = []
        for stats in subnet_stats:
            subnet_response = self._subnet_to_response(stats['subnet'])
            subnet_response.ip_count = stats['ip_count']
            subnet_response.allocated_count = stats['allocated_count']
            subnet_response.available_count = stats['available_count']
            subnets.append(subnet_response)
        
        return subnets, total

    def update_subnet(self, subnet_id: int, subnet_data: SubnetUpdate) -> SubnetResponse:
        """更新网段"""
        # 检查网段是否存在
        existing_subnet = self.subnet_repo.get_by_id(subnet_id)
        if not existing_subnet:
            raise NotFoundError("网段不存在")

        # 如果更新了网段地址，检查重叠
        if subnet_data.network and subnet_data.network != existing_subnet.network:
            overlapping_subnets = self.subnet_repo.check_network_overlap(
                subnet_data.network, exclude_id=subnet_id
            )
            if overlapping_subnets:
                overlap_networks = [s.network for s in overlapping_subnets]
                raise ConflictError(f"网段与现有网段重叠: {', '.join(overlap_networks)}")

        # 更新网段
        updated_subnet = self.subnet_repo.update(subnet_id, subnet_data)
        
        # 如果网段地址发生变化，需要同步IP地址
        if subnet_data.network and subnet_data.network != existing_subnet.network:
            try:
                # 使用同步功能更新IP地址列表
                sync_result = self.ip_service.sync_subnet_ips(subnet_id, subnet_data.network)
                print(f"网段IP地址同步完成: {sync_result.message}")
            except Exception as e:
                raise ValidationError(f"同步IP地址失败: {str(e)}")

        return self._subnet_to_response(updated_subnet)

    def delete_subnet(self, subnet_id: int) -> bool:
        """删除网段"""
        # 检查网段是否存在
        subnet = self.subnet_repo.get_by_id(subnet_id)
        if not subnet:
            raise NotFoundError("网段不存在")

        # 检查是否有已分配的IP地址
        if self.subnet_repo.has_allocated_ips(subnet_id):
            allocated_count = self.subnet_repo.get_allocated_ip_count(subnet_id)
            raise ConflictError(f"无法删除网段，存在 {allocated_count} 个已分配的IP地址")

        # 删除网段（级联删除IP地址）
        return self.subnet_repo.delete(subnet_id)

    def validate_subnet(self, network: str, exclude_id: Optional[int] = None) -> SubnetValidationResponse:
        """验证网段"""
        try:
            # 验证CIDR格式
            ipaddress.ip_network(network, strict=False)
        except ValueError:
            return SubnetValidationResponse(
                is_valid=False,
                message="无效的网段格式，请使用CIDR格式如192.168.1.0/24"
            )

        # 检查重叠
        overlapping_subnets = self.subnet_repo.check_network_overlap(network, exclude_id)
        if overlapping_subnets:
            overlap_responses = [self._subnet_to_response(s) for s in overlapping_subnets]
            return SubnetValidationResponse(
                is_valid=False,
                message=f"网段与 {len(overlapping_subnets)} 个现有网段重叠",
                overlapping_subnets=overlap_responses
            )

        return SubnetValidationResponse(
            is_valid=True,
            message="网段验证通过"
        )

    def search_subnets(self, query: str, skip: int = 0, limit: int = 100) -> Tuple[List[SubnetResponse], int]:
        """搜索网段"""
        subnets = self.subnet_repo.search(query, skip, limit)
        # 注意：搜索结果的总数计算可能不准确，这里简化处理
        total = len(subnets)
        
        subnet_responses = [self._subnet_to_response(s) for s in subnets]
        return subnet_responses, total

    def get_subnets_by_vlan(self, vlan_id: int) -> List[SubnetResponse]:
        """根据VLAN ID获取网段"""
        subnets = self.subnet_repo.get_by_vlan(vlan_id)
        return [self._subnet_to_response(s) for s in subnets]

    def _subnet_to_response(self, subnet: Subnet) -> SubnetResponse:
        """将Subnet模型转换为响应模型"""
        return SubnetResponse(
            id=subnet.id,
            network=subnet.network,
            netmask=subnet.netmask,
            gateway=subnet.gateway,
            description=subnet.description,
            vlan_id=subnet.vlan_id,
            location=subnet.location,
            created_by=subnet.created_by,
            created_at=subnet.created_at,
            updated_at=subnet.updated_at
        )