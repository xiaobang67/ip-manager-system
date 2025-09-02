"""
报告服务单元测试
"""
import pytest
import os
import json
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, mock_open
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks, HTTPException

from app.services.report_service import ReportService
from app.schemas.monitoring import ReportRequest, ReportFormat


class TestReportService:
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def temp_reports_dir(self):
        """创建临时报告目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @pytest.fixture
    def report_service(self, mock_db, temp_reports_dir):
        """创建报告服务实例"""
        service = ReportService(mock_db)
        service.reports_dir = temp_reports_dir
        return service
    
    @pytest.fixture
    def sample_report_request(self):
        """创建示例报告请求"""
        return ReportRequest(
            report_type="utilization",
            format=ReportFormat.PDF,
            subnet_ids=[1, 2],
            include_details=True
        )
    
    def test_ensure_reports_directory(self, mock_db):
        """测试确保报告目录存在"""
        with tempfile.TemporaryDirectory() as temp_dir:
            reports_dir = os.path.join(temp_dir, "test_reports")
            
            service = ReportService(mock_db)
            service.reports_dir = reports_dir
            service.ensure_reports_directory()
            
            assert os.path.exists(reports_dir)
    
    def test_generate_report(self, report_service, sample_report_request):
        """测试生成报告"""
        mock_background_tasks = Mock(spec=BackgroundTasks)
        
        result = report_service.generate_report(
            sample_report_request, 
            user_id=1, 
            background_tasks=mock_background_tasks
        )
        
        assert result.report_type == "utilization"
        assert result.format == "pdf"
        assert result.report_id is not None
        assert "/api/v1/monitoring/reports/" in result.file_url
        mock_background_tasks.add_task.assert_called_once()
    
    @patch('app.services.report_service.MonitoringService')
    def test_get_utilization_report_data(self, mock_monitoring_service, report_service, sample_report_request):
        """测试获取使用率报告数据"""
        # 模拟监控服务返回的数据
        mock_monitoring_instance = mock_monitoring_service.return_value
        mock_monitoring_instance.calculate_ip_utilization_stats.return_value = {
            'total_ips': 1000,
            'utilization_rate': 75.5
        }
        mock_monitoring_instance.calculate_subnet_utilization_stats.return_value = [
            {'subnet_id': 1, 'network': '192.168.1.0/24', 'utilization_rate': 80.0},
            {'subnet_id': 2, 'network': '192.168.2.0/24', 'utilization_rate': 60.0}
        ]
        mock_monitoring_instance.get_ip_allocation_trends.return_value = [
            {'date': '2023-01-01', 'allocations': 10},
            {'date': '2023-01-02', 'allocations': 15}
        ]
        
        result = report_service._get_utilization_report_data(
            mock_monitoring_instance, 
            sample_report_request
        )
        
        assert result['report_type'] == "IP地址使用率报告"
        assert 'summary' in result
        assert 'subnet_details' in result
        assert 'allocation_trends' in result
        assert len(result['subnet_details']) == 2  # 过滤后的网段数据
    
    def test_get_inventory_report_data(self, report_service, mock_db, sample_report_request):
        """测试获取清单报告数据"""
        # 模拟IP地址数据
        mock_ip1 = Mock()
        mock_ip1.ip_address = "192.168.1.100"
        mock_ip1.status.value = "allocated"
        mock_ip1.mac_address = "00:11:22:33:44:55"
        mock_ip1.hostname = "server1"
        mock_ip1.device_type = "server"
        mock_ip1.location = "datacenter"
        mock_ip1.assigned_to = "admin"
        mock_ip1.description = "Web server"
        mock_ip1.allocated_at = datetime.utcnow()
        mock_ip1.created_at = datetime.utcnow()
        mock_ip1.subnet.network = "192.168.1.0/24"
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_ip1]
        
        result = report_service._get_inventory_report_data(
            Mock(), 
            sample_report_request
        )
        
        assert result['report_type'] == "IP地址清单报告"
        assert result['total_count'] == 1
        assert len(result['ip_addresses']) == 1
        
        ip_data = result['ip_addresses'][0]
        assert ip_data['ip_address'] == "192.168.1.100"
        assert ip_data['status'] == "allocated"
        assert ip_data['hostname'] == "server1"
    
    @patch('app.services.report_service.MonitoringService')
    def test_get_subnet_planning_report_data(self, mock_monitoring_service, report_service, sample_report_request):
        """测试获取网段规划报告数据"""
        mock_monitoring_instance = mock_monitoring_service.return_value
        mock_monitoring_instance.calculate_subnet_utilization_stats.return_value = [
            {
                'subnet_id': 1,
                'network': '192.168.1.0/24',
                'utilization_rate': 85.0,
                'total_ips': 254,
                'allocated_ips': 200
            }
        ]
        
        result = report_service._get_subnet_planning_report_data(
            mock_monitoring_instance,
            sample_report_request
        )
        
        assert result['report_type'] == "网段规划报告"
        assert len(result['subnet_analysis']) == 1
        
        subnet_data = result['subnet_analysis'][0]
        assert 'planning_recommendation' in subnet_data
        assert subnet_data['utilization_rate'] == 85.0
    
    def test_get_subnet_planning_recommendation(self, report_service):
        """测试网段规划建议生成"""
        # 测试不同使用率的建议
        test_cases = [
            (95.0, "紧急：使用率过高，建议立即扩容或添加新网段"),
            (85.0, "警告：使用率较高，建议规划扩容"),
            (65.0, "注意：使用率中等，可考虑未来扩容计划"),
            (45.0, "正常：使用率适中，继续监控"),
            (25.0, "良好：使用率较低，资源充足")
        ]
        
        for utilization, expected_recommendation in test_cases:
            subnet_stats = {'utilization_rate': utilization}
            result = report_service._get_subnet_planning_recommendation(subnet_stats)
            assert result == expected_recommendation
    
    @patch('app.services.report_service.SimpleDocTemplate')
    @patch('app.services.report_service.Table')
    def test_generate_pdf_report(self, mock_table, mock_doc, report_service, sample_report_request):
        """测试生成PDF报告"""
        mock_doc_instance = Mock()
        mock_doc.return_value = mock_doc_instance
        
        test_data = {
            'report_type': 'IP地址使用率报告',
            'generated_at': datetime.utcnow().isoformat(),
            'summary': {
                'total_ips': 1000,
                'allocated_ips': 750,
                'utilization_rate': 75.0
            },
            'subnet_details': []
        }
        
        result = report_service._generate_pdf_report(
            "test_report_id",
            test_data,
            sample_report_request
        )
        
        assert result.endswith("test_report_id.pdf")
        mock_doc.assert_called_once()
        mock_doc_instance.build.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_csv_report(self, mock_file, report_service, sample_report_request):
        """测试生成CSV报告"""
        test_data = {
            'ip_addresses': [
                {
                    'ip_address': '192.168.1.100',
                    'subnet_network': '192.168.1.0/24',
                    'status': 'allocated',
                    'mac_address': '00:11:22:33:44:55',
                    'hostname': 'server1',
                    'device_type': 'server',
                    'location': 'datacenter',
                    'assigned_to': 'admin',
                    'description': 'Web server',
                    'allocated_at': '2023-01-01T10:00:00',
                    'created_at': '2023-01-01T09:00:00'
                }
            ]
        }
        
        # 修改请求类型为inventory以测试CSV生成
        inventory_request = ReportRequest(
            report_type="inventory",
            format=ReportFormat.CSV
        )
        
        result = report_service._generate_csv_report(
            "test_report_id",
            test_data,
            inventory_request
        )
        
        assert result.endswith("test_report_id.csv")
        mock_file.assert_called_once()
    
    @patch('pandas.ExcelWriter')
    @patch('pandas.DataFrame')
    def test_generate_excel_report(self, mock_dataframe, mock_excel_writer, report_service, sample_report_request):
        """测试生成Excel报告"""
        mock_writer_instance = Mock()
        mock_excel_writer.return_value.__enter__.return_value = mock_writer_instance
        
        mock_df_instance = Mock()
        mock_dataframe.return_value = mock_df_instance
        
        test_data = {
            'summary': {'total_ips': 1000},
            'subnet_details': [{'network': '192.168.1.0/24'}],
            'allocation_trends': [{'date': '2023-01-01', 'allocations': 10}]
        }
        
        result = report_service._generate_excel_report(
            "test_report_id",
            test_data,
            sample_report_request
        )
        
        assert result.endswith("test_report_id.xlsx")
        mock_excel_writer.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_generate_json_report(self, mock_json_dump, mock_file, report_service, sample_report_request):
        """测试生成JSON报告"""
        test_data = {'report_type': 'test', 'data': [1, 2, 3]}
        
        result = report_service._generate_json_report(
            "test_report_id",
            test_data,
            sample_report_request
        )
        
        assert result.endswith("test_report_id.json")
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once_with(
            test_data, 
            mock_file.return_value.__enter__.return_value,
            ensure_ascii=False,
            indent=2,
            default=str
        )
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_report_metadata(self, mock_json_dump, mock_file, report_service, sample_report_request):
        """测试保存报告元数据"""
        report_service._save_report_metadata(
            "test_report_id",
            sample_report_request,
            user_id=1,
            file_path="/path/to/report.pdf"
        )
        
        mock_file.assert_called_once()
        mock_json_dump.assert_called_once()
        
        # 检查传递给json.dump的数据结构
        call_args = mock_json_dump.call_args[0]
        metadata = call_args[0]
        
        assert metadata['report_id'] == "test_report_id"
        assert metadata['report_type'] == "utilization"
        assert metadata['format'] == "pdf"
        assert metadata['user_id'] == 1
        assert metadata['file_path'] == "/path/to/report.pdf"
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"report_id": "test", "file_path": "/test/path.pdf"}')
    @patch('os.path.exists')
    def test_get_report_status_exists(self, mock_exists, mock_file, report_service):
        """测试获取存在的报告状态"""
        mock_exists.side_effect = lambda path: True  # 元数据文件和报告文件都存在
        
        result = report_service.get_report_status("test_report_id")
        
        assert result['report_id'] == "test_report_id"
        assert result['status'] == "completed"
    
    @patch('os.path.exists')
    def test_get_report_status_not_found(self, mock_exists, report_service):
        """测试获取不存在的报告状态"""
        mock_exists.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            report_service.get_report_status("nonexistent_report_id")
        
        assert exc_info.value.status_code == 404
        assert "报告不存在" in str(exc_info.value.detail)
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"file_path": "/test/path.pdf", "expires_at": "2025-01-01T00:00:00"}')
    @patch('os.path.exists')
    @patch('app.services.report_service.FileResponse')
    def test_download_report_success(self, mock_file_response, mock_exists, mock_file, report_service):
        """测试成功下载报告"""
        mock_exists.side_effect = lambda path: True  # 所有文件都存在
        
        # 模拟未过期的报告
        future_date = datetime.utcnow() + timedelta(days=1)
        metadata_content = json.dumps({
            "file_path": "/test/path.pdf",
            "expires_at": future_date.isoformat()
        })
        mock_file.return_value.read.return_value = metadata_content
        
        with patch('builtins.open', mock_open(read_data=metadata_content)):
            result = report_service.download_report("test_report_id")
            
            mock_file_response.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists')
    def test_download_report_expired(self, mock_exists, mock_file, report_service):
        """测试下载过期的报告"""
        mock_exists.side_effect = lambda path: True
        
        # 模拟已过期的报告
        past_date = datetime.utcnow() - timedelta(days=1)
        metadata_content = json.dumps({
            "file_path": "/test/path.pdf",
            "expires_at": past_date.isoformat()
        })
        
        with patch('builtins.open', mock_open(read_data=metadata_content)):
            with pytest.raises(HTTPException) as exc_info:
                report_service.download_report("test_report_id")
            
            assert exc_info.value.status_code == 410
            assert "报告已过期" in str(exc_info.value.detail)


class TestReportServiceIntegration:
    """报告服务集成测试"""
    
    def test_full_report_generation_workflow(self):
        """测试完整的报告生成工作流程"""
        # 这里可以添加端到端的报告生成测试
        pass
    
    def test_concurrent_report_generation(self):
        """测试并发报告生成"""
        # 测试多个报告同时生成的情况
        pass
    
    def test_large_dataset_report_performance(self):
        """测试大数据集报告生成性能"""
        # 测试在大量数据情况下的报告生成性能
        pass