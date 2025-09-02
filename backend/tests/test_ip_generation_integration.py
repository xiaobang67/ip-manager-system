import pytest
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ip_service import IPService
from app.services.subnet_service import SubnetService
from app.services.ip_lifecycle_service import IPLifecycleService
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.subnet import SubnetCreate, SubnetUpdate
from app.schemas.ip_address import IPAllocationRequest, IPReservationRequest, IPReleaseRequest
from app.core.exceptions import ValidationError, ConflictError
import ipaddress


class TestIPGenerationIntegration:
    """IP地址生成和同步集成测试"""

    @pytest.fixture
    def db_session(self):
        """获取数据库会话"""
        db = next(get_db())
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def ip_service(self, db_session):
        return IPService(db_session)

    @pytest.fixture
    def subnet_service(self, db_session):
        return SubnetService(db_session)

    @pytest.fixture
    def lifecycle_service(self, db_session):
        return IPLifecycleService(db_session)

    @pytest.fixture
    def test_subnet_data(self):
        return SubnetCreate(
            network="192.168.100.0/28",  # 小网段，14个主机IP
            netmask="255.255.255.240",
            gateway="192.168.100.1",
            description="集成测试网段",
            vlan_id=100,
            location="测试环境"
        )

    def test_create_subnet_auto_generates_ips(self, subnet_service, ip_service, test_subnet_data, db_session):
        """测试创建网段时自动生成IP地址"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 验证网段创建成功
        assert subnet_response.network == "192.168.100.0/28"
        assert subnet_response.id is not None
        
        # 验证IP地址自动生成
        ips = db_session.query(IPAddress).filter(IPAddress.subnet_id == subnet_response.id).all()
        
        # /28网段应该有14个主机IP（192.168.100.1 到 192.168.100.14）
        assert len(ips) == 14
        
        # 验证所有IP都是可用状态
        for ip in ips:
            assert ip.status == IPStatus.AVAILABLE
            assert ip.subnet_id == subnet_response.id
        
        # 验证IP地址范围正确
        ip_addresses = {ip.ip_address for ip in ips}
        expected_network = ipaddress.ip_network("192.168.100.0/28", strict=False)
        expected_ips = {str(ip) for ip in expected_network.hosts()}
        assert ip_addresses == expected_ips
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_update_subnet_syncs_ips(self, subnet_service, ip_service, test_subnet_data, db_session):
        """测试更新网段时同步IP地址"""
        # 创建初始网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        initial_ip_count = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id
        ).count()
        assert initial_ip_count == 14  # /28网段
        
        # 更新网段为更大的范围
        update_data = SubnetUpdate(
            network="192.168.100.0/27",  # 更大的网段，30个主机IP
            netmask="255.255.255.224"
        )
        
        updated_subnet = subnet_service.update_subnet(subnet_response.id, update_data)
        
        # 验证网段更新成功
        assert updated_subnet.network == "192.168.100.0/27"
        
        # 验证IP地址同步
        updated_ip_count = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id
        ).count()
        assert updated_ip_count == 30  # /27网段
        
        # 验证新增的IP地址都是可用状态
        all_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id
        ).all()
        available_count = sum(1 for ip in all_ips if ip.status == IPStatus.AVAILABLE)
        assert available_count == 30
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_ip_allocation_lifecycle(self, subnet_service, ip_service, lifecycle_service, test_subnet_data, db_session):
        """测试IP地址分配生命周期"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 分配IP地址
        allocation_request = IPAllocationRequest(
            subnet_id=subnet_response.id,
            hostname="test-server",
            device_type="服务器",
            assigned_to="测试用户",
            description="集成测试分配"
        )
        
        allocated_ip = ip_service.allocate_ip(allocation_request, allocated_by=1)
        
        # 验证分配成功
        assert allocated_ip.status == IPStatus.ALLOCATED
        assert allocated_ip.hostname == "test-server"
        assert allocated_ip.assigned_to == "测试用户"
        assert allocated_ip.allocated_by == 1
        assert allocated_ip.allocated_at is not None
        
        # 验证生命周期跟踪
        lifecycle_info = lifecycle_service.track_ip_lifecycle(allocated_ip.id)
        assert lifecycle_info['current_status'] == IPStatus.ALLOCATED
        assert lifecycle_info['lifecycle_stage'] == 'newly_allocated'
        assert lifecycle_info['usage_duration'] == 0  # 刚分配
        
        # 保留另一个IP
        available_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        reservation_request = IPReservationRequest(
            ip_address=available_ips.ip_address,
            reason="集成测试保留"
        )
        
        reserved_ip = ip_service.reserve_ip(reservation_request, reserved_by=1)
        assert reserved_ip.status == IPStatus.RESERVED
        
        # 释放分配的IP
        release_request = IPReleaseRequest(
            ip_address=allocated_ip.ip_address,
            reason="集成测试释放"
        )
        
        released_ip = ip_service.release_ip(release_request, released_by=1)
        assert released_ip.status == IPStatus.AVAILABLE
        assert released_ip.allocated_at is None
        assert released_ip.allocated_by is None
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_ip_conflict_detection_and_resolution(self, subnet_service, ip_service, test_subnet_data, db_session):
        """测试IP地址冲突检测和解决"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 人为创建冲突：手动插入重复的IP地址
        duplicate_ip = IPAddress(
            ip_address="192.168.100.5",
            subnet_id=subnet_response.id,
            status=IPStatus.ALLOCATED,
            hostname="duplicate-host"
        )
        db_session.add(duplicate_ip)
        db_session.commit()
        
        # 检测冲突
        conflicts = ip_service.detect_ip_conflicts(subnet_id=subnet_response.id)
        
        # 验证检测到冲突
        assert len(conflicts) == 1
        assert conflicts[0].ip_address == "192.168.100.5"
        assert conflicts[0].conflict_count == 2
        
        # 解决冲突
        resolution_result = ip_service.resolve_ip_conflicts(conflicts)
        assert resolution_result['resolved_conflicts'] == 1
        assert resolution_result['marked_ips'] == 2
        
        # 验证冲突IP被标记
        conflict_ips = db_session.query(IPAddress).filter(
            IPAddress.ip_address == "192.168.100.5",
            IPAddress.status == IPStatus.CONFLICT
        ).all()
        assert len(conflict_ips) == 2
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_subnet_ip_statistics(self, subnet_service, ip_service, test_subnet_data, db_session):
        """测试网段IP统计功能"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 分配几个IP
        for i in range(3):
            allocation_request = IPAllocationRequest(
                subnet_id=subnet_response.id,
                hostname=f"host-{i}",
                assigned_to=f"用户{i}"
            )
            ip_service.allocate_ip(allocation_request, allocated_by=1)
        
        # 保留一个IP
        available_ip = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id,
            IPAddress.status == IPStatus.AVAILABLE
        ).first()
        
        reservation_request = IPReservationRequest(
            ip_address=available_ip.ip_address,
            reason="统计测试保留"
        )
        ip_service.reserve_ip(reservation_request, reserved_by=1)
        
        # 获取统计信息
        stats = ip_service.get_ip_statistics(subnet_id=subnet_response.id)
        
        # 验证统计结果
        assert stats.total == 14  # /28网段总IP数
        assert stats.allocated == 3  # 分配了3个
        assert stats.reserved == 1   # 保留了1个
        assert stats.available == 10 # 剩余10个可用
        assert stats.conflict == 0   # 无冲突
        assert stats.utilization_rate == 21.43  # 3/14 * 100 ≈ 21.43%
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_subnet_lifecycle_summary(self, subnet_service, ip_service, lifecycle_service, test_subnet_data, db_session):
        """测试网段生命周期摘要"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 分配一些IP以创建活动
        for i in range(2):
            allocation_request = IPAllocationRequest(
                subnet_id=subnet_response.id,
                hostname=f"summary-host-{i}",
                assigned_to=f"摘要用户{i}"
            )
            ip_service.allocate_ip(allocation_request, allocated_by=1)
        
        # 获取生命周期摘要
        summary = lifecycle_service.get_subnet_lifecycle_summary(subnet_response.id)
        
        # 验证摘要信息
        assert summary['subnet_id'] == subnet_response.id
        assert summary['network'] == "192.168.100.0/28"
        assert summary['total_ips'] == 14
        assert summary['utilization_rate'] == 14.29  # 2/14 * 100 ≈ 14.29%
        assert summary['status_distribution']['total'] == 14
        assert summary['status_distribution'][IPStatus.ALLOCATED] == 2
        assert len(summary['recent_allocations']) == 2
        assert summary['long_term_allocated_count'] == 0  # 刚分配的不算长期
        assert 0 <= summary['health_score'] <= 100
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_ip_range_status_query(self, subnet_service, ip_service, test_subnet_data, db_session):
        """测试IP地址范围状态查询"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 分配一个IP
        allocation_request = IPAllocationRequest(
            subnet_id=subnet_response.id,
            preferred_ip="192.168.100.5",
            hostname="range-test-host",
            mac_address="00:11:22:33:44:55",
            assigned_to="范围测试用户"
        )
        ip_service.allocate_ip(allocation_request, allocated_by=1)
        
        # 查询IP范围状态
        from app.schemas.ip_address import IPRangeStatusRequest
        range_request = IPRangeStatusRequest(
            start_ip="192.168.100.3",
            end_ip="192.168.100.7"
        )
        
        range_status = ip_service.get_ip_range_status(range_request)
        
        # 验证范围查询结果
        assert len(range_status) == 5  # 5个IP地址
        
        # 查找已分配的IP
        allocated_ip_status = next(
            (item for item in range_status if item.ip_address == "192.168.100.5"),
            None
        )
        assert allocated_ip_status is not None
        assert allocated_ip_status.status == IPStatus.ALLOCATED
        assert allocated_ip_status.hostname == "range-test-host"
        assert allocated_ip_status.mac_address == "00:11:22:33:44:55"
        assert allocated_ip_status.assigned_to == "范围测试用户"
        
        # 验证其他IP为可用状态
        available_ips = [
            item for item in range_status 
            if item.ip_address != "192.168.100.5"
        ]
        for ip_status in available_ips:
            assert ip_status.status == IPStatus.AVAILABLE
            assert ip_status.hostname is None
        
        # 清理测试数据
        subnet_service.delete_subnet(subnet_response.id)

    def test_error_handling_invalid_network(self, subnet_service):
        """测试无效网段的错误处理"""
        invalid_subnet_data = SubnetCreate(
            network="invalid_network",
            netmask="255.255.255.0",
            description="无效网段测试"
        )
        
        with pytest.raises(ValidationError, match="生成IP地址失败"):
            subnet_service.create_subnet(invalid_subnet_data, created_by=1)

    def test_error_handling_large_network(self, subnet_service):
        """测试过大网段的错误处理"""
        large_subnet_data = SubnetCreate(
            network="10.0.0.0/16",  # 65534个主机IP，太大
            netmask="255.255.0.0",
            description="过大网段测试"
        )
        
        with pytest.raises(ValidationError, match="网段过大"):
            subnet_service.create_subnet(large_subnet_data, created_by=1)

    def test_delete_subnet_with_allocated_ips(self, subnet_service, ip_service, test_subnet_data, db_session):
        """测试删除包含已分配IP的网段"""
        # 创建网段
        subnet_response = subnet_service.create_subnet(test_subnet_data, created_by=1)
        
        # 分配一个IP
        allocation_request = IPAllocationRequest(
            subnet_id=subnet_response.id,
            hostname="delete-test-host"
        )
        ip_service.allocate_ip(allocation_request, allocated_by=1)
        
        # 尝试删除网段应该失败
        with pytest.raises(ConflictError, match="存在.*已分配的IP地址"):
            subnet_service.delete_subnet(subnet_response.id)
        
        # 释放所有已分配的IP
        allocated_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id,
            IPAddress.status == IPStatus.ALLOCATED
        ).all()
        
        for ip in allocated_ips:
            release_request = IPReleaseRequest(
                ip_address=ip.ip_address,
                reason="清理测试"
            )
            ip_service.release_ip(release_request, released_by=1)
        
        # 现在应该可以删除网段
        result = subnet_service.delete_subnet(subnet_response.id)
        assert result is True
        
        # 验证IP地址也被删除
        remaining_ips = db_session.query(IPAddress).filter(
            IPAddress.subnet_id == subnet_response.id
        ).count()
        assert remaining_ips == 0