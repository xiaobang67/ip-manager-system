import pytest
from unittest.mock import Mock, patch
from app.services.subnet_service import SubnetService
from app.schemas.subnet import SubnetCreate, SubnetUpdate
from app.models.subnet import Subnet
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
from datetime import datetime


class TestSubnetService:
    """网段服务单元测试"""

    def setup_method(self):
        """测试前置设置"""
        self.mock_db = Mock()
        self.subnet_service = SubnetService(self.mock_db)
        self.subnet_service.subnet_repo = Mock()
        self.subnet_service.ip_service = Mock()

    def test_create_subnet_success(self):
        """测试成功创建网段"""
        # 准备测试数据
        subnet_data = SubnetCreate(
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="测试网段"
        )
        
        mock_subnet = Subnet(
            id=1,
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="测试网段",
            created_by=1,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # 设置mock返回值
        self.subnet_service.subnet_repo.check_network_overlap.return_value = []
        self.subnet_service.subnet_repo.create.return_value = mock_subnet
        self.subnet_service.ip_service.generate_ips_for_subnet.return_value = []

        # 执行测试
        result = self.subnet_service.create_subnet(subnet_data, 1)

        # 验证结果
        assert result.network == "192.168.1.0/24"
        assert result.netmask == "255.255.255.0"
        assert result.gateway == "192.168.1.1"
        assert result.description == "测试网段"
        
        # 验证方法调用
        self.subnet_service.subnet_repo.check_network_overlap.assert_called_once_with("192.168.1.0/24")
        self.subnet_service.subnet_repo.create.assert_called_once_with(subnet_data, 1)
        self.subnet_service.ip_service.generate_ips_for_subnet.assert_called_once_with(1, "192.168.1.0/24")

    def test_create_subnet_with_overlap(self):
        """测试创建重叠网段时抛出异常"""
        subnet_data = SubnetCreate(
            network="192.168.1.0/24",
            netmask="255.255.255.0"
        )
        
        # 模拟重叠网段
        overlapping_subnet = Subnet(id=2, network="192.168.1.0/25")
        self.subnet_service.subnet_repo.check_network_overlap.return_value = [overlapping_subnet]

        # 执行测试并验证异常
        with pytest.raises(ConflictError) as exc_info:
            self.subnet_service.create_subnet(subnet_data, 1)
        
        assert "网段与现有网段重叠" in str(exc_info.value)

    def test_create_subnet_ip_generation_failure(self):
        """测试IP生成失败时回滚网段创建"""
        subnet_data = SubnetCreate(
            network="192.168.1.0/24",
            netmask="255.255.255.0"
        )
        
        mock_subnet = Subnet(id=1, network="192.168.1.0/24")
        
        # 设置mock返回值
        self.subnet_service.subnet_repo.check_network_overlap.return_value = []
        self.subnet_service.subnet_repo.create.return_value = mock_subnet
        self.subnet_service.ip_service.generate_ips_for_subnet.side_effect = Exception("IP生成失败")

        # 执行测试并验证异常
        with pytest.raises(ValidationError) as exc_info:
            self.subnet_service.create_subnet(subnet_data, 1)
        
        assert "生成IP地址失败" in str(exc_info.value)
        # 验证回滚操作
        self.subnet_service.subnet_repo.delete.assert_called_once_with(1)

    def test_get_subnet_success(self):
        """测试成功获取网段"""
        mock_subnet = Subnet(
            id=1,
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.subnet_service.subnet_repo.get_by_id.return_value = mock_subnet

        result = self.subnet_service.get_subnet(1)

        assert result.id == 1
        assert result.network == "192.168.1.0/24"
        self.subnet_service.subnet_repo.get_by_id.assert_called_once_with(1)

    def test_get_subnet_not_found(self):
        """测试获取不存在的网段"""
        self.subnet_service.subnet_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            self.subnet_service.get_subnet(1)
        
        assert "网段不存在" in str(exc_info.value)

    def test_get_subnets_with_stats(self):
        """测试获取带统计信息的网段列表"""
        mock_stats = [
            {
                'subnet': Subnet(id=1, network="192.168.1.0/24", netmask="255.255.255.0", created_at=datetime.now(), updated_at=datetime.now()),
                'ip_count': 254,
                'allocated_count': 10,
                'available_count': 244
            }
        ]
        
        self.subnet_service.subnet_repo.get_with_stats.return_value = mock_stats
        self.subnet_service.subnet_repo.count.return_value = 1

        subnets, total = self.subnet_service.get_subnets(0, 10)

        assert len(subnets) == 1
        assert total == 1
        assert subnets[0].ip_count == 254
        assert subnets[0].allocated_count == 10
        assert subnets[0].available_count == 244

    def test_update_subnet_success(self):
        """测试成功更新网段"""
        existing_subnet = Subnet(
            id=1,
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        updated_subnet = Subnet(
            id=1,
            network="192.168.2.0/24",
            netmask="255.255.255.0",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        subnet_data = SubnetUpdate(
            network="192.168.2.0/24",
            description="更新的描述"
        )

        self.subnet_service.subnet_repo.get_by_id.return_value = existing_subnet
        self.subnet_service.subnet_repo.check_network_overlap.return_value = []
        self.subnet_service.subnet_repo.update.return_value = updated_subnet
        self.subnet_service.ip_service.cleanup_unallocated_ips.return_value = 10
        self.subnet_service.ip_service.generate_ips_for_subnet.return_value = []

        result = self.subnet_service.update_subnet(1, subnet_data)

        assert result.network == "192.168.2.0/24"
        # 验证IP地址重新生成
        self.subnet_service.ip_service.cleanup_unallocated_ips.assert_called_once_with(1)
        self.subnet_service.ip_service.generate_ips_for_subnet.assert_called_once_with(1, "192.168.2.0/24")

    def test_update_subnet_not_found(self):
        """测试更新不存在的网段"""
        self.subnet_service.subnet_repo.get_by_id.return_value = None
        
        subnet_data = SubnetUpdate(description="更新的描述")

        with pytest.raises(NotFoundError):
            self.subnet_service.update_subnet(1, subnet_data)

    def test_update_subnet_with_overlap(self):
        """测试更新网段时检测到重叠"""
        existing_subnet = Subnet(id=1, network="192.168.1.0/24")
        overlapping_subnet = Subnet(id=2, network="192.168.2.0/25")
        
        subnet_data = SubnetUpdate(network="192.168.2.0/24")

        self.subnet_service.subnet_repo.get_by_id.return_value = existing_subnet
        self.subnet_service.subnet_repo.check_network_overlap.return_value = [overlapping_subnet]

        with pytest.raises(ConflictError) as exc_info:
            self.subnet_service.update_subnet(1, subnet_data)
        
        assert "网段与现有网段重叠" in str(exc_info.value)

    def test_delete_subnet_success(self):
        """测试成功删除网段"""
        mock_subnet = Subnet(id=1, network="192.168.1.0/24")
        
        self.subnet_service.subnet_repo.get_by_id.return_value = mock_subnet
        self.subnet_service.subnet_repo.has_allocated_ips.return_value = False
        self.subnet_service.subnet_repo.delete.return_value = True

        result = self.subnet_service.delete_subnet(1)

        assert result is True
        self.subnet_service.subnet_repo.delete.assert_called_once_with(1)

    def test_delete_subnet_not_found(self):
        """测试删除不存在的网段"""
        self.subnet_service.subnet_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            self.subnet_service.delete_subnet(1)

    def test_delete_subnet_with_allocated_ips(self):
        """测试删除有已分配IP的网段"""
        mock_subnet = Subnet(id=1, network="192.168.1.0/24")
        
        self.subnet_service.subnet_repo.get_by_id.return_value = mock_subnet
        self.subnet_service.subnet_repo.has_allocated_ips.return_value = True
        self.subnet_service.subnet_repo.get_allocated_ip_count.return_value = 5

        with pytest.raises(ConflictError) as exc_info:
            self.subnet_service.delete_subnet(1)
        
        assert "存在 5 个已分配的IP地址" in str(exc_info.value)

    def test_validate_subnet_valid(self):
        """测试验证有效网段"""
        self.subnet_service.subnet_repo.check_network_overlap.return_value = []

        result = self.subnet_service.validate_subnet("192.168.1.0/24")

        assert result.is_valid is True
        assert result.message == "网段验证通过"
        assert result.overlapping_subnets is None

    def test_validate_subnet_invalid_format(self):
        """测试验证无效格式的网段"""
        result = self.subnet_service.validate_subnet("invalid-network")

        assert result.is_valid is False
        assert "无效的网段格式" in result.message

    def test_validate_subnet_with_overlap(self):
        """测试验证重叠的网段"""
        overlapping_subnet = Subnet(id=1, network="192.168.1.0/25", netmask="255.255.255.128", created_at=datetime.now(), updated_at=datetime.now())
        self.subnet_service.subnet_repo.check_network_overlap.return_value = [overlapping_subnet]

        result = self.subnet_service.validate_subnet("192.168.1.0/24")

        assert result.is_valid is False
        assert "网段与 1 个现有网段重叠" in result.message
        assert len(result.overlapping_subnets) == 1

    def test_search_subnets(self):
        """测试搜索网段"""
        mock_subnets = [
            Subnet(id=1, network="192.168.1.0/24", netmask="255.255.255.0", description="测试网段1", created_at=datetime.now(), updated_at=datetime.now()),
            Subnet(id=2, network="192.168.2.0/24", netmask="255.255.255.0", description="测试网段2", created_at=datetime.now(), updated_at=datetime.now())
        ]
        
        self.subnet_service.subnet_repo.search.return_value = mock_subnets

        results, total = self.subnet_service.search_subnets("测试", 0, 10)

        assert len(results) == 2
        assert total == 2
        assert results[0].description == "测试网段1"
        self.subnet_service.subnet_repo.search.assert_called_once_with("测试", 0, 10)

    def test_get_subnets_by_vlan(self):
        """测试根据VLAN ID获取网段"""
        mock_subnets = [
            Subnet(id=1, network="192.168.1.0/24", netmask="255.255.255.0", vlan_id=100, created_at=datetime.now(), updated_at=datetime.now())
        ]
        
        self.subnet_service.subnet_repo.get_by_vlan.return_value = mock_subnets

        results = self.subnet_service.get_subnets_by_vlan(100)

        assert len(results) == 1
        assert results[0].vlan_id == 100
        self.subnet_service.subnet_repo.get_by_vlan.assert_called_once_with(100)