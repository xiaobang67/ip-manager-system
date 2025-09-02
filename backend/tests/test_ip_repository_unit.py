import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session, Query
from sqlalchemy import func
from app.repositories.ip_repository import IPRepository
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.ip_address import IPAddressCreate, IPAddressUpdate
from datetime import datetime
import ipaddress


class TestIPRepository:
    """IP仓储层单元测试"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_query(self):
        return Mock(spec=Query)

    @pytest.fixture
    def ip_repo(self, mock_db):
        return IPRepository(mock_db)

    @pytest.fixture
    def sample_ip_create(self):
        return IPAddressCreate(
            ip_address="192.168.1.100",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            hostname="test-host"
        )

    @pytest.fixture
    def sample_ip_update(self):
        return IPAddressUpdate(
            hostname="updated-host",
            status=IPStatus.ALLOCATED
        )

    @pytest.fixture
    def sample_ip_record(self):
        return IPAddress(
            id=1,
            ip_address="192.168.1.100",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            hostname="test-host",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def test_create_ip_success(self, ip_repo, mock_db, sample_ip_create):
        """测试成功创建IP地址记录"""
        # 执行测试
        result = ip_repo.create(sample_ip_create)

        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证创建的对象属性
        added_ip = mock_db.add.call_args[0][0]
        assert added_ip.ip_address == "192.168.1.100"
        assert added_ip.subnet_id == 1
        assert added_ip.status == IPStatus.AVAILABLE
        assert added_ip.hostname == "test-host"

    def test_bulk_create_ips(self, ip_repo, mock_db):
        """测试批量创建IP地址记录"""
        ip_data_list = [
            IPAddressCreate(ip_address="192.168.1.100", subnet_id=1),
            IPAddressCreate(ip_address="192.168.1.101", subnet_id=1),
            IPAddressCreate(ip_address="192.168.1.102", subnet_id=1)
        ]

        # 模拟返回的IP对象
        mock_ips = [
            IPAddress(id=1, ip_address="192.168.1.100", subnet_id=1),
            IPAddress(id=2, ip_address="192.168.1.101", subnet_id=1),
            IPAddress(id=3, ip_address="192.168.1.102", subnet_id=1)
        ]

        # 执行测试
        result = ip_repo.bulk_create(ip_data_list)

        # 验证数据库操作
        mock_db.add_all.assert_called_once()
        mock_db.commit.assert_called_once()
        assert mock_db.refresh.call_count == 3  # 每个IP都要刷新

        # 验证批量添加的对象
        added_ips = mock_db.add_all.call_args[0][0]
        assert len(added_ips) == 3
        assert added_ips[0].ip_address == "192.168.1.100"
        assert added_ips[1].ip_address == "192.168.1.101"
        assert added_ips[2].ip_address == "192.168.1.102"

    def test_get_by_id_found(self, ip_repo, mock_db, mock_query, sample_ip_record):
        """测试根据ID获取IP地址记录（找到）"""
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_ip_record

        result = ip_repo.get_by_id(1)

        assert result == sample_ip_record
        mock_db.query.assert_called_once_with(IPAddress)
        mock_query.filter.assert_called_once()
        mock_query.first.assert_called_once()

    def test_get_by_id_not_found(self, ip_repo, mock_db, mock_query):
        """测试根据ID获取IP地址记录（未找到）"""
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = ip_repo.get_by_id(999)

        assert result is None

    def test_get_by_ip_address(self, ip_repo, mock_db, mock_query, sample_ip_record):
        """测试根据IP地址获取记录"""
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_ip_record

        result = ip_repo.get_by_ip_address("192.168.1.100")

        assert result == sample_ip_record
        mock_query.filter.assert_called_once()

    def test_get_by_subnet(self, ip_repo, mock_db, mock_query, sample_ip_record):
        """测试获取网段下的IP地址"""
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_ip_record]

        result = ip_repo.get_by_subnet(subnet_id=1, skip=0, limit=10)

        assert len(result) == 1
        assert result[0] == sample_ip_record
        mock_query.filter.assert_called_once()
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(10)

    def test_get_available_ips(self, ip_repo, mock_db, mock_query, sample_ip_record):
        """测试获取可用的IP地址"""
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_ip_record]

        result = ip_repo.get_available_ips(subnet_id=1, limit=5)

        assert len(result) == 1
        assert result[0] == sample_ip_record
        mock_query.limit.assert_called_once_with(5)

    def test_update_ip_success(self, ip_repo, mock_db, sample_ip_record, sample_ip_update):
        """测试成功更新IP地址记录"""
        # 模拟get_by_id返回记录
        with patch.object(ip_repo, 'get_by_id', return_value=sample_ip_record):
            result = ip_repo.update(1, sample_ip_update)

        # 验证数据库操作
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(sample_ip_record)
        
        # 验证属性更新
        assert sample_ip_record.hostname == "updated-host"
        assert sample_ip_record.status == IPStatus.ALLOCATED

    def test_update_ip_not_found(self, ip_repo, sample_ip_update):
        """测试更新不存在的IP地址记录"""
        with patch.object(ip_repo, 'get_by_id', return_value=None):
            result = ip_repo.update(999, sample_ip_update)

        assert result is None

    def test_delete_ip_success(self, ip_repo, mock_db, sample_ip_record):
        """测试成功删除IP地址记录"""
        with patch.object(ip_repo, 'get_by_id', return_value=sample_ip_record):
            result = ip_repo.delete(1)

        assert result is True
        mock_db.delete.assert_called_once_with(sample_ip_record)
        mock_db.commit.assert_called_once()

    def test_delete_ip_not_found(self, ip_repo):
        """测试删除不存在的IP地址记录"""
        with patch.object(ip_repo, 'get_by_id', return_value=None):
            result = ip_repo.delete(999)

        assert result is False

    def test_delete_by_subnet_with_status_filter(self, ip_repo, mock_db, mock_query):
        """测试按网段和状态删除IP地址"""
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.delete.return_value = 5

        result = ip_repo.delete_by_subnet(subnet_id=1, status_filter=IPStatus.AVAILABLE)

        assert result == 5
        mock_query.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_by_subnet_without_status_filter(self, ip_repo, mock_db, mock_query):
        """测试按网段删除所有IP地址"""
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.delete.return_value = 10

        result = ip_repo.delete_by_subnet(subnet_id=1)

        assert result == 10

    def test_check_ip_conflicts(self, ip_repo, mock_db, mock_query):
        """测试检查IP地址冲突"""
        # 模拟重复IP查询
        duplicate_ips = [("192.168.1.100",), ("192.168.1.101",)]
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = duplicate_ips

        # 模拟冲突IP记录查询
        conflict_records = [
            IPAddress(id=1, ip_address="192.168.1.100", subnet_id=1),
            IPAddress(id=2, ip_address="192.168.1.100", subnet_id=1)
        ]
        
        # 第二次查询返回冲突记录
        mock_query.all.side_effect = [duplicate_ips, conflict_records]

        result = ip_repo.check_ip_conflicts(subnet_id=1)

        assert len(result) == 2
        assert result[0].ip_address == "192.168.1.100"
        assert result[1].ip_address == "192.168.1.100"

    def test_check_ip_conflicts_no_duplicates(self, ip_repo, mock_db, mock_query):
        """测试检查IP地址冲突（无冲突）"""
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.having.return_value = mock_query
        mock_query.all.return_value = []

        result = ip_repo.check_ip_conflicts(subnet_id=1)

        assert len(result) == 0

    def test_mark_conflicts(self, ip_repo, mock_db, mock_query):
        """测试标记IP地址为冲突状态"""
        ip_addresses = ["192.168.1.100", "192.168.1.101"]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 2

        result = ip_repo.mark_conflicts(ip_addresses)

        assert result == 2
        mock_query.update.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_ip_statistics(self, ip_repo, mock_db, mock_query):
        """测试获取IP地址统计信息"""
        # 模拟统计查询结果
        stats_data = [
            (IPStatus.AVAILABLE, 70),
            (IPStatus.ALLOCATED, 25),
            (IPStatus.RESERVED, 3),
            (IPStatus.CONFLICT, 2)
        ]
        
        mock_db.query.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = stats_data

        result = ip_repo.get_ip_statistics()

        expected_stats = {
            IPStatus.AVAILABLE: 70,
            IPStatus.ALLOCATED: 25,
            IPStatus.RESERVED: 3,
            IPStatus.CONFLICT: 2,
            'total': 100
        }
        
        assert result['total'] == 100
        assert result[IPStatus.AVAILABLE] == 70
        assert result[IPStatus.ALLOCATED] == 25
        assert result[IPStatus.RESERVED] == 3
        assert result[IPStatus.CONFLICT] == 2

    def test_get_ip_statistics_with_subnet_filter(self, ip_repo, mock_db, mock_query):
        """测试获取特定网段的IP统计信息"""
        stats_data = [(IPStatus.AVAILABLE, 50), (IPStatus.ALLOCATED, 20)]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = stats_data

        result = ip_repo.get_ip_statistics(subnet_id=1)

        mock_query.filter.assert_called_once()
        assert result['total'] == 70

    def test_search_ips_with_all_filters(self, ip_repo, mock_db, mock_query, sample_ip_record):
        """测试使用所有过滤条件搜索IP地址"""
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_ip_record]

        result = ip_repo.search(
            query="192.168.1",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            skip=0,
            limit=10
        )

        assert len(result) == 1
        assert result[0] == sample_ip_record
        # 验证所有过滤条件都被应用
        assert mock_query.filter.call_count == 3  # query, subnet_id, status

    def test_search_ips_without_filters(self, ip_repo, mock_db, mock_query, sample_ip_record):
        """测试不使用过滤条件搜索IP地址"""
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_ip_record]

        result = ip_repo.search(skip=0, limit=10)

        assert len(result) == 1
        # 没有过滤条件时不应该调用filter
        mock_query.filter.assert_not_called()

    def test_count_by_subnet(self, ip_repo, mock_db, mock_query):
        """测试统计网段中的IP地址数量"""
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 254

        result = ip_repo.count_by_subnet(subnet_id=1)

        assert result == 254
        mock_query.filter.assert_called_once()
        mock_query.count.assert_called_once()

    def test_sync_subnet_ips_add_and_remove(self, ip_repo, mock_db, mock_query):
        """测试同步网段IP地址（添加和删除）"""
        # 模拟现有IP地址
        existing_ips = [
            IPAddress(ip_address="192.168.1.1", subnet_id=1),
            IPAddress(ip_address="192.168.1.2", subnet_id=1),
            IPAddress(ip_address="192.168.1.5", subnet_id=1)  # 这个不在新网段中
        ]
        
        with patch.object(ip_repo, 'get_by_subnet', return_value=existing_ips):
            mock_db.query.return_value = mock_query
            mock_query.filter.return_value = mock_query
            mock_query.delete.return_value = 1  # 删除1个IP

            result = ip_repo.sync_subnet_ips(1, "192.168.1.0/30")  # 只有.1和.2两个主机IP

            # 验证结果
            assert result['removed'] == 1  # 删除了.5
            assert result['added'] == 0   # .1和.2已存在，无需添加
            assert result['kept'] == 2    # 保持.1和.2

    def test_sync_subnet_ips_invalid_network(self, ip_repo):
        """测试同步无效网段格式"""
        with pytest.raises(ValueError, match="无效的网段格式"):
            ip_repo.sync_subnet_ips(1, "invalid_network")

    def test_get_ip_range_status(self, ip_repo, mock_db, mock_query):
        """测试获取IP地址范围状态"""
        # 模拟数据库中的IP记录
        db_ips = [
            IPAddress(
                ip_address="192.168.1.1",
                status=IPStatus.ALLOCATED,
                hostname="host1",
                mac_address="00:11:22:33:44:55",
                assigned_to="用户1"
            ),
            IPAddress(
                ip_address="192.168.1.3",
                status=IPStatus.RESERVED,
                hostname="host3",
                assigned_to="保留"
            )
        ]
        
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = db_ips

        result = ip_repo.get_ip_range_status("192.168.1.1", "192.168.1.4")

        # 验证结果包含范围内的所有IP
        assert len(result) == 4
        
        # 验证已管理的IP状态
        ip1_status = next(item for item in result if item['ip_address'] == '192.168.1.1')
        assert ip1_status['status'] == IPStatus.ALLOCATED
        assert ip1_status['hostname'] == 'host1'
        
        # 验证未管理的IP状态
        ip2_status = next(item for item in result if item['ip_address'] == '192.168.1.2')
        assert ip2_status['status'] == 'not_managed'
        assert ip2_status['hostname'] is None

    def test_get_ip_range_status_invalid_ip(self, ip_repo):
        """测试获取无效IP范围状态"""
        result = ip_repo.get_ip_range_status("invalid_ip", "192.168.1.2")
        assert result == []