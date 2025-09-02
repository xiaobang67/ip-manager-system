import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.ip_lifecycle_service import IPLifecycleService
from app.repositories.ip_repository import IPRepository
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.core.exceptions import NotFoundError
from datetime import datetime, timedelta


class TestIPLifecycleService:
    """IP生命周期服务单元测试"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def mock_ip_repo(self):
        return Mock(spec=IPRepository)

    @pytest.fixture
    def lifecycle_service(self, mock_db, mock_ip_repo):
        service = IPLifecycleService(mock_db)
        service.ip_repo = mock_ip_repo
        return service

    @pytest.fixture
    def sample_ip_available(self):
        return IPAddress(
            id=1,
            ip_address="192.168.1.100",
            subnet_id=1,
            status=IPStatus.AVAILABLE,
            created_at=datetime.utcnow() - timedelta(days=10),
            updated_at=datetime.utcnow() - timedelta(days=1)
        )

    @pytest.fixture
    def sample_ip_allocated(self):
        return IPAddress(
            id=2,
            ip_address="192.168.1.101",
            subnet_id=1,
            status=IPStatus.ALLOCATED,
            allocated_at=datetime.utcnow() - timedelta(days=5),
            allocated_by=1,
            assigned_to="测试用户",
            created_at=datetime.utcnow() - timedelta(days=10),
            updated_at=datetime.utcnow() - timedelta(days=5)
        )

    @pytest.fixture
    def sample_ip_long_term(self):
        return IPAddress(
            id=3,
            ip_address="192.168.1.102",
            subnet_id=1,
            status=IPStatus.ALLOCATED,
            allocated_at=datetime.utcnow() - timedelta(days=100),
            allocated_by=1,
            assigned_to="长期用户",
            created_at=datetime.utcnow() - timedelta(days=110),
            updated_at=datetime.utcnow() - timedelta(days=100)
        )

    @pytest.fixture
    def sample_subnet(self):
        return Subnet(
            id=1,
            network="192.168.1.0/24",
            netmask="255.255.255.0",
            description="测试网段"
        )

    def test_track_ip_lifecycle_available(self, lifecycle_service, mock_ip_repo, sample_ip_available):
        """测试跟踪可用IP的生命周期"""
        mock_ip_repo.get_by_id.return_value = sample_ip_available

        result = lifecycle_service.track_ip_lifecycle(1)

        assert result['ip_address'] == "192.168.1.100"
        assert result['current_status'] == IPStatus.AVAILABLE
        assert result['lifecycle_stage'] == 'available'
        assert result['usage_duration'] is None
        assert 'next_actions' in result
        assert "可以分配给新设备" in result['next_actions']

    def test_track_ip_lifecycle_newly_allocated(self, lifecycle_service, mock_ip_repo, sample_ip_allocated):
        """测试跟踪新分配IP的生命周期"""
        mock_ip_repo.get_by_id.return_value = sample_ip_allocated

        result = lifecycle_service.track_ip_lifecycle(2)

        assert result['ip_address'] == "192.168.1.101"
        assert result['current_status'] == IPStatus.ALLOCATED
        assert result['lifecycle_stage'] == 'newly_allocated'
        assert result['usage_duration'] == 5
        assert result['allocated_at'] == sample_ip_allocated.allocated_at
        assert result['allocated_by'] == 1

    def test_track_ip_lifecycle_long_term(self, lifecycle_service, mock_ip_repo, sample_ip_long_term):
        """测试跟踪长期分配IP的生命周期"""
        mock_ip_repo.get_by_id.return_value = sample_ip_long_term

        result = lifecycle_service.track_ip_lifecycle(3)

        assert result['lifecycle_stage'] == 'long_term'
        assert result['usage_duration'] == 100
        assert any("检查是否仍在使用" in action for action in result['next_actions'])

    def test_track_ip_lifecycle_not_found(self, lifecycle_service, mock_ip_repo):
        """测试跟踪不存在的IP"""
        mock_ip_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError, match="IP地址记录不存在"):
            lifecycle_service.track_ip_lifecycle(999)

    def test_get_ip_lifecycle_history(self, lifecycle_service, mock_ip_repo, sample_ip_allocated):
        """测试获取IP生命周期历史"""
        mock_ip_repo.get_by_ip_address.return_value = sample_ip_allocated

        result = lifecycle_service.get_ip_lifecycle_history("192.168.1.101")

        assert len(result) == 2  # 创建和分配两个事件
        assert result[0]['action'] == 'CREATED'
        assert result[1]['action'] == 'ALLOCATED'
        assert result[1]['user_id'] == 1
        assert "分配给: 测试用户" in result[1]['details']

    def test_get_ip_lifecycle_history_not_found(self, lifecycle_service, mock_ip_repo):
        """测试获取不存在IP的历史"""
        mock_ip_repo.get_by_ip_address.return_value = None

        with pytest.raises(NotFoundError, match="IP地址不存在"):
            lifecycle_service.get_ip_lifecycle_history("192.168.1.999")

    def test_manage_ip_expiration(self, lifecycle_service, mock_db):
        """测试管理IP地址过期"""
        # 模拟长期分配的IP
        long_allocated = [
            IPAddress(ip_address="192.168.1.100", status=IPStatus.ALLOCATED),
            IPAddress(ip_address="192.168.1.101", status=IPStatus.ALLOCATED)
        ]
        
        # 模拟长期保留的IP
        long_reserved = [
            IPAddress(ip_address="192.168.1.200", status=IPStatus.RESERVED)
        ]

        # 模拟数据库查询
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = [long_allocated, long_reserved]

        result = lifecycle_service.manage_ip_expiration(days_threshold=30)

        assert len(result['long_term_allocated']) == 2
        assert len(result['long_term_reserved']) == 1
        assert len(result['suggestions']) == 2
        assert "长期分配" in result['suggestions'][0]
        assert "长期保留" in result['suggestions'][1]

    def test_auto_cleanup_expired_reservations(self, lifecycle_service, mock_db):
        """测试自动清理过期保留"""
        # 模拟过期保留的IP
        expired_reserved = [
            IPAddress(
                ip_address="192.168.1.100",
                status=IPStatus.RESERVED,
                allocated_at=datetime.utcnow() - timedelta(days=100)
            ),
            IPAddress(
                ip_address="192.168.1.101",
                status=IPStatus.RESERVED,
                allocated_at=datetime.utcnow() - timedelta(days=120)
            )
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = expired_reserved

        result = lifecycle_service.auto_cleanup_expired_reservations(days_threshold=90)

        assert result['cleaned_count'] == 2
        assert result['threshold_days'] == 90
        
        # 验证IP状态被更新
        for ip in expired_reserved:
            assert ip.status == IPStatus.AVAILABLE
            assert ip.allocated_at is None
            assert ip.allocated_by is None
            assert ip.assigned_to is None
            assert "自动清理过期保留" in ip.description

        mock_db.commit.assert_called_once()

    def test_validate_ip_state_transition_valid(self, lifecycle_service, mock_ip_repo, sample_ip_available):
        """测试有效的IP状态转换"""
        mock_ip_repo.get_by_ip_address.return_value = sample_ip_available

        # 从AVAILABLE到ALLOCATED是有效的
        result = lifecycle_service.validate_ip_state_transition("192.168.1.100", IPStatus.ALLOCATED)
        assert result is True

        # 从AVAILABLE到RESERVED是有效的
        result = lifecycle_service.validate_ip_state_transition("192.168.1.100", IPStatus.RESERVED)
        assert result is True

    def test_validate_ip_state_transition_invalid(self, lifecycle_service, mock_ip_repo, sample_ip_allocated):
        """测试无效的IP状态转换"""
        mock_ip_repo.get_by_ip_address.return_value = sample_ip_allocated

        # 从ALLOCATED到CONFLICT通常不是直接的转换
        result = lifecycle_service.validate_ip_state_transition("192.168.1.101", IPStatus.CONFLICT)
        assert result is False

    def test_validate_ip_state_transition_not_found(self, lifecycle_service, mock_ip_repo):
        """测试验证不存在IP的状态转换"""
        mock_ip_repo.get_by_ip_address.return_value = None

        with pytest.raises(NotFoundError, match="IP地址不存在"):
            lifecycle_service.validate_ip_state_transition("192.168.1.999", IPStatus.ALLOCATED)

    def test_get_subnet_lifecycle_summary(self, lifecycle_service, mock_db, mock_ip_repo, sample_subnet):
        """测试获取网段生命周期摘要"""
        # 模拟网段查询
        mock_query_subnet = Mock()
        mock_db.query.return_value = mock_query_subnet
        mock_query_subnet.filter.return_value.first.return_value = sample_subnet

        # 模拟IP统计
        mock_stats = {
            'total': 100,
            IPStatus.AVAILABLE: 70,
            IPStatus.ALLOCATED: 25,
            IPStatus.RESERVED: 3,
            IPStatus.CONFLICT: 2
        }
        mock_ip_repo.get_ip_statistics.return_value = mock_stats

        # 模拟最近分配的IP
        recent_ips = [
            IPAddress(
                ip_address="192.168.1.100",
                allocated_at=datetime.utcnow() - timedelta(days=1),
                assigned_to="用户1"
            )
        ]
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = recent_ips
        mock_query.count.return_value = 5  # 长期分配的数量

        result = lifecycle_service.get_subnet_lifecycle_summary(1)

        assert result['subnet_id'] == 1
        assert result['network'] == "192.168.1.0/24"
        assert result['total_ips'] == 100
        assert result['utilization_rate'] == 25.0
        assert result['status_distribution'] == mock_stats
        assert len(result['recent_allocations']) == 1
        assert result['long_term_allocated_count'] == 5
        assert 'health_score' in result
        assert 0 <= result['health_score'] <= 100

    def test_get_subnet_lifecycle_summary_not_found(self, lifecycle_service, mock_db):
        """测试获取不存在网段的生命周期摘要"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(NotFoundError, match="网段不存在"):
            lifecycle_service.get_subnet_lifecycle_summary(999)

    def test_detect_ip_usage_patterns(self, lifecycle_service, mock_db):
        """测试检测IP使用模式"""
        # 模拟IP记录
        all_ips = [
            IPAddress(
                ip_address="192.168.1.100",
                status=IPStatus.ALLOCATED,
                allocated_at=datetime.utcnow() - timedelta(days=50),
                assigned_to="稳定用户"
            ),
            IPAddress(
                ip_address="192.168.1.101",
                status=IPStatus.AVAILABLE
            )
        ]

        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = all_ips

        result = lifecycle_service.detect_ip_usage_patterns(subnet_id=1)

        assert 'stable_allocations' in result
        assert 'unused_ranges' in result
        assert 'allocation_trends' in result
        assert len(result['stable_allocations']) == 1
        assert result['stable_allocations'][0]['ip_address'] == "192.168.1.100"
        assert result['stable_allocations'][0]['duration_days'] == 50

    def test_calculate_subnet_health_score_perfect(self, lifecycle_service):
        """测试计算完美网段的健康评分"""
        stats = {
            'total': 100,
            IPStatus.AVAILABLE: 50,
            IPStatus.ALLOCATED: 50,
            IPStatus.RESERVED: 0,
            IPStatus.CONFLICT: 0
        }
        utilization_rate = 50.0

        score = lifecycle_service._calculate_subnet_health_score(stats, utilization_rate)
        assert score == 100

    def test_calculate_subnet_health_score_with_issues(self, lifecycle_service):
        """测试计算有问题网段的健康评分"""
        stats = {
            'total': 100,
            IPStatus.AVAILABLE: 5,
            IPStatus.ALLOCATED: 70,
            IPStatus.RESERVED: 20,
            IPStatus.CONFLICT: 5
        }
        utilization_rate = 95.0  # 过高的利用率

        score = lifecycle_service._calculate_subnet_health_score(stats, utilization_rate)
        assert score < 100  # 应该有扣分
        assert score >= 0   # 不应该是负数

    def test_determine_lifecycle_stage_available(self, lifecycle_service):
        """测试确定可用IP的生命周期阶段"""
        ip = IPAddress(status=IPStatus.AVAILABLE)
        stage = lifecycle_service._determine_lifecycle_stage(ip)
        assert stage == 'available'

    def test_determine_lifecycle_stage_conflict(self, lifecycle_service):
        """测试确定冲突IP的生命周期阶段"""
        ip = IPAddress(status=IPStatus.CONFLICT)
        stage = lifecycle_service._determine_lifecycle_stage(ip)
        assert stage == 'conflict'

    def test_determine_lifecycle_stage_newly_allocated(self, lifecycle_service):
        """测试确定新分配IP的生命周期阶段"""
        ip = IPAddress(
            status=IPStatus.ALLOCATED,
            allocated_at=datetime.utcnow() - timedelta(days=3)
        )
        stage = lifecycle_service._determine_lifecycle_stage(ip)
        assert stage == 'newly_allocated'

    def test_determine_lifecycle_stage_long_term(self, lifecycle_service):
        """测试确定长期分配IP的生命周期阶段"""
        ip = IPAddress(
            status=IPStatus.ALLOCATED,
            allocated_at=datetime.utcnow() - timedelta(days=100)
        )
        stage = lifecycle_service._determine_lifecycle_stage(ip)
        assert stage == 'long_term'

    def test_calculate_usage_duration_with_allocation(self, lifecycle_service):
        """测试计算有分配时间的IP使用时长"""
        ip = IPAddress(allocated_at=datetime.utcnow() - timedelta(days=15))
        duration = lifecycle_service._calculate_usage_duration(ip)
        assert duration == 15

    def test_calculate_usage_duration_without_allocation(self, lifecycle_service):
        """测试计算无分配时间的IP使用时长"""
        ip = IPAddress(allocated_at=None)
        duration = lifecycle_service._calculate_usage_duration(ip)
        assert duration is None

    def test_suggest_next_actions_conflict(self, lifecycle_service):
        """测试为冲突IP建议下一步操作"""
        ip = IPAddress(status=IPStatus.CONFLICT)
        suggestions = lifecycle_service._suggest_next_actions(ip)
        assert "解决IP地址冲突" in suggestions

    def test_suggest_next_actions_available(self, lifecycle_service):
        """测试为可用IP建议下一步操作"""
        ip = IPAddress(status=IPStatus.AVAILABLE)
        suggestions = lifecycle_service._suggest_next_actions(ip)
        assert "可以分配给新设备" in suggestions

    def test_suggest_next_actions_long_term_allocated(self, lifecycle_service):
        """测试为长期分配IP建议下一步操作"""
        ip = IPAddress(
            status=IPStatus.ALLOCATED,
            allocated_at=datetime.utcnow() - timedelta(days=100)
        )
        suggestions = lifecycle_service._suggest_next_actions(ip)
        assert any("检查是否仍在使用" in suggestion for suggestion in suggestions)