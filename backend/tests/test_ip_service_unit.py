import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.ip_service import IPService
from app.repositories.ip_repository import IPRepository
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.schemas.ip_address import (
    IPAddressCreate, IPAllocationRequest, IPReservationRequest,
    IPReleaseRequest, IPSearchRequest, IPSyncResponse
)
from app.core.exceptions import ValidationError, NotFoundError, ConflictError
from datetime import datetime
import ipaddress


class TestIPService:
    """IP服务单元测试"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_ip_repo(self):
        return Mock(spec=IPRepository)

    @pytest.fixture
    def ip_service(self, mock_db, mock_ip_repo):
        service = IPService(mock_db)
        service.ip_repo = mock_ip_repo
        return service

    @pytest.fixture
    def sample_subnet(self):
        return Subnet(
            id=1,
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            gateway="192.168.1.1",
            description="测试网段"
        )

    @pytest.fixture
    def sample_ip(self):
        return IPAddress(
            id=1,
            ip_address="192.168.1.100",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    def test_generate_ips_for_subnet_success(self, ip_service, mock_db, mock_ip_repo, sample_subnet):
        """测试成功为网段生成IP地址"""
        # 准备测试数据
        network = "192.168.1.0/30"  # 小网段，只有2个主机IP
        mock_db.query.return_value.filter.return_value.first.return_value = sample_subnet
        mock_ip_repo.get_by_ip_address.return_value = None
        
        # 模拟批量创建IP
        created_ips = [
            IPAddress(id=1, ip_address="192.168.1.1", subnet_id=1, status=IPStatus.AVAILABLE),
            IPAddress(id=2, ip_address="192.168.1.2", subnet_id=1, status=IPStatus.AVAILABLE)
        ]
        mock_ip_repo.bulk_create.return_value = created_ips

        # 执行测试
        result = ip_service.generate_ips_for_subnet(1, network)

        # 验证结果
        assert len(result) == 2
        assert result[0].ip_address == "192.168.1.1"
        assert result[1].ip_address == "192.168.1.2"
        mock_ip_repo.bulk_create.assert_called_once()

    def test_generate_ips_for_subnet_invalid_network(self, ip_service, mock_db, sample_subnet):
        """测试无效网段格式"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_subnet
        
        with pytest.raises(ValueError, match="无效的网段格式"):
            ip_service.generate_ips_for_subnet(1, "invalid_network")

    def test_generate_ips_for_subnet_nonexistent_subnet(self, ip_service, mock_db):
        """测试不存在的网段"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="网段不存在"):
            ip_service.generate_ips_for_subnet(999, "192.168.1.0/24")

    def test_generate_ips_for_subnet_too_large(self, ip_service, mock_db, sample_subnet):
        """测试网段过大的情况"""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_subnet
        
        with pytest.raises(ValidationError, match="网段过大"):
            ip_service.generate_ips_for_subnet(1, "10.0.0.0/15")  # /15网段有131072个地址，超过65536

    def test_sync_subnet_ips_success(self, ip_service, mock_ip_repo):
        """测试成功同步网段IP地址"""
        # 模拟同步结果
        sync_stats = {'added': 5, 'removed': 2, 'kept': 10}
        mock_ip_repo.sync_subnet_ips.return_value = sync_stats
        
        # 模拟无冲突
        with patch.object(ip_service, 'detect_ip_conflicts', return_value=[]):
            with patch.object(ip_service, 'resolve_ip_conflicts'):
                result = ip_service.sync_subnet_ips(1, "192.168.1.0/24")

        # 验证结果
        assert isinstance(result, IPSyncResponse)
        assert result.subnet_id == 1
        assert result.network == "192.168.1.0/24"
        assert result.added == 5
        assert result.removed == 2
        assert result.kept == 10
        assert "同步完成" in result.message

    def test_sync_subnet_ips_with_conflicts(self, ip_service, mock_ip_repo):
        """测试同步时处理冲突"""
        sync_stats = {'added': 3, 'removed': 1, 'kept': 8}
        mock_ip_repo.sync_subnet_ips.return_value = sync_stats
        
        # 模拟有冲突
        mock_conflicts = [Mock()]
        with patch.object(ip_service, 'detect_ip_conflicts', return_value=mock_conflicts):
            with patch.object(ip_service, 'resolve_ip_conflicts') as mock_resolve:
                result = ip_service.sync_subnet_ips(1, "192.168.1.0/24")
                mock_resolve.assert_called_once_with(mock_conflicts)

    def test_allocate_ip_with_preferred_ip(self, ip_service, mock_ip_repo, sample_ip):
        """测试分配指定的IP地址"""
        # 准备测试数据
        request = IPAllocationRequest(
            subnet_id=1,
            preferred_ip="192.168.1.100",
            hostname="test-host",
            assigned_to="测试用户"
        )
        
        # 模拟找到可用的首选IP
        sample_ip.status = IPStatus.AVAILABLE
        mock_ip_repo.get_by_ip_address.return_value = sample_ip
        mock_ip_repo.update.return_value = sample_ip

        # 执行测试
        result = ip_service.allocate_ip(request, allocated_by=1)

        # 验证结果
        assert result.ip_address == "192.168.1.100"
        mock_ip_repo.update.assert_called_once()

    def test_allocate_ip_preferred_not_available(self, ip_service, mock_ip_repo, sample_ip):
        """测试首选IP不可用的情况"""
        request = IPAllocationRequest(
            subnet_id=1,
            preferred_ip="192.168.1.100"
        )
        
        # 模拟首选IP已被分配
        sample_ip.status = IPStatus.ALLOCATED
        mock_ip_repo.get_by_ip_address.return_value = sample_ip

        with pytest.raises(ConflictError, match="不可用"):
            ip_service.allocate_ip(request, allocated_by=1)

    def test_allocate_ip_auto_assignment(self, ip_service, mock_ip_repo, sample_ip):
        """测试自动分配IP地址"""
        request = IPAllocationRequest(
            subnet_id=1,
            hostname="auto-host"
        )
        
        # 模拟没有首选IP，自动分配
        mock_ip_repo.get_available_ips.return_value = [sample_ip]
        mock_ip_repo.update.return_value = sample_ip

        result = ip_service.allocate_ip(request, allocated_by=1)

        assert result.ip_address == "192.168.1.100"
        mock_ip_repo.get_available_ips.assert_called_once_with(1, limit=1)

    def test_allocate_ip_no_available(self, ip_service, mock_ip_repo):
        """测试没有可用IP的情况"""
        request = IPAllocationRequest(subnet_id=1)
        
        mock_ip_repo.get_available_ips.return_value = []

        with pytest.raises(NotFoundError, match="没有可用的IP地址"):
            ip_service.allocate_ip(request, allocated_by=1)

    def test_reserve_ip_success(self, ip_service, mock_ip_repo, sample_ip):
        """测试成功保留IP地址"""
        request = IPReservationRequest(
            ip_address="192.168.1.100",
            reason="测试保留"
        )
        
        sample_ip.status = IPStatus.AVAILABLE
        mock_ip_repo.get_by_ip_address.return_value = sample_ip
        mock_ip_repo.update.return_value = sample_ip

        result = ip_service.reserve_ip(request, reserved_by=1)

        assert result.ip_address == "192.168.1.100"
        mock_ip_repo.update.assert_called_once()

    def test_reserve_ip_not_found(self, ip_service, mock_ip_repo):
        """测试保留不存在的IP"""
        request = IPReservationRequest(ip_address="192.168.1.100")
        
        mock_ip_repo.get_by_ip_address.return_value = None

        with pytest.raises(NotFoundError, match="不存在"):
            ip_service.reserve_ip(request, reserved_by=1)

    def test_reserve_ip_not_available(self, ip_service, mock_ip_repo, sample_ip):
        """测试保留不可用的IP"""
        request = IPReservationRequest(ip_address="192.168.1.100")
        
        sample_ip.status = IPStatus.ALLOCATED
        mock_ip_repo.get_by_ip_address.return_value = sample_ip

        with pytest.raises(ConflictError, match="不可用"):
            ip_service.reserve_ip(request, reserved_by=1)

    def test_release_ip_success(self, ip_service, mock_ip_repo, sample_ip):
        """测试成功释放IP地址"""
        request = IPReleaseRequest(
            ip_address="192.168.1.100",
            reason="测试释放"
        )
        
        sample_ip.status = IPStatus.ALLOCATED
        mock_ip_repo.get_by_ip_address.return_value = sample_ip
        mock_ip_repo.update.return_value = sample_ip

        result = ip_service.release_ip(request, released_by=1)

        assert result.ip_address == "192.168.1.100"
        mock_ip_repo.update.assert_called_once()

    def test_release_ip_invalid_status(self, ip_service, mock_ip_repo, sample_ip):
        """测试释放状态无效的IP"""
        request = IPReleaseRequest(ip_address="192.168.1.100")
        
        sample_ip.status = IPStatus.AVAILABLE
        mock_ip_repo.get_by_ip_address.return_value = sample_ip

        with pytest.raises(ValidationError, match="无法释放"):
            ip_service.release_ip(request, released_by=1)

    def test_detect_ip_conflicts(self, ip_service, mock_ip_repo):
        """测试检测IP地址冲突"""
        # 模拟冲突的IP记录
        conflict_ips = [
            IPAddress(id=1, ip_address="192.168.1.100", subnet_id=1),
            IPAddress(id=2, ip_address="192.168.1.100", subnet_id=1)
        ]
        mock_ip_repo.check_ip_conflicts.return_value = conflict_ips

        # 创建模拟的IP响应对象
        from app.schemas.ip_address import IPAddressResponse
        mock_response = IPAddressResponse(
            id=1,
            ip_address="192.168.1.100",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            mac_address=None,
            hostname=None,
            device_type=None,
            location=None,
            assigned_to=None,
            description=None,
            allocated_at=None,
            allocated_by=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        with patch.object(ip_service, '_ip_to_response', return_value=mock_response):
            conflicts = ip_service.detect_ip_conflicts(subnet_id=1)

        assert len(conflicts) == 1
        assert conflicts[0].ip_address == "192.168.1.100"
        assert conflicts[0].conflict_count == 2

    def test_resolve_ip_conflicts(self, ip_service, mock_ip_repo):
        """测试解决IP地址冲突"""
        # 模拟冲突响应
        mock_conflicts = [
            Mock(conflicted_records=[Mock(ip_address="192.168.1.100")])
        ]
        mock_ip_repo.mark_conflicts.return_value = 2

        result = ip_service.resolve_ip_conflicts(mock_conflicts)

        assert result['resolved_conflicts'] == 1
        assert result['marked_ips'] == 2

    def test_get_ip_statistics(self, ip_service, mock_ip_repo):
        """测试获取IP统计信息"""
        mock_stats = {
            'total': 100,
            IPStatus.AVAILABLE: 70,
            IPStatus.ALLOCATED: 25,
            IPStatus.RESERVED: 3,
            IPStatus.CONFLICT: 2
        }
        mock_ip_repo.get_ip_statistics.return_value = mock_stats

        result = ip_service.get_ip_statistics(subnet_id=1)

        assert result.total == 100
        assert result.available == 70
        assert result.allocated == 25
        assert result.reserved == 3
        assert result.conflict == 2
        assert result.utilization_rate == 25.0

    def test_search_ips(self, ip_service, mock_ip_repo, sample_ip):
        """测试搜索IP地址"""
        request = IPSearchRequest(
            query="192.168.1",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            skip=0,
            limit=10
        )
        
        mock_ip_repo.search.return_value = [sample_ip]

        with patch.object(ip_service, '_ip_to_response') as mock_to_response:
            mock_to_response.return_value = Mock()
            results, total = ip_service.search_ips(request)

        assert len(results) == 1
        assert total >= 1
        mock_ip_repo.search.assert_called_once_with(
            query="192.168.1",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            skip=0,
            limit=10
        )

    def test_cleanup_unallocated_ips(self, ip_service, mock_ip_repo):
        """测试清理未分配的IP地址"""
        mock_ip_repo.delete_by_subnet.return_value = 5

        result = ip_service.cleanup_unallocated_ips(subnet_id=1)

        assert result == 5
        mock_ip_repo.delete_by_subnet.assert_called_once_with(1, IPStatus.AVAILABLE)

    def test_ip_to_response_conversion(self, ip_service, sample_ip):
        """测试IP模型到响应模型的转换"""
        result = ip_service._ip_to_response(sample_ip)

        assert result.id == sample_ip.id
        assert result.ip_address == sample_ip.ip_address
        assert result.subnet_id == sample_ip.subnet_id
        assert result.status == sample_ip.status