"""
监控API端点测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.models.user import User, UserRole
from app.schemas.monitoring import ReportRequest, ReportFormat


class TestMonitoringEndpoints:
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.role = UserRole.ADMIN
        user.is_active = True
        return user
    
    @pytest.fixture
    def auth_headers(self):
        """创建认证头"""
        # 这里应该使用真实的JWT token生成逻辑
        return {"Authorization": "Bearer test_token"}
    
    def test_get_dashboard_summary_success(self, client, auth_headers):
        """测试获取仪表盘汇总数据成功"""
        mock_dashboard_data = {
            "ip_statistics": {
                "total_ips": 1000,
                "allocated_ips": 750,
                "utilization_rate": 75.0
            },
            "alert_statistics": {
                "active_rules": 5,
                "unresolved_alerts": 3
            },
            "total_subnets": 25,
            "total_users": 15,
            "recent_allocations_24h": 12,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch('app.api.v1.endpoints.monitoring.MonitoringService') as mock_service:
            mock_service.return_value.get_dashboard_summary.return_value = mock_dashboard_data
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get("/api/v1/monitoring/dashboard", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["ip_statistics"]["total_ips"] == 1000
        assert data["total_subnets"] == 25
    
    def test_get_dashboard_summary_unauthorized(self, client):
        """测试未授权访问仪表盘数据"""
        response = client.get("/api/v1/monitoring/dashboard")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_ip_utilization_stats_success(self, client, auth_headers):
        """测试获取IP使用率统计成功"""
        mock_stats = {
            "total_ips": 1000,
            "allocated_ips": 750,
            "reserved_ips": 50,
            "available_ips": 180,
            "conflict_ips": 20,
            "utilization_rate": 80.0,
            "allocation_rate": 75.0,
            "reservation_rate": 5.0
        }
        
        with patch('app.api.v1.endpoints.monitoring.MonitoringService') as mock_service:
            mock_service.return_value.calculate_ip_utilization_stats.return_value = mock_stats
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get("/api/v1/monitoring/ip-utilization", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_ips"] == 1000
        assert data["utilization_rate"] == 80.0
    
    def test_get_subnet_utilization_stats_success(self, client, auth_headers):
        """测试获取网段使用率统计成功"""
        mock_subnet_stats = [
            {
                "subnet_id": 1,
                "network": "192.168.1.0/24",
                "description": "Main Office",
                "total_ips": 254,
                "allocated_ips": 200,
                "utilization_rate": 78.74,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        with patch('app.api.v1.endpoints.monitoring.MonitoringService') as mock_service:
            mock_service.return_value.calculate_subnet_utilization_stats.return_value = mock_subnet_stats
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get("/api/v1/monitoring/subnet-utilization", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["network"] == "192.168.1.0/24"
    
    def test_get_allocation_trends_success(self, client, auth_headers):
        """测试获取分配趋势成功"""
        mock_trends = [
            {"date": "2023-01-01", "allocations": 10},
            {"date": "2023-01-02", "allocations": 15},
            {"date": "2023-01-03", "allocations": 8}
        ]
        
        with patch('app.api.v1.endpoints.monitoring.MonitoringService') as mock_service:
            mock_service.return_value.get_ip_allocation_trends.return_value = mock_trends
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get("/api/v1/monitoring/allocation-trends?days=30", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert data[0]["date"] == "2023-01-01"
    
    def test_get_allocation_trends_invalid_days(self, client, auth_headers):
        """测试获取分配趋势时使用无效天数"""
        with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
            response = client.get("/api/v1/monitoring/allocation-trends?days=400", headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_top_utilized_subnets_success(self, client, auth_headers):
        """测试获取使用率最高网段成功"""
        mock_subnets = [
            {
                "subnet_id": 1,
                "network": "192.168.1.0/24",
                "utilization_rate": 85.0
            },
            {
                "subnet_id": 2,
                "network": "192.168.2.0/24",
                "utilization_rate": 70.0
            }
        ]
        
        with patch('app.api.v1.endpoints.monitoring.MonitoringService') as mock_service:
            mock_service.return_value.get_top_utilized_subnets.return_value = mock_subnets
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get("/api/v1/monitoring/top-utilized-subnets?limit=10", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["utilization_rate"] == 85.0
    
    def test_get_alert_statistics_success(self, client, auth_headers):
        """测试获取警报统计成功"""
        mock_alert_stats = {
            "active_rules": 5,
            "recent_alerts": 10,
            "unresolved_alerts": 3,
            "severity_breakdown": {
                "low": 2,
                "medium": 5,
                "high": 2,
                "critical": 1
            }
        }
        
        with patch('app.api.v1.endpoints.monitoring.MonitoringService') as mock_service:
            mock_service.return_value.get_alert_statistics.return_value = mock_alert_stats
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get("/api/v1/monitoring/alerts/statistics", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["active_rules"] == 5
        assert data["unresolved_alerts"] == 3
    
    def test_create_alert_rule_success(self, client, auth_headers, mock_user):
        """测试创建警报规则成功"""
        rule_data = {
            "name": "High Utilization Alert",
            "rule_type": "utilization",
            "threshold_value": 80.0,
            "subnet_id": 1,
            "notification_emails": '["admin@example.com"]'
        }
        
        mock_created_rule = Mock()
        mock_created_rule.id = 1
        mock_created_rule.name = rule_data["name"]
        mock_created_rule.rule_type = rule_data["rule_type"]
        mock_created_rule.threshold_value = rule_data["threshold_value"]
        mock_created_rule.created_at = datetime.utcnow()
        
        with patch('app.api.v1.endpoints.monitoring.AlertService') as mock_service:
            mock_service.return_value.create_alert_rule.return_value = mock_created_rule
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=mock_user):
                response = client.post(
                    "/api/v1/monitoring/alerts/rules",
                    json=rule_data,
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == rule_data["name"]
    
    def test_create_alert_rule_invalid_data(self, client, auth_headers):
        """测试创建警报规则时数据无效"""
        invalid_rule_data = {
            "name": "",  # 空名称
            "rule_type": "invalid_type",  # 无效类型
            "threshold_value": -10  # 无效阈值
        }
        
        with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
            response = client.post(
                "/api/v1/monitoring/alerts/rules",
                json=invalid_rule_data,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_update_alert_rule_success(self, client, auth_headers):
        """测试更新警报规则成功"""
        rule_id = 1
        update_data = {
            "name": "Updated Alert Rule",
            "threshold_value": 90.0,
            "is_active": False
        }
        
        mock_updated_rule = Mock()
        mock_updated_rule.id = rule_id
        mock_updated_rule.name = update_data["name"]
        mock_updated_rule.threshold_value = update_data["threshold_value"]
        mock_updated_rule.is_active = update_data["is_active"]
        
        with patch('app.api.v1.endpoints.monitoring.AlertService') as mock_service:
            mock_service.return_value.update_alert_rule.return_value = mock_updated_rule
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.put(
                    f"/api/v1/monitoring/alerts/rules/{rule_id}",
                    json=update_data,
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == update_data["name"]
    
    def test_delete_alert_rule_success(self, client, auth_headers):
        """测试删除警报规则成功"""
        rule_id = 1
        
        with patch('app.api.v1.endpoints.monitoring.AlertService') as mock_service:
            mock_service.return_value.delete_alert_rule.return_value = True
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.delete(
                    f"/api/v1/monitoring/alerts/rules/{rule_id}",
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "警报规则已删除"
    
    def test_resolve_alert_success(self, client, auth_headers, mock_user):
        """测试解决警报成功"""
        alert_id = 1
        
        mock_resolved_alert = Mock()
        mock_resolved_alert.id = alert_id
        mock_resolved_alert.is_resolved = True
        mock_resolved_alert.resolved_by = mock_user.id
        
        with patch('app.api.v1.endpoints.monitoring.AlertService') as mock_service:
            mock_service.return_value.resolve_alert.return_value = mock_resolved_alert
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=mock_user):
                response = client.put(
                    f"/api/v1/monitoring/alerts/history/{alert_id}/resolve",
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "警报已解决"
    
    def test_generate_report_success(self, client, auth_headers, mock_user):
        """测试生成报告成功"""
        report_request = {
            "report_type": "utilization",
            "format": "pdf",
            "subnet_ids": [1, 2],
            "include_details": True
        }
        
        mock_report_response = {
            "report_id": "test-report-123",
            "report_type": "utilization",
            "format": "pdf",
            "file_url": "/api/v1/monitoring/reports/test-report-123/download",
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        with patch('app.api.v1.endpoints.monitoring.ReportService') as mock_service:
            mock_service.return_value.generate_report.return_value = mock_report_response
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=mock_user):
                response = client.post(
                    "/api/v1/monitoring/reports/generate",
                    json=report_request,
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["report_id"] == "test-report-123"
        assert data["report_type"] == "utilization"
    
    def test_generate_report_invalid_type(self, client, auth_headers):
        """测试生成报告时类型无效"""
        invalid_request = {
            "report_type": "invalid_type",
            "format": "pdf"
        }
        
        with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
            response = client.post(
                "/api/v1/monitoring/reports/generate",
                json=invalid_request,
                headers=auth_headers
            )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_get_report_status_success(self, client, auth_headers):
        """测试获取报告状态成功"""
        report_id = "test-report-123"
        
        mock_status = {
            "report_id": report_id,
            "status": "completed",
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "download_url": f"/api/v1/monitoring/reports/{report_id}/download"
        }
        
        with patch('app.api.v1.endpoints.monitoring.ReportService') as mock_service:
            mock_service.return_value.get_report_status.return_value = mock_status
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get(
                    f"/api/v1/monitoring/reports/{report_id}",
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["report_id"] == report_id
        assert data["status"] == "completed"
    
    def test_download_report_success(self, client, auth_headers):
        """测试下载报告成功"""
        report_id = "test-report-123"
        
        mock_file_response = Mock()
        mock_file_response.status_code = 200
        mock_file_response.headers = {"content-type": "application/pdf"}
        
        with patch('app.api.v1.endpoints.monitoring.ReportService') as mock_service:
            mock_service.return_value.download_report.return_value = mock_file_response
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.get(
                    f"/api/v1/monitoring/reports/{report_id}/download",
                    headers=auth_headers
                )
        
        # 注意：这里的断言可能需要根据实际的FileResponse实现调整
        assert response.status_code == status.HTTP_200_OK
    
    def test_check_alerts_success(self, client, auth_headers):
        """测试手动触发警报检查成功"""
        with patch('app.api.v1.endpoints.monitoring.AlertService') as mock_service:
            mock_service.return_value.check_and_create_alerts.return_value = []
            
            with patch('app.api.v1.endpoints.monitoring.get_current_user', return_value=Mock()):
                response = client.post(
                    "/api/v1/monitoring/alerts/check",
                    headers=auth_headers
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "警报检查已启动"


class TestMonitoringEndpointsIntegration:
    """监控API端点集成测试"""
    
    def test_full_monitoring_workflow(self):
        """测试完整的监控工作流程"""
        # 这里可以添加端到端的监控流程测试
        # 包括创建警报规则、触发警报、生成报告等
        pass
    
    def test_concurrent_report_generation(self):
        """测试并发报告生成"""
        # 测试多个用户同时生成报告的情况
        pass