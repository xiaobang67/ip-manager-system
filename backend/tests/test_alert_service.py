"""
警报服务单元测试
"""
import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.services.alert_service import AlertService
from app.models.alert import AlertRule, AlertHistory, RuleType, AlertSeverity
from app.models.subnet import Subnet
from app.schemas.monitoring import AlertRuleCreate, AlertRuleUpdate


class TestAlertService:
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def alert_service(self, mock_db):
        """创建警报服务实例"""
        return AlertService(mock_db)
    
    @pytest.fixture
    def sample_alert_rule_data(self):
        """创建示例警报规则数据"""
        return AlertRuleCreate(
            name="Test Alert Rule",
            rule_type="utilization",
            threshold_value=80.0,
            subnet_id=1,
            notification_emails='["test@example.com", "admin@example.com"]'
        )
    
    def test_get_alert_rules(self, alert_service, mock_db):
        """测试获取警报规则列表"""
        # 模拟数据库查询结果
        mock_rules = [
            Mock(id=1, name="Rule 1", is_active=True),
            Mock(id=2, name="Rule 2", is_active=False)
        ]
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = mock_rules
        
        result = alert_service.get_alert_rules(skip=0, limit=10, is_active=True)
        
        assert len(result) == 2
        mock_db.query.assert_called_with(AlertRule)
    
    def test_create_alert_rule_success(self, alert_service, mock_db, sample_alert_rule_data):
        """测试成功创建警报规则"""
        # 模拟网段存在
        mock_subnet = Mock(id=1, network="192.168.1.0/24")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_subnet
        
        # 模拟创建的警报规则
        mock_alert_rule = Mock()
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.alert_service.AlertRule', return_value=mock_alert_rule):
            result = alert_service.create_alert_rule(sample_alert_rule_data, user_id=1)
            
            assert result == mock_alert_rule
            mock_db.add.assert_called_once_with(mock_alert_rule)
            mock_db.commit.assert_called_once()
    
    def test_create_alert_rule_invalid_type(self, alert_service, mock_db):
        """测试创建无效类型的警报规则"""
        invalid_data = AlertRuleCreate(
            name="Invalid Rule",
            rule_type="invalid_type",
            threshold_value=80.0
        )
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.create_alert_rule(invalid_data, user_id=1)
        
        assert exc_info.value.status_code == 400
        assert "无效的规则类型" in str(exc_info.value.detail)
    
    def test_create_alert_rule_subnet_not_found(self, alert_service, mock_db, sample_alert_rule_data):
        """测试创建警报规则时网段不存在"""
        # 模拟网段不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.create_alert_rule(sample_alert_rule_data, user_id=1)
        
        assert exc_info.value.status_code == 404
        assert "指定的网段不存在" in str(exc_info.value.detail)
    
    def test_create_alert_rule_invalid_emails(self, alert_service, mock_db):
        """测试创建警报规则时邮箱格式无效"""
        invalid_email_data = AlertRuleCreate(
            name="Test Rule",
            rule_type="utilization",
            threshold_value=80.0,
            notification_emails="invalid_json"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.create_alert_rule(invalid_email_data, user_id=1)
        
        assert exc_info.value.status_code == 400
        assert "邮箱列表格式错误" in str(exc_info.value.detail)
    
    def test_update_alert_rule_success(self, alert_service, mock_db):
        """测试成功更新警报规则"""
        # 模拟现有规则
        mock_rule = Mock()
        mock_rule.id = 1
        mock_rule.name = "Old Name"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule
        
        update_data = AlertRuleUpdate(
            name="New Name",
            threshold_value=90.0,
            is_active=False
        )
        
        result = alert_service.update_alert_rule(1, update_data)
        
        assert result == mock_rule
        assert mock_rule.name == "New Name"
        assert mock_rule.threshold_value == 90.0
        assert mock_rule.is_active == False
        mock_db.commit.assert_called_once()
    
    def test_update_alert_rule_not_found(self, alert_service, mock_db):
        """测试更新不存在的警报规则"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        update_data = AlertRuleUpdate(name="New Name")
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.update_alert_rule(999, update_data)
        
        assert exc_info.value.status_code == 404
        assert "警报规则不存在" in str(exc_info.value.detail)
    
    def test_delete_alert_rule_success(self, alert_service, mock_db):
        """测试成功删除警报规则"""
        mock_rule = Mock(id=1, name="Test Rule")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_rule
        
        result = alert_service.delete_alert_rule(1)
        
        assert result == True
        mock_db.delete.assert_called_once_with(mock_rule)
        mock_db.commit.assert_called_once()
    
    def test_delete_alert_rule_not_found(self, alert_service, mock_db):
        """测试删除不存在的警报规则"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.delete_alert_rule(999)
        
        assert exc_info.value.status_code == 404
        assert "警报规则不存在" in str(exc_info.value.detail)
    
    def test_get_alert_history(self, alert_service, mock_db):
        """测试获取警报历史记录"""
        mock_alerts = [
            Mock(id=1, severity=AlertSeverity.HIGH, is_resolved=False),
            Mock(id=2, severity=AlertSeverity.MEDIUM, is_resolved=True)
        ]
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_alerts
        
        result = alert_service.get_alert_history(
            skip=0, 
            limit=10, 
            is_resolved=False, 
            severity="high"
        )
        
        assert len(result) == 2
        mock_db.query.assert_called_with(AlertHistory)
    
    def test_get_alert_history_invalid_severity(self, alert_service, mock_db):
        """测试获取警报历史时使用无效严重程度"""
        with pytest.raises(HTTPException) as exc_info:
            alert_service.get_alert_history(severity="invalid_severity")
        
        assert exc_info.value.status_code == 400
        assert "无效的严重程度" in str(exc_info.value.detail)
    
    def test_resolve_alert_success(self, alert_service, mock_db):
        """测试成功解决警报"""
        mock_alert = Mock()
        mock_alert.id = 1
        mock_alert.is_resolved = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        
        result = alert_service.resolve_alert(1, user_id=1)
        
        assert result == mock_alert
        assert mock_alert.is_resolved == True
        assert mock_alert.resolved_by == 1
        assert isinstance(mock_alert.resolved_at, datetime)
        mock_db.commit.assert_called_once()
    
    def test_resolve_alert_not_found(self, alert_service, mock_db):
        """测试解决不存在的警报"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.resolve_alert(999, user_id=1)
        
        assert exc_info.value.status_code == 404
        assert "警报记录不存在" in str(exc_info.value.detail)
    
    def test_resolve_alert_already_resolved(self, alert_service, mock_db):
        """测试解决已经解决的警报"""
        mock_alert = Mock()
        mock_alert.is_resolved = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_alert
        
        with pytest.raises(HTTPException) as exc_info:
            alert_service.resolve_alert(1, user_id=1)
        
        assert exc_info.value.status_code == 400
        assert "警报已经被解决" in str(exc_info.value.detail)
    
    def test_check_and_create_alerts(self, alert_service, mock_db):
        """测试检查并创建警报"""
        # 模拟监控服务返回的警报数据
        mock_alert_data = [
            {
                'rule_id': 1,
                'message': 'High utilization detected',
                'severity': AlertSeverity.HIGH
            }
        ]
        
        # 模拟没有现有的未解决警报
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.alert_service.MonitoringService') as mock_monitoring_service:
            mock_monitoring_instance = mock_monitoring_service.return_value
            mock_monitoring_instance.check_utilization_alerts.return_value = mock_alert_data
            mock_monitoring_instance.create_alert_history.return_value = Mock(id=1)
            
            result = alert_service.check_and_create_alerts()
            
            assert len(result) == 1
            mock_monitoring_instance.check_utilization_alerts.assert_called_once()
            mock_monitoring_instance.create_alert_history.assert_called_once_with(mock_alert_data[0])
    
    def test_check_and_create_alerts_duplicate_prevention(self, alert_service, mock_db):
        """测试防止创建重复警报"""
        mock_alert_data = [
            {
                'rule_id': 1,
                'message': 'High utilization detected',
                'severity': AlertSeverity.HIGH
            }
        ]
        
        # 模拟已存在相同的未解决警报
        mock_existing_alert = Mock(id=1, rule_id=1, is_resolved=False)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_alert
        
        with patch('app.services.alert_service.MonitoringService') as mock_monitoring_service:
            mock_monitoring_instance = mock_monitoring_service.return_value
            mock_monitoring_instance.check_utilization_alerts.return_value = mock_alert_data
            
            result = alert_service.check_and_create_alerts()
            
            # 应该没有创建新的警报
            assert len(result) == 0
            mock_monitoring_instance.create_alert_history.assert_not_called()
    
    def test_get_active_alerts(self, alert_service, mock_db):
        """测试获取活跃警报"""
        mock_alerts = [
            Mock(id=1, is_resolved=False),
            Mock(id=2, is_resolved=False)
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_alerts
        
        result = alert_service.get_active_alerts()
        
        assert len(result) == 2
        assert all(not alert.is_resolved for alert in result)
    
    def test_get_alert_summary_by_severity(self, alert_service, mock_db):
        """测试按严重程度获取警报汇总"""
        mock_severity_counts = [
            (AlertSeverity.LOW, 2),
            (AlertSeverity.MEDIUM, 5),
            (AlertSeverity.HIGH, 3),
            (AlertSeverity.CRITICAL, 1)
        ]
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = mock_severity_counts
        
        result = alert_service.get_alert_summary_by_severity()
        
        assert result['low'] == 2
        assert result['medium'] == 5
        assert result['high'] == 3
        assert result['critical'] == 1


class TestAlertServiceValidation:
    """警报服务验证测试"""
    
    def test_email_validation_valid_json(self):
        """测试有效的邮箱JSON格式验证"""
        valid_emails = '["test@example.com", "admin@example.com"]'
        emails = json.loads(valid_emails)
        assert isinstance(emails, list)
        assert len(emails) == 2
    
    def test_email_validation_invalid_json(self):
        """测试无效的邮箱JSON格式验证"""
        invalid_emails = "not_json_format"
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_emails)
    
    def test_email_validation_not_list(self):
        """测试邮箱不是列表格式的验证"""
        not_list_emails = '{"email": "test@example.com"}'
        emails = json.loads(not_list_emails)
        assert not isinstance(emails, list)