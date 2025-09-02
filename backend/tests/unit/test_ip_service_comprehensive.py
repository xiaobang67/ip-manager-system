"""
IP服务单元测试 - 全面覆盖
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import ipaddress

from app.services.ip_service import IPService
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.user import User
from app.core.exceptions import (
    IPNotFoundError, IPAlreadyAllocatedError, 
    IPConflictError, InvalidIPError
)
from tests.factories import (
    IPAddressFactory, SubnetFactory, UserFactory,
    AllocatedIPFactory, ReservedIPFactory
)


class TestIPService:
    """IP服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock()

    @pytest.fixture
    def ip_service(self, mock_db):
        """IP服务实例"""
        return IPService(mock_db)

    @pytest.fixture
    def test_subnet(self):
        """测试网段"""
        return SubnetFactory.build(network="192.168.1.0/24")

    @pytest.fixture
    def test_user(self):
        """测试用户"""
        return UserFactory.build()

    @pytest.mark.unit
    def test_allocate_ip_success(self, ip_service, mock_db, test_subnet, test_user):
        """测试成功分配IP地址"""
        # 准备测试数据
        available_ip = IPAddressFactory.build(
            ip_address="192.168.1.10",
            subnet=test_subnet,
            status=IPStatus.AVAILABLE
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = available_ip
        mock_db.commit = Mock()
        
        # 执行测试
        result = ip_service.allocate_ip("192.168.1.10", test_user.id, "Test Device")
        
        # 验证结果
        assert result.status == IPStatus.ALLOCATED
        assert result.allocated_by == test_user.id
        assert result.hostname == "Test Device"
        assert result.allocated_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    def test_allocate_ip_not_found(self, ip_service, mock_db, test_user):
        """测试分配不存在的IP地址"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(IPNotFoundError):
            ip_service.allocate_ip("192.168.1.999", test_user.id, "Test Device")

    @pytest.mark.unit
    def test_allocate_already_allocated_ip(self, ip_service, mock_db, test_subnet, test_user):
        """测试分配已分配的IP地址"""
        allocated_ip = AllocatedIPFactory.build(
            ip_address="192.168.1.10",
            subnet=test_subnet
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = allocated_ip
        
        with pytest.raises(IPAlreadyAllocatedError):
            ip_service.allocate_ip("192.168.1.10", test_user.id, "Test Device")

    @pytest.mark.unit
    def test_reserve_ip_success(self, ip_service, mock_db, test_subnet, test_user):
        """测试成功保留IP地址"""
        available_ip = IPAddressFactory.build(
            ip_address="192.168.1.20",
            subnet=test_subnet,
            status=IPStatus.AVAILABLE
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = available_ip
        mock_db.commit = Mock()
        
        result = ip_service.reserve_ip("192.168.1.20", test_user.id, "Reserved for server")
        
        assert result.status == IPStatus.RESERVED
        assert result.description == "Reserved for server"
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    def test_release_ip_success(self, ip_service, mock_db, test_subnet, test_user):
        """测试成功释放IP地址"""
        allocated_ip = AllocatedIPFactory.build(
            ip_address="192.168.1.30",
            subnet=test_subnet,
            allocated_by=test_user.id
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = allocated_ip
        mock_db.commit = Mock()
        
        result = ip_service.release_ip("192.168.1.30", test_user.id)
        
        assert result.status == IPStatus.AVAILABLE
        assert result.allocated_by is None
        assert result.allocated_at is None
        assert result.hostname is None
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    def test_detect_ip_conflict(self, ip_service, mock_db):
        """测试IP冲突检测"""
        # 模拟冲突的IP地址
        conflicting_ips = [
            IPAddressFactory.build(ip_address="192.168.1.100", mac_address="AA:BB:CC:DD:EE:01"),
            IPAddressFactory.build(ip_address="192.168.1.101", mac_address="AA:BB:CC:DD:EE:01")
        ]
        
        mock_db.query.return_value.group_by.return_value.having.return_value.all.return_value = [
            ("AA:BB:CC:DD:EE:01", 2)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = conflicting_ips
        
        conflicts = ip_service.detect_conflicts()
        
        assert len(conflicts) == 1
        assert conflicts[0]["mac_address"] == "AA:BB:CC:DD:EE:01"
        assert len(conflicts[0]["ips"]) == 2

    @pytest.mark.unit
    def test_validate_ip_address_valid(self, ip_service):
        """测试有效IP地址验证"""
        assert ip_service.validate_ip_address("192.168.1.1") is True
        assert ip_service.validate_ip_address("10.0.0.1") is True
        assert ip_service.validate_ip_address("172.16.0.1") is True

    @pytest.mark.unit
    def test_validate_ip_address_invalid(self, ip_service):
        """测试无效IP地址验证"""
        assert ip_service.validate_ip_address("256.1.1.1") is False
        assert ip_service.validate_ip_address("192.168.1") is False
        assert ip_service.validate_ip_address("invalid") is False
        assert ip_service.validate_ip_address("") is False

    @pytest.mark.unit
    def test_get_ip_utilization_stats(self, ip_service, mock_db, test_subnet):
        """测试IP使用率统计"""
        # 模拟统计查询结果
        mock_db.query.return_value.filter.return_value.count.side_effect = [100, 30, 10, 5]
        
        stats = ip_service.get_utilization_stats(test_subnet.id)
        
        assert stats["total"] == 100
        assert stats["allocated"] == 30
        assert stats["reserved"] == 10
        assert stats["available"] == 60
        assert stats["utilization_rate"] == 40.0

    @pytest.mark.unit
    def test_bulk_allocate_ips(self, ip_service, mock_db, test_subnet, test_user):
        """测试批量分配IP地址"""
        ip_addresses = ["192.168.1.10", "192.168.1.11", "192.168.1.12"]
        available_ips = [
            IPAddressFactory.build(ip_address=ip, subnet=test_subnet, status=IPStatus.AVAILABLE)
            for ip in ip_addresses
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = available_ips
        mock_db.commit = Mock()
        
        results = ip_service.bulk_allocate(ip_addresses, test_user.id, "Bulk allocation")
        
        assert len(results) == 3
        for result in results:
            assert result.status == IPStatus.ALLOCATED
            assert result.allocated_by == test_user.id
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    @patch('app.services.ip_service.datetime')
    def test_ip_allocation_with_expiry(self, mock_datetime, ip_service, mock_db, test_subnet, test_user):
        """测试带过期时间的IP分配"""
        mock_now = datetime(2023, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        
        available_ip = IPAddressFactory.build(
            ip_address="192.168.1.40",
            subnet=test_subnet,
            status=IPStatus.AVAILABLE
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = available_ip
        mock_db.commit = Mock()
        
        expiry_hours = 24
        result = ip_service.allocate_ip_with_expiry(
            "192.168.1.40", test_user.id, "Temporary allocation", expiry_hours
        )
        
        assert result.status == IPStatus.ALLOCATED
        assert result.allocated_at == mock_now
        # 验证过期时间设置（如果模型支持）

    @pytest.mark.unit
    def test_search_ips_by_criteria(self, ip_service, mock_db):
        """测试按条件搜索IP地址"""
        search_criteria = {
            "ip_address": "192.168.1",
            "status": IPStatus.ALLOCATED,
            "hostname": "server"
        }
        
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        results = ip_service.search_ips(search_criteria)
        
        # 验证查询构建
        assert mock_query.filter.called
        assert mock_query.all.called

    @pytest.mark.unit
    def test_get_ip_history(self, ip_service, mock_db):
        """测试获取IP地址历史记录"""
        ip_address = "192.168.1.50"
        
        # 模拟审计日志查询
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        history = ip_service.get_ip_history(ip_address)
        
        assert isinstance(history, list)
        mock_db.query.assert_called()

    @pytest.mark.unit
    def test_calculate_subnet_utilization(self, ip_service, mock_db):
        """测试计算网段使用率"""
        subnet_id = 1
        
        # 模拟不同状态的IP数量
        mock_db.query.return_value.filter.return_value.count.side_effect = [254, 100, 20]
        
        utilization = ip_service.calculate_subnet_utilization(subnet_id)
        
        assert utilization["total_ips"] == 254
        assert utilization["allocated_ips"] == 100
        assert utilization["reserved_ips"] == 20
        assert utilization["available_ips"] == 134
        assert utilization["utilization_percentage"] == pytest.approx(47.24, rel=1e-2)

    @pytest.mark.unit
    def test_auto_assign_next_available_ip(self, ip_service, mock_db, test_subnet, test_user):
        """测试自动分配下一个可用IP"""
        available_ip = IPAddressFactory.build(
            ip_address="192.168.1.60",
            subnet=test_subnet,
            status=IPStatus.AVAILABLE
        )
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = available_ip
        mock_db.commit = Mock()
        
        result = ip_service.auto_assign_ip(test_subnet.id, test_user.id, "Auto assigned")
        
        assert result.status == IPStatus.ALLOCATED
        assert result.ip_address == "192.168.1.60"
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    def test_validate_ip_in_subnet(self, ip_service):
        """测试验证IP是否在网段内"""
        subnet_network = "192.168.1.0/24"
        
        assert ip_service.validate_ip_in_subnet("192.168.1.10", subnet_network) is True
        assert ip_service.validate_ip_in_subnet("192.168.2.10", subnet_network) is False
        assert ip_service.validate_ip_in_subnet("10.0.0.1", subnet_network) is False

    @pytest.mark.unit
    def test_error_handling_database_failure(self, ip_service, mock_db, test_user):
        """测试数据库故障错误处理"""
        mock_db.query.side_effect = Exception("Database connection failed")
        
        with pytest.raises(Exception) as exc_info:
            ip_service.allocate_ip("192.168.1.70", test_user.id, "Test")
        
        assert "Database connection failed" in str(exc_info.value)

    @pytest.mark.unit
    def test_concurrent_allocation_prevention(self, ip_service, mock_db, test_subnet, test_user):
        """测试防止并发分配同一IP"""
        available_ip = IPAddressFactory.build(
            ip_address="192.168.1.80",
            subnet=test_subnet,
            status=IPStatus.AVAILABLE
        )
        
        # 模拟在分配过程中IP状态被其他进程改变
        def side_effect(*args, **kwargs):
            available_ip.status = IPStatus.ALLOCATED
            return available_ip
        
        mock_db.query.return_value.filter.return_value.first.side_effect = side_effect
        
        with pytest.raises(IPAlreadyAllocatedError):
            ip_service.allocate_ip("192.168.1.80", test_user.id, "Test")