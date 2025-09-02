import pytest
from unittest.mock import Mock, MagicMock
from app.repositories.subnet_repository import SubnetRepository
from app.models.subnet import Subnet
from app.models.ip_address import IPAddress, IPStatus
from app.schemas.subnet import SubnetCreate, SubnetUpdate
from datetime import datetime


class TestSubnetRepository:
    """网段仓库单元测试"""

    def setup_method(self):
        """测试前置设置"""
        self.mock_db = Mock()
        self.subnet_repo = SubnetRepository(self.mock_db)

    def test_create_subnet(self):
        """测试创建网段"""
        subnet_data = SubnetCreate(
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="测试网段"
        )

        # 执行测试
        result = self.subnet_repo.create(subnet_data, 1)

        # 验证数据库操作
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

        # 验证创建的对象属性
        added_subnet = self.mock_db.add.call_args[0][0]
        assert added_subnet.network == "192.168.1.0/24"
        assert added_subnet.netmask == "255.255.255.0"
        assert added_subnet.gateway == "192.168.1.1"
        assert added_subnet.description == "测试网段"
        assert added_subnet.created_by == 1

    def test_get_by_id(self):
        """测试根据ID获取网段"""
        mock_subnet = Subnet(id=1, network="192.168.1.0/24")
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_subnet
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.get_by_id(1)

        assert result == mock_subnet
        self.mock_db.query.assert_called_once_with(Subnet)
        mock_query.filter.assert_called_once()

    def test_get_by_network(self):
        """测试根据网段地址获取网段"""
        mock_subnet = Subnet(id=1, network="192.168.1.0/24")
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_subnet
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.get_by_network("192.168.1.0/24")

        assert result == mock_subnet
        self.mock_db.query.assert_called_once_with(Subnet)

    def test_get_all(self):
        """测试获取所有网段"""
        mock_subnets = [
            Subnet(id=1, network="192.168.1.0/24"),
            Subnet(id=2, network="192.168.2.0/24")
        ]
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_subnets
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.get_all(0, 10)

        assert len(result) == 2
        assert result == mock_subnets
        mock_query.offset.assert_called_once_with(0)
        mock_query.offset.return_value.limit.assert_called_once_with(10)

    def test_count(self):
        """测试获取网段总数"""
        mock_query = Mock()
        mock_query.count.return_value = 5
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.count()

        assert result == 5
        self.mock_db.query.assert_called_once_with(Subnet)

    def test_update_subnet(self):
        """测试更新网段"""
        mock_subnet = Subnet(id=1, network="192.168.1.0/24", description="原描述")
        
        # 模拟get_by_id返回
        self.subnet_repo.get_by_id = Mock(return_value=mock_subnet)
        
        subnet_data = SubnetUpdate(description="新描述", location="新位置")

        result = self.subnet_repo.update(1, subnet_data)

        # 验证属性更新
        assert mock_subnet.description == "新描述"
        assert mock_subnet.location == "新位置"
        
        # 验证数据库操作
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(mock_subnet)

    def test_update_subnet_not_found(self):
        """测试更新不存在的网段"""
        self.subnet_repo.get_by_id = Mock(return_value=None)
        
        subnet_data = SubnetUpdate(description="新描述")

        result = self.subnet_repo.update(1, subnet_data)

        assert result is None

    def test_delete_subnet(self):
        """测试删除网段"""
        mock_subnet = Subnet(id=1, network="192.168.1.0/24")
        self.subnet_repo.get_by_id = Mock(return_value=mock_subnet)

        result = self.subnet_repo.delete(1)

        assert result is True
        self.mock_db.delete.assert_called_once_with(mock_subnet)
        self.mock_db.commit.assert_called_once()

    def test_delete_subnet_not_found(self):
        """测试删除不存在的网段"""
        self.subnet_repo.get_by_id = Mock(return_value=None)

        result = self.subnet_repo.delete(1)

        assert result is False
        self.mock_db.delete.assert_not_called()

    def test_check_network_overlap_no_overlap(self):
        """测试检查网段重叠 - 无重叠"""
        mock_subnets = [
            Subnet(id=1, network="192.168.2.0/24"),
            Subnet(id=2, network="10.0.0.0/8")
        ]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_subnets
        mock_query.all.return_value = mock_subnets
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.check_network_overlap("192.168.1.0/24")

        assert len(result) == 0

    def test_check_network_overlap_with_overlap(self):
        """测试检查网段重叠 - 有重叠"""
        mock_subnets = [
            Subnet(id=1, network="192.168.1.0/25"),  # 与192.168.1.0/24重叠
            Subnet(id=2, network="10.0.0.0/8")       # 不重叠
        ]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_subnets
        mock_query.all.return_value = mock_subnets
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.check_network_overlap("192.168.1.0/24")

        assert len(result) == 1
        assert result[0].network == "192.168.1.0/25"

    def test_check_network_overlap_exclude_id(self):
        """测试检查网段重叠 - 排除指定ID"""
        mock_subnets = [
            Subnet(id=2, network="192.168.2.0/24")
        ]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_subnets
        mock_query.all.return_value = mock_subnets
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.check_network_overlap("192.168.1.0/24", exclude_id=1)

        # 验证过滤条件包含排除ID
        mock_query.filter.assert_called_once()

    def test_get_allocated_ip_count(self):
        """测试获取已分配IP数量"""
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 10
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.get_allocated_ip_count(1)

        assert result == 10
        self.mock_db.query.assert_called_once_with(IPAddress)

    def test_has_allocated_ips_true(self):
        """测试检查是否有已分配IP - 有"""
        self.subnet_repo.get_allocated_ip_count = Mock(return_value=5)

        result = self.subnet_repo.has_allocated_ips(1)

        assert result is True

    def test_has_allocated_ips_false(self):
        """测试检查是否有已分配IP - 无"""
        self.subnet_repo.get_allocated_ip_count = Mock(return_value=0)

        result = self.subnet_repo.has_allocated_ips(1)

        assert result is False

    def test_search_subnets(self):
        """测试搜索网段"""
        mock_subnets = [
            Subnet(id=1, network="192.168.1.0/24", description="测试网段")
        ]
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_subnets
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.search("测试", 0, 10)

        assert len(result) == 1
        assert result[0].description == "测试网段"
        mock_query.filter.assert_called_once()
        mock_query.filter.return_value.offset.assert_called_once_with(0)
        mock_query.filter.return_value.offset.return_value.limit.assert_called_once_with(10)

    def test_get_by_vlan(self):
        """测试根据VLAN ID获取网段"""
        mock_subnets = [
            Subnet(id=1, network="192.168.1.0/24", vlan_id=100)
        ]
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_subnets
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.get_by_vlan(100)

        assert len(result) == 1
        assert result[0].vlan_id == 100
        mock_query.filter.assert_called_once()

    def test_get_with_stats(self):
        """测试获取带统计信息的网段"""
        # 这个测试比较复杂，因为涉及到复杂的SQL查询
        # 这里简化测试，主要验证方法调用
        mock_results = [
            (Subnet(id=1, network="192.168.1.0/24"), 254, 10, 244)
        ]
        
        mock_query = Mock()
        mock_query.outerjoin.return_value.offset.return_value.limit.return_value.all.return_value = mock_results
        self.mock_db.query.return_value = mock_query

        result = self.subnet_repo.get_with_stats(0, 10)

        assert len(result) == 1
        assert result[0]['subnet'].network == "192.168.1.0/24"
        assert result[0]['ip_count'] == 254
        assert result[0]['allocated_count'] == 10
        assert result[0]['available_count'] == 244