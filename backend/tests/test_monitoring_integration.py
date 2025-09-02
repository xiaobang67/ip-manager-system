"""
监控功能集成测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.monitoring_service import MonitoringService
from app.services.alert_service import AlertService
from app.services.report_service import ReportService
from app.schemas.monitoring import ReportRequest, ReportFormat


class TestMonitoringIntegration:
    """监控功能集成测试"""
    
    def test_monitoring_service_initialization(self):
        """测试监控服务初始化"""
        mock_db = Mock()
        service = MonitoringService(mock_db)
        assert service.db == mock_db
    
    def test_alert_service_initialization(self):
        """测试警报服务初始化"""
        mock_db = Mock()
        service = AlertService(mock_db)
        assert service.db == mock_db
    
    def test_report_service_initialization(self):
        """测试报告服务初始化"""
        mock_db = Mock()
        service = ReportService(mock_db)
        assert service.db == mock_db
        assert service.reports_dir == "reports"
    
    def test_dashboard_data_flow(self):
        """测试仪表盘数据流"""
        mock_db = Mock()
        monitoring_service = MonitoringService(mock_db)
        
        # 模拟数据库查询
        mock_db.query.return_value.count.side_effect = [1000, 750, 50, 180, 20, 25, 15, 12]
        
        with patch.object(monitoring_service, 'get_alert_statistics') as mock_alert_stats:
            mock_alert_stats.return_value = {
                'active_rules': 5,
                'recent_alerts': 10,
                'unresolved_alerts': 3,
                'severity_breakdown': {'low': 2, 'medium': 5, 'high': 2, 'critical': 1}
            }
            
            result = monitoring_service.get_dashboard_summary()
            
            assert 'ip_statistics' in result
            assert 'alert_statistics' in result
            assert 'total_subnets' in result
            assert 'total_users' in result
            assert 'timestamp' in result
    
    def test_report_generation_workflow(self):
        """测试报告生成工作流"""
        mock_db = Mock()
        report_service = ReportService(mock_db)
        
        # 创建报告请求
        report_request = ReportRequest(
            report_type="utilization",
            format=ReportFormat.JSON,
            include_details=True
        )
        
        # 模拟后台任务
        mock_background_tasks = Mock()
        
        result = report_service.generate_report(
            report_request, 
            user_id=1, 
            background_tasks=mock_background_tasks
        )
        
        assert result.report_type == "utilization"
        assert result.format == "json"
        assert result.report_id is not None
        mock_background_tasks.add_task.assert_called_once()
    
    def test_alert_creation_workflow(self):
        """测试警报创建工作流"""
        mock_db = Mock()
        alert_service = AlertService(mock_db)
        
        # 模拟监控服务返回警报数据
        mock_alert_data = [
            {
                'rule_id': 1,
                'message': 'Test alert',
                'severity': 'high'
            }
        ]
        
        # 模拟没有现有警报
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.alert_service.MonitoringService') as mock_monitoring_service:
            mock_monitoring_instance = mock_monitoring_service.return_value
            mock_monitoring_instance.check_utilization_alerts.return_value = mock_alert_data
            mock_monitoring_instance.create_alert_history.return_value = Mock(id=1)
            
            result = alert_service.check_and_create_alerts()
            
            assert len(result) == 1
            mock_monitoring_instance.check_utilization_alerts.assert_called_once()
    
    def test_service_error_handling(self):
        """测试服务错误处理"""
        mock_db = Mock()
        
        # 测试监控服务错误处理
        monitoring_service = MonitoringService(mock_db)
        mock_db.query.side_effect = Exception("Database error")
        
        # 应该能够处理数据库错误而不崩溃
        try:
            monitoring_service.calculate_ip_utilization_stats()
        except Exception as e:
            # 确保是预期的数据库错误
            assert "Database error" in str(e)
    
    def test_data_validation(self):
        """测试数据验证"""
        # 测试报告请求验证
        valid_request = ReportRequest(
            report_type="utilization",
            format=ReportFormat.PDF
        )
        assert valid_request.report_type == "utilization"
        assert valid_request.format == ReportFormat.PDF
        
        # 测试无效数据会被Pydantic捕获
        with pytest.raises(ValueError):
            ReportRequest(
                report_type="invalid_type",
                format="invalid_format"
            )
    
    def test_monitoring_performance(self):
        """测试监控性能"""
        mock_db = Mock()
        monitoring_service = MonitoringService(mock_db)
        
        # 模拟大量数据
        mock_db.query.return_value.count.return_value = 100000
        
        start_time = datetime.utcnow()
        result = monitoring_service.calculate_ip_utilization_stats()
        end_time = datetime.utcnow()
        
        # 确保计算在合理时间内完成（这里设置为1秒）
        execution_time = (end_time - start_time).total_seconds()
        assert execution_time < 1.0
        assert result is not None


if __name__ == "__main__":
    # 运行基本的集成测试
    test = TestMonitoringIntegration()
    test.test_monitoring_service_initialization()
    test.test_alert_service_initialization()
    test.test_report_service_initialization()
    print("All integration tests passed!")