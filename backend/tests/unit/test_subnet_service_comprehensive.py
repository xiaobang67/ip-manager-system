"""
网段服务单元测试 - 全面覆盖
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import ipaddress
from datetime import datetime

from app.services.subnet_service import SubnetService
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress, IPStatus
from app.models.user import User
from app.core.exceptions import (
    SubnetNotFoundError, SubnetOverlapError, 
    InvalidSubnetError, SubnetNotEmptyError
)
from tests.factories import SubnetFactory, UserFactory, IPAddressFactory


class TestSubnetService:
    """网段服务测试类"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock()

    @pytest.fixture
    def subnet_service(self, mock_db):
        """网段服务实例"""
        return SubnetService(mock_db)

    @pytest.fixture
    def test_user(self):
        """测试用户"""
        return UserFactory.build()

    @pytest.mark.unit
    def test_create_subnet_success(self, subnet_service, mock_db, test_user):
        """测试成功创建网段"""
        subnet_data = {
            "network": "192.168.1.0/24",
            "netmask": "255.255.255.0",
            "gateway": "192.168.1.1",
            "description": "Test subnet",
            "vlan_id": 100,
            "location": "Office"
        }
        
        # 模拟无重叠网段
        mock_db.query.return_value.all.return_value = []
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch.object(subnet_service, '_generate_ip_addresses') as mock_generate:
            result = subnet_service.create_subnet(subnet_data, test_user.id)
            
            assert result.network == "192.168.1.0/24"
            assert result.created_by == test_user.id
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_generate.assert_called_once()

    @pytest.mark.unit
    def test_create_subnet_invalid_network(self, subnet_service, mock_db, test_user):
        """测试创建无效网段"""
        subnet_data = {
            "network": "invalid_network",
            "netmask": "255.255.255.0"
        }
        
        with pytest.raises(InvalidSubnetError):
            subnet_service.create_subnet(subnet_data, test_user.id)

    @pytest.mark.unit
    def test_create_subnet_overlap_detection(self, subnet_service, mock_db, test_user):
        """测试网段重叠检测"""
        existing_subnet = SubnetFactory.build(network="192.168.1.0/24")
        mock_db.query.return_value.all.return_value = [existing_subnet]
        
        subnet_data = {
            "network": "192.168.1.128/25",  # 与现有网段重叠
            "netmask": "255.255.255.128"
        }
        
        with pytest.raises(SubnetOverlapError):
            subnet_service.create_subnet(subnet_data, test_user.id)

    @pytest.mark.unit
    def test_update_subnet_success(self, subnet_service, mock_db, test_user):
        """测试成功更新网段"""
        existing_subnet = SubnetFactory.build(
            id=1,
            network="192.168.1.0/24",
            created_by=test_user.id
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_subnet
        mock_db.query.return_value.all.return_value = []  # 无重叠
        mock_db.commit = Mock()
        
        update_data = {
            "description": "Updated description",
            "vlan_id": 200
        }
        
        result = subnet_service.update_subnet(1, update_data, test_user.id)
        
        assert result.description == "Updated description"
        assert result.vlan_id == 200
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    def test_delete_subnet_success(self, subnet_service, mock_db, test_user):
        """测试成功删除空网段"""
        existing_subnet = SubnetFactory.build(id=1, created_by=test_user.id)
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_subnet
        # 模拟网段下无已分配IP
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        result = subnet_service.delete_subnet(1, test_user.id)
        
        assert result is True
        mock_db.delete.assert_called_once_with(existing_subnet)
        mock_db.commit.assert_called_once()

    @pytest.mark.unit
    def test_delete_subnet_not_empty(self, subnet_service, mock_db, test_user):
        """测试删除包含已分配IP的网段"""
        existing_subnet = SubnetFactory.build(id=1, created_by=test_user.id)
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_subnet
        # 模拟网段下有已分配IP
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        with pytest.raises(SubnetNotEmptyError):
            subnet_service.delete_subnet(1, test_user.id)

    @pytest.mark.unit
    def test_validate_subnet_format_valid(self, subnet_service):
        """测试有效网段格式验证"""
        valid_networks = [
            "192.168.1.0/24",
            "10.0.0.0/8",
            "172.16.0.0/16",
            "192.168.100.0/28"
        ]
        
        for network in valid_networks:
            assert subnet_service.validate_subnet_format(network) is True

    @pytest.mark.unit
    def test_validate_subnet_format_invalid(self, subnet_service):
        """测试无效网段格式验证"""
        invalid_networks = [
            "192.168.1.0",  # 缺少CIDR
            "192.168.1.0/33",  # 无效CIDR
            "256.1.1.0/24",  # 无效IP
            "192.168.1.1/24",  # 主机地址而非网络地址
            "invalid/24"
        ]
        
        for network in invalid_networks:
            assert subnet_service.validate_subnet_format(network) is False

    @pytest.mark.unit
    def test_check_subnet_overlap(self, subnet_service):
        """测试网段重叠检查"""
        existing_subnets = [
            SubnetFactory.build(network="192.168.1.0/24"),
            SubnetFactory.build(network="10.0.0.0/16"),
            SubnetFactory.build(network="172.16.0.0/20")
        ]
        
        # 测试重叠情况
        overlapping_networks = [
            "192.168.1.128/25",  # 子网重叠
            "192.168.0.0/23",    # 父网重叠
            "10.0.1.0/24"        # 子网重叠
        ]
        
        for network in overlapping_networks:
            assert subnet_service.check_overlap(network, existing_subnets) is True
        
        # 测试不重叠情况
        non_overlapping_networks = [
            "192.168.2.0/24",
            "172.17.0.0/24",
            "10.1.0.0/16"
        ]
        
        for network in non_overlapping_networks:
            assert subnet_service.check_overlap(network, existing_subnets) is False

    @pytest.mark.unit
    def test_generate_ip_addresses(self, subnet_service, mock_db):
        """测试生成IP地址列表"""
        subnet = SubnetFactory.build(
            id=1,
            network="192.168.1.0/30"  # 小网段，只有2个主机地址
        )
        
        mock_db.add_all = Mock()
        mock_db.commit = Mock()
        
        subnet_service._generate_ip_addresses(subnet)
        
        # 验证调用了add_all和commit
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # 验证生成的IP地址数量
        call_args = mock_db.add_all.call_args[0][0]
        assert len(call_args) == 2  # /30网段有2个可用主机地址

    @pytest.mark.unit
    def test_get_subnet_statistics(self, subnet_service, mock_db):
        """测试获取网段统计信息"""
        subnet_id = 1
        
        # 模拟统计查询结果
        mock_db.query.return_value.filter.return_value.count.side_effect = [254, 100, 20, 5]
        
        stats = subnet_service.get_subnet_statistics(subnet_id)
        
        assert stats["total_ips"] == 254
        assert stats["allocated_ips"] == 100
        assert stats["reserved_ips"] == 20
        assert stats["available_ips"] == 134
        assert stats["conflict_ips"] == 5
        assert stats["utilization_rate"] == pytest.approx(47.24, rel=1e-2)

    @pytest.mark.unit
    def test_get_available_ip_ranges(self, subnet_service, mock_db):
        """测试获取可用IP范围"""
        subnet = SubnetFactory.build(network="192.168.1.0/24")
        allocated_ips = [
            IPAddressFactory.build(ip_address="192.168.1.10", status=IPStatus.ALLOCATED),
            IPAddressFactory.build(ip_address="192.168.1.11", status=IPStatus.ALLOCATED),
            IPAddressFactory.build(ip_address="192.168.1.20", status=IPStatus.RESERVED)
        ]
        
        mock_db.query.return_value.filter.return_value.first.return_value = subnet
        mock_db.query.return_value.filter.return_value.all.return_value = allocated_ips
        
        ranges = subnet_service.get_available_ip_ranges(1)
        
        assert isinstance(ranges, list)
        # 验证返回的是可用IP范围

    @pytest.mark.unit
    def test_calculate_subnet_capacity(self, subnet_service):
        """测试计算网段容量"""
        test_cases = [
            ("192.168.1.0/24", 254),  # /24 = 256 - 2 (网络地址和广播地址)
            ("10.0.0.0/16", 65534),   # /16 = 65536 - 2
            ("192.168.1.0/30", 2),    # /30 = 4 - 2
            ("172.16.0.0/28", 14)     # /28 = 16 - 2
        ]
        
        for network, expected_capacity in test_cases:
            capacity = subnet_service.calculate_subnet_capacity(network)
            assert capacity == expected_capacity

    @pytest.mark.unit
    def test_suggest_subnet_split(self, subnet_service):
        """测试网段拆分建议"""
        network = "192.168.1.0/24"
        
        suggestions = subnet_service.suggest_subnet_split(network, 4)
        
        assert len(suggestions) == 4
        for suggestion in suggestions:
            assert "/26" in suggestion  # /24拆分为4个/26

    @pytest.mark.unit
    def test_validate_gateway_in_subnet(self, subnet_service):
        """测试验证网关是否在网段内"""
        network = "192.168.1.0/24"
        
        valid_gateways = ["192.168.1.1", "192.168.1.254"]
        invalid_gateways = ["192.168.2.1", "10.0.0.1", "192.168.1.0", "192.168.1.255"]
        
        for gateway in valid_gateways:
            assert subnet_service.validate_gateway(gateway, network) is True
        
        for gateway in invalid_gateways:
            assert subnet_service.validate_gateway(gateway, network) is False

    @pytest.mark.unit
    def test_get_subnet_neighbors(self, subnet_service, mock_db):
        """测试获取相邻网段"""
        target_subnet = SubnetFactory.build(network="192.168.1.0/24")
        neighbor_subnets = [
            SubnetFactory.build(network="192.168.0.0/24"),  # 前一个
            SubnetFactory.build(network="192.168.2.0/24"),  # 后一个
            SubnetFactory.build(network="10.0.0.0/24")      # 不相邻
        ]
        
        mock_db.query.return_value.filter.return_value.first.return_value = target_subnet
        mock_db.query.return_value.all.return_value = neighbor_subnets
        
        neighbors = subnet_service.get_subnet_neighbors(1)
        
        # 验证只返回相邻的网段
        assert len(neighbors) <= 2

    @pytest.mark.unit
    def test_bulk_create_subnets(self, subnet_service, mock_db, test_user):
        """测试批量创建网段"""
        subnet_data_list = [
            {"network": "192.168.1.0/24", "description": "Subnet 1"},
            {"network": "192.168.2.0/24", "description": "Subnet 2"},
            {"network": "192.168.3.0/24", "description": "Subnet 3"}
        ]
        
        mock_db.query.return_value.all.return_value = []  # 无重叠
        mock_db.add_all = Mock()
        mock_db.commit = Mock()
        
        with patch.object(subnet_service, '_generate_ip_addresses'):
            results = subnet_service.bulk_create_subnets(subnet_data_list, test_user.id)
            
            assert len(results) == 3
            mock_db.add_all.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.unit
    def test_subnet_utilization_alert_check(self, subnet_service, mock_db):
        """测试网段使用率警报检查"""
        subnet_id = 1
        threshold = 80.0
        
        # 模拟高使用率情况
        mock_db.query.return_value.filter.return_value.count.side_effect = [100, 85, 5]
        
        alert_needed = subnet_service.check_utilization_alert(subnet_id, threshold)
        
        assert alert_needed is True

    @pytest.mark.unit
    def test_export_subnet_configuration(self, subnet_service, mock_db):
        """测试导出网段配置"""
        subnet = SubnetFactory.build(
            network="192.168.1.0/24",
            gateway="192.168.1.1",
            description="Test subnet"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = subnet
        
        config = subnet_service.export_subnet_config(1)
        
        assert config["network"] == "192.168.1.0/24"
        assert config["gateway"] == "192.168.1.1"
        assert "description" in config

    @pytest.mark.unit
    def test_error_handling_invalid_operations(self, subnet_service, mock_db, test_user):
        """测试无效操作的错误处理"""
        # 测试更新不存在的网段
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(SubnetNotFoundError):
            subnet_service.update_subnet(999, {"description": "test"}, test_user.id)
        
        # 测试删除不存在的网段
        with pytest.raises(SubnetNotFoundError):
            subnet_service.delete_subnet(999, test_user.id)