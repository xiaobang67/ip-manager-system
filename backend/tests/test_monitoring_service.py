"""
监控服务单元测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.monitoring_service import MonitoringService
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.alert import AlertRule, AlertHistory, RuleType, AlertSeverity
from app.models.user import User


class TestMonitoringService:
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def monitoring_service(self, mock_db):
        """创建监控服务实例"""
        return MonitoringService(mock_db)
    
    @pytest.fixture
    def sample_ip_data(self):
        """创建示例IP地址数据"""
        return [
            Mock(status=IPStatus.ALLOCATED),
            Mock(status=IPStatus.ALLOCATED),
            Mock(status=IPStatus.RESERVED),
            Mock(status=IPStatus.AVAILABLE),
            Mock(status=IPStatus.AVAILABLE),
            Mock(status=IPStatus.CONFLICT)
        ]
    
    def test_calculate_ip_utilization_stats(self, monitoring_service, mock_db):
        """测试IP使用率统计计算"""
        # 模拟数据库查询结果
        mock_db.query.return_value.count.side_effect = [6, 2, 1, 2, 1]  # total, allocated, reserved, available, conflict
        
        result = monitoring_service.calculate_ip_utilization_stats()
        
        assert result['total_ips'] == 6
        assert result['allocated_ips'] == 2
        assert result['reserved_ips'] == 1
        assert result['available_ips'] == 2
        assert result['conflict_ips'] == 1
        assert result['utilization_rate'] == 50.0  # (2+1)/6 * 100
        assert result['allocation_rate'] == 33.33  # 2/6 * 100
        assert result['reservation_rate'] == 16.67  # 1/6 * 100
    
    def test_calculate_ip_utilization_stats_empty(self, monitoring_service, mock_db):
        """测试空数据库的IP使用率统计"""
        mock_db.query.return_value.count.return_value = 0
        
        result = monitoring_service.calculate_ip_utilization_stats()
        
        assert result['total_ips'] == 0
        assert result['utilization_rate'] == 0
        assert result['allocation_rate'] == 0
        assert result['reservation_rate'] == 0
    
    @patch('app.services.monitoring_service.ipaddress')
    def test_calculate_subnet_utilization_stats(self, mock_ipaddress, monitoring_service, mock_db):
        """测试网段使用率统计计算"""
        # 模拟网段数据
        mock_subnet = Mock()
        mock_subnet.id = 1
        mock_subnet.network = "192.168.1.0/24"
        mock_subnet.description = "Test Subnet"
        mock_subnet.vlan_id = 100
        mock_subnet.location = "Office"
        mock_subnet.created_at = datetime.utcnow()
        
        mock_db.query.return_value.all.return_value = [mock_subnet]
        
        # 模拟IP网络计算
        mock_network = Mock()
        mock_network.num_addresses = 256
        mock_ipaddress.ip_network.return_value = mock_network
        
        # 模拟IP统计查询
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (IPStatus.ALLOCATED, 50),
            (IPStatus.RESERVED, 10),
            (IPStatus.AVAILABLE, 190),
            (IPStatus.CONFLICT, 4)
        ]
        
        result = monitoring_service.calculate_subnet_utilization_stats()
        
        assert len(result) == 1
        subnet_stat = result[0]
        assert subnet_stat['subnet_id'] == 1
        assert subnet_stat['network'] == "192.168.1.0/24"
        assert subnet_stat['total_ips'] == 254  # 256 - 2 (network and broadcast)
        assert subnet_stat['allocated_ips'] == 50
        assert subnet_stat['reserved_ips'] == 10
        assert subnet_stat['utilization_rate'] == 23.62  # (50+10)/254 * 100
    
    def test_get_ip_allocation_trends(self, monitoring_service, mock_db):
        """测试IP分配趋势数据获取"""
        # 模拟数据库查询结果
        base_date = datetime.utcnow().date()
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (base_date - timedelta(days=2), 5),
            (base_date - timedelta(days=1), 3),
            (base_date, 7)
        ]
        
        result = monitoring_service.get_ip_allocation_trends(days=3)
        
        assert len(result) == 3
        assert all('date' in item and 'allocations' in item for item in result)
        
        # 检查日期是否连续
        dates = [item['date'] for item in result]
        assert len(set(dates)) == 3  # 确保没有重复日期
    
    def test_get_alert_statistics(self, monitoring_service, mock_db):
        """测试警报统计信息获取"""
        # 模拟查询结果
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 10, 3]  # active_rules, recent_alerts, unresolved_alerts
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            (AlertSeverity.LOW, 2),
            (AlertSeverity.MEDIUM, 5),
            (AlertSeverity.HIGH, 2),
            (AlertSeverity.CRITICAL, 1)
        ]
        
        result = monitoring_service.get_alert_statistics()
        
        assert result['active_rules'] == 5
        assert result['recent_alerts'] == 10
        assert result['unresolved_alerts'] == 3
        assert result['severity_breakdown']['low'] == 2
        assert result['severity_breakdown']['medium'] == 5
        assert result['severity_breakdown']['high'] == 2
        assert result['severity_breakdown']['critical'] == 1
    
    def test_get_dashboard_summary(self, monitoring_service, mock_db):
        """测试仪表盘汇总数据获取"""
        # 模拟各种查询结果
        mock_db.query.return_value.count.side_effect = [100, 5, 10, 2]  # total_ips, total_subnets, total_users, recent_allocations
        
        with patch.object(monitoring_service, 'calculate_ip_utilization_stats') as mock_ip_stats, \
             patch.object(monitoring_service, 'get_alert_statistics') as mock_alert_stats:
            
            mock_ip_stats.return_value = {'total_ips': 100, 'utilization_rate': 75.0}
            mock_alert_stats.return_value = {'active_rules': 5, 'unresolved_alerts': 3}
            
            result = monitoring_service.get_dashboard_summary()
            
            assert 'ip_statistics' in result
            assert 'alert_statistics' in result
            assert result['total_subnets'] == 5
            assert result['total_users'] == 10
            assert result['recent_allocations_24h'] == 2
            assert 'timestamp' in result
    
    def test_check_utilization_alerts_subnet_specific(self, monitoring_service, mock_db):
        """测试特定网段的使用率警报检查"""
        # 创建模拟警报规则
        mock_rule = Mock()
        mock_rule.id = 1
        mock_rule.name = "Test Subnet Alert"
        mock_rule.subnet_id = 1
        mock_rule.threshold_value = 80.0
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]
        
        # 模拟网段统计数据
        with patch.object(monitoring_service, 'calculate_subnet_utilization_stats') as mock_subnet_stats:
            mock_subnet_stats.return_value = [
                {
                    'subnet_id': 1,
                    'network': '192.168.1.0/24',
                    'utilization_rate': 85.0
                }
            ]
            
            result = monitoring_service.check_utilization_alerts()
            
            assert len(result) == 1
            alert = result[0]
            assert alert['rule_id'] == 1
            assert alert['subnet_id'] == 1
            assert alert['current_utilization'] == 85.0
            assert alert['threshold'] == 80.0
            assert alert['severity'] == AlertSeverity.MEDIUM
    
    def test_check_utilization_alerts_global(self, monitoring_service, mock_db):
        """测试全局使用率警报检查"""
        # 创建模拟全局警报规则
        mock_rule = Mock()
        mock_rule.id = 2
        mock_rule.name = "Global Alert"
        mock_rule.subnet_id = None
        mock_rule.threshold_value = 90.0
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_rule]
        
        # 模拟全局IP统计
        with patch.object(monitoring_service, 'calculate_ip_utilization_stats') as mock_ip_stats:
            mock_ip_stats.return_value = {'utilization_rate': 95.0}
            
            result = monitoring_service.check_utilization_alerts()
            
            assert len(result) == 1
            alert = result[0]
            assert alert['rule_id'] == 2
            assert alert['subnet_id'] is None
            assert alert['current_utilization'] == 95.0
            assert alert['severity'] == AlertSeverity.CRITICAL
    
    def test_create_alert_history(self, monitoring_service, mock_db):
        """测试创建警报历史记录"""
        alert_data = {
            'rule_id': 1,
            'message': 'Test alert message',
            'severity': AlertSeverity.HIGH
        }
        
        # 模拟数据库操作
        mock_alert_history = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.monitoring_service.AlertHistory', return_value=mock_alert_history):
            result = monitoring_service.create_alert_history(alert_data)
            
            assert result == mock_alert_history
            mock_db.add.assert_called_once_with(mock_alert_history)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_alert_history)


class TestMonitoringServiceIntegration:
    """监控服务集成测试"""
    
    def test_end_to_end_monitoring_flow(self):
        """测试端到端监控流程"""
        # 这里可以添加更复杂的集成测试
        # 涉及真实数据库操作和多个服务的交互
        pass
    
    def test_performance_with_large_dataset(self):
        """测试大数据集下的性能"""
        # 测试在大量IP地址和网段情况下的性能
        pass