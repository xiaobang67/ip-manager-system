from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress, IPStatus
from app.schemas.subnet import SubnetCreate, SubnetUpdate
import ipaddress


class SubnetRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, subnet_data: SubnetCreate, created_by: int) -> Subnet:
        """创建新网段"""
        db_subnet = Subnet(
            network=subnet_data.network,
            netmask=subnet_data.netmask,
            gateway=subnet_data.gateway,
            description=subnet_data.description,
            vlan_id=subnet_data.vlan_id,
            location=subnet_data.location,
            created_by=created_by
        )
        self.db.add(db_subnet)
        self.db.commit()
        self.db.refresh(db_subnet)
        return db_subnet

    def get_by_id(self, subnet_id: int) -> Optional[Subnet]:
        """根据ID获取网段"""
        return self.db.query(Subnet).filter(Subnet.id == subnet_id).first()

    def get_by_network(self, network: str) -> Optional[Subnet]:
        """根据网段地址获取网段"""
        return self.db.query(Subnet).filter(Subnet.network == network).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Subnet]:
        """获取所有网段（分页）"""
        return self.db.query(Subnet).offset(skip).limit(limit).all()

    def get_with_stats(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """获取带统计信息的网段列表"""
        # 子查询：计算每个网段的IP统计
        from sqlalchemy import case
        ip_stats = (
            self.db.query(
                IPAddress.subnet_id,
                func.count(IPAddress.id).label('total_ips'),
                func.sum(case((IPAddress.status == IPStatus.ALLOCATED, 1), else_=0)).label('allocated_ips'),
                func.sum(case((IPAddress.status == IPStatus.AVAILABLE, 1), else_=0)).label('available_ips')
            )
            .group_by(IPAddress.subnet_id)
            .subquery()
        )

        # 主查询：获取网段信息并关联统计数据
        query = (
            self.db.query(
                Subnet,
                func.coalesce(ip_stats.c.total_ips, 0).label('ip_count'),
                func.coalesce(ip_stats.c.allocated_ips, 0).label('allocated_count'),
                func.coalesce(ip_stats.c.available_ips, 0).label('available_count')
            )
            .outerjoin(ip_stats, Subnet.id == ip_stats.c.subnet_id)
            .offset(skip)
            .limit(limit)
        )

        results = []
        for subnet, ip_count, allocated_count, available_count in query.all():
            subnet_dict = {
                'subnet': subnet,
                'ip_count': ip_count,
                'allocated_count': allocated_count,
                'available_count': available_count
            }
            results.append(subnet_dict)
        
        return results

    def count(self) -> int:
        """获取网段总数"""
        return self.db.query(Subnet).count()

    def update(self, subnet_id: int, subnet_data: SubnetUpdate) -> Optional[Subnet]:
        """更新网段"""
        db_subnet = self.get_by_id(subnet_id)
        if not db_subnet:
            return None

        update_data = subnet_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_subnet, field, value)

        self.db.commit()
        self.db.refresh(db_subnet)
        return db_subnet

    def delete(self, subnet_id: int) -> bool:
        """删除网段"""
        db_subnet = self.get_by_id(subnet_id)
        if not db_subnet:
            return False

        self.db.delete(db_subnet)
        self.db.commit()
        return True

    def check_network_overlap(self, network: str, exclude_id: Optional[int] = None) -> List[Subnet]:
        """检查网段重叠"""
        try:
            new_network = ipaddress.ip_network(network, strict=False)
        except ValueError:
            return []

        query = self.db.query(Subnet)
        if exclude_id:
            query = query.filter(Subnet.id != exclude_id)

        existing_subnets = query.all()
        overlapping_subnets = []

        for subnet in existing_subnets:
            try:
                existing_network = ipaddress.ip_network(subnet.network, strict=False)
                # 检查是否重叠
                if new_network.overlaps(existing_network):
                    overlapping_subnets.append(subnet)
            except ValueError:
                continue

        return overlapping_subnets

    def get_allocated_ip_count(self, subnet_id: int) -> int:
        """获取网段中已分配的IP数量"""
        return (
            self.db.query(IPAddress)
            .filter(
                and_(
                    IPAddress.subnet_id == subnet_id,
                    IPAddress.status == IPStatus.ALLOCATED
                )
            )
            .count()
        )

    def has_allocated_ips(self, subnet_id: int) -> bool:
        """检查网段是否有已分配的IP地址"""
        return self.get_allocated_ip_count(subnet_id) > 0

    def search(self, query: str, skip: int = 0, limit: int = 100) -> List[Subnet]:
        """搜索网段"""
        search_filter = or_(
            Subnet.network.contains(query),
            Subnet.description.contains(query),
            Subnet.location.contains(query),
            Subnet.gateway.contains(query)
        )
        
        return (
            self.db.query(Subnet)
            .filter(search_filter)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_vlan(self, vlan_id: int) -> List[Subnet]:
        """根据VLAN ID获取网段"""
        return self.db.query(Subnet).filter(Subnet.vlan_id == vlan_id).all()