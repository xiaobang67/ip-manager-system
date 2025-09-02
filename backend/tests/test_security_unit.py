"""
安全功能单元测试
不依赖外部服务的安全功能测试
"""
import pytest
import time
from unittest.mock import patch, MagicMock

from app.core.validators import InputValidator, XSSProtection, rate_limiter
from app.core.security_middleware import CSRFProtection
from app.core.security_config import SecurityPolicies, SecurityConfig, ThreatDetection
from app.core.security_testing import SecurityTester, PasswordStrengthTester
from app.core.security_monitoring import SecurityEvent, SecurityEventType, SecurityLevel, SecurityMonitor


class TestInputValidation:
    """输入验证测试"""
    
    def test_ip_address_validation(self):
        """测试IP地址验证"""
        # 有效IP地址
        assert InputValidator.validate_ip_address("192.168.1.1") == True
        assert InputValidator.validate_ip_address("10.0.0.1") == True
        assert InputValidator.validate_ip_address("172.16.0.1") == True
        assert InputValidator.validate_ip_address("::1") == True
        
        # 无效IP地址
        assert InputValidator.validate_ip_address("256.256.256.256") == False
        assert InputValidator.validate_ip_address("192.168.1") == False
        assert InputValidator.validate_ip_address("not_an_ip") == False
        assert InputValidator.validate_ip_address("") == False
    
    def test_subnet_validation(self):
        """测试子网验证"""
        # 有效子网
        assert InputValidator.validate_subnet("192.168.1.0/24") == True
        assert InputValidator.validate_subnet("10.0.0.0/8") == True
        assert InputValidator.validate_subnet("172.16.0.0/12") == True
        
        # 无效子网
        assert InputValidator.validate_subnet("192.168.1.0/33") == False
        assert InputValidator.validate_subnet("256.256.256.0/24") == False
        assert InputValidator.validate_subnet("not_a_subnet") == False
    
    def test_mac_address_validation(self):
        """测试MAC地址验证"""
        # 有效MAC地址
        assert InputValidator.validate_mac_address("00:11:22:33:44:55") == True
        assert InputValidator.validate_mac_address("AA:BB:CC:DD:EE:FF") == True
        assert InputValidator.validate_mac_address("00-11-22-33-44-55") == True
        
        # 无效MAC地址
        assert InputValidator.validate_mac_address("00:11:22:33:44") == False
        assert InputValidator.validate_mac_address("GG:HH:II:JJ:KK:LL") == False
        assert InputValidator.validate_mac_address("not_a_mac") == False
    
    def test_hostname_validation(self):
        """测试主机名验证"""
        # 有效主机名
        assert InputValidator.validate_hostname("server1") == True
        assert InputValidator.validate_hostname("web-server.example.com") == True
        assert InputValidator.validate_hostname("host123") == True
        
        # 无效主机名
        assert InputValidator.validate_hostname("-invalid") == False
        assert InputValidator.validate_hostname("invalid-") == False
        assert InputValidator.validate_hostname("") == False
        assert InputValidator.validate_hostname("a" * 64) == False  # 标签过长
    
    def test_sql_injection_detection(self):
        """测试SQL注入检测"""
        # 安全输入
        assert InputValidator.validate_sql_safe_string("normal text") == True
        assert InputValidator.validate_sql_safe_string("server123") == True
        
        # SQL注入尝试
        assert InputValidator.validate_sql_safe_string("'; DROP TABLE users; --") == False
        assert InputValidator.validate_sql_safe_string("' OR '1'='1") == False
        assert InputValidator.validate_sql_safe_string("UNION SELECT * FROM users") == False
    
    def test_string_sanitization(self):
        """测试字符串清理"""
        # 测试HTML转义
        dirty_input = "<script>alert('xss')</script>"
        clean_output = InputValidator.sanitize_string(dirty_input)
        assert "<script>" not in clean_output
        assert "&lt;script&gt;" in clean_output
        
        # 测试长度限制
        long_input = "a" * 2000
        clean_output = InputValidator.sanitize_string(long_input, max_length=100)
        assert len(clean_output) <= 100


class TestXSSProtection:
    """XSS防护测试"""
    
    def test_string_sanitization(self):
        """测试字符串清理"""
        # 测试基本HTML转义
        dirty_string = "<script>alert('xss')</script>"
        clean_string = XSSProtection._sanitize_string(dirty_string)
        
        assert "&lt;script&gt;" in clean_string
        assert "<script>" not in clean_string
    
    def test_nested_data_sanitization(self):
        """测试嵌套数据清理"""
        dirty_data = {
            "name": "<script>alert('xss')</script>",
            "description": "Normal text",
            "nested": {
                "field": "<img src=x onerror=alert('xss')>"
            },
            "list": ["<script>", "normal", "<iframe>"]
        }
        
        clean_data = XSSProtection.sanitize_input(dirty_data)
        
        assert "<script>" not in clean_data["name"]
        assert "&lt;script&gt;" in clean_data["name"]
        assert clean_data["description"] == "Normal text"
        assert "<img" not in clean_data["nested"]["field"]
        assert "<script>" not in clean_data["list"][0]


class TestCSRFProtection:
    """CSRF保护测试"""
    
    def test_token_generation(self):
        """测试CSRF令牌生成"""
        csrf = CSRFProtection()
        token1 = csrf.generate_token("session1")
        token2 = csrf.generate_token("session2")
        
        assert token1 != token2
        assert len(token1) > 20  # 确保令牌足够长
        assert len(token2) > 20
    
    def test_token_validation(self):
        """测试CSRF令牌验证"""
        csrf = CSRFProtection()
        token = csrf.generate_token("session1")
        
        # 有效令牌
        assert csrf.validate_token(token) == True
        
        # 无效令牌
        assert csrf.validate_token("invalid_token") == False
        assert csrf.validate_token("") == False
        assert csrf.validate_token(None) == False
    
    def test_token_expiration(self):
        """测试令牌过期"""
        csrf = CSRFProtection()
        csrf.token_lifetime = 1  # 1秒过期
        
        token = csrf.generate_token("session1")
        assert csrf.validate_token(token) == True
        
        # 等待令牌过期
        time.sleep(2)
        assert csrf.validate_token(token) == False


class TestRateLimiting:
    """速率限制测试"""
    
    def test_rate_limiting(self):
        """测试速率限制"""
        # 重置速率限制器
        rate_limiter.requests.clear()
        
        client_ip = "192.168.1.100"
        
        # 在限制内的请求应该被允许
        for i in range(50):
            assert rate_limiter.is_allowed(client_ip) == True
        
        # 超过限制的请求应该被拒绝
        rate_limiter.max_requests = 50
        assert rate_limiter.is_allowed(client_ip) == False


class TestSecurityTesting:
    """安全测试工具测试"""
    
    def test_vulnerability_scanning(self):
        """测试漏洞扫描"""
        tester = SecurityTester()
        
        # 测试SQL注入检测
        sql_injection = "'; DROP TABLE users; --"
        vulnerabilities = tester.scan_input_for_vulnerabilities(sql_injection)
        assert 'sql_injection' in vulnerabilities
        
        # 测试XSS检测
        xss_payload = "<script>alert('xss')</script>"
        vulnerabilities = tester.scan_input_for_vulnerabilities(xss_payload)
        assert 'xss' in vulnerabilities
        
        # 测试安全输入
        safe_input = "normal text input"
        vulnerabilities = tester.scan_input_for_vulnerabilities(safe_input)
        assert len(vulnerabilities) == 0
    
    def test_input_validation_testing(self):
        """测试输入验证测试"""
        tester = SecurityTester()
        
        # 创建一个简单的验证函数
        def simple_validator(input_str):
            return len(input_str) < 100 and "<script>" not in input_str
        
        # 测试验证函数
        results = tester.test_input_validation(simple_validator, 'xss')
        
        assert 'xss' in results
        assert len(results['xss']) > 0
        
        # 检查是否正确识别了漏洞
        vulnerable_count = sum(1 for result in results['xss'] if result['status'] == 'vulnerable')
        safe_count = sum(1 for result in results['xss'] if result['status'] == 'safe')
        
        assert safe_count > 0  # 应该有一些测试通过


class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_password_strength_testing(self):
        """测试密码强度测试"""
        tester = PasswordStrengthTester()
        
        # 强密码
        strong_password = "MyStr0ng!P@ssw0rd"
        result = tester.test_password_strength(strong_password)
        assert result['strength'] in ['强', '中等']
        assert result['is_strong'] == True
        
        # 弱密码
        weak_password = "123456"
        result = tester.test_password_strength(weak_password)
        assert result['strength'] in ['很弱', '弱']
        assert result['is_strong'] == False
        
        # 常见密码
        common_password = "password"
        result = tester.test_password_strength(common_password)
        assert result['is_strong'] == False
        assert any('常见密码' in feedback for feedback in result['feedback'])


class TestThreatDetection:
    """威胁检测测试"""
    
    def test_threat_detection(self):
        """测试威胁检测"""
        detector = ThreatDetection()
        
        # 测试SQL注入检测
        sql_threat = "'; DROP TABLE users; --"
        threats = detector.detect_threats(sql_threat)
        assert "SQL注入" in threats
        
        # 测试XSS检测
        xss_threat = "<script>alert('xss')</script>"
        threats = detector.detect_threats(xss_threat)
        assert "XSS攻击" in threats
        
        # 测试安全输入
        safe_input = "This is a normal input"
        threats = detector.detect_threats(safe_input)
        assert len(threats) == 0
    
    def test_suspicious_request_detection(self):
        """测试可疑请求检测"""
        detector = ThreatDetection()
        
        # 正常请求
        normal_request = {
            "username": "admin",
            "password": "password123",
            "email": "admin@example.com"
        }
        assert detector.is_suspicious_request(normal_request) == False
        
        # 可疑请求（包含恶意脚本）
        suspicious_request = {
            "username": "admin",
            "comment": "<script>alert('xss')</script>",
            "description": "'; DROP TABLE users; --"
        }
        assert detector.is_suspicious_request(suspicious_request) == True


class TestSecurityMonitoring:
    """安全监控测试"""
    
    def test_security_event_creation(self):
        """测试安全事件创建"""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILED,
            level=SecurityLevel.MEDIUM,
            timestamp=time.time(),
            client_ip="192.168.1.100",
            username="testuser"
        )
        
        assert event.event_type == SecurityEventType.LOGIN_FAILED
        assert event.level == SecurityLevel.MEDIUM
        assert event.client_ip == "192.168.1.100"
        assert event.username == "testuser"
        
        # 测试转换为字典
        event_dict = event.to_dict()
        assert event_dict['event_type'] == 'login_failed'
        assert event_dict['level'] == 'medium'
        assert event_dict['client_ip'] == "192.168.1.100"
    
    def test_security_monitor_basic_functionality(self):
        """测试安全监控器基本功能"""
        monitor = SecurityMonitor(max_events=100)
        
        # 创建测试事件
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILED,
            level=SecurityLevel.MEDIUM,
            timestamp=time.time(),
            client_ip="192.168.1.100"
        )
        
        # 记录事件
        monitor.record_event(event)
        
        # 检查事件是否被记录
        assert len(monitor.events) == 1
        assert monitor.event_counts[SecurityEventType.LOGIN_FAILED] == 1
        assert "192.168.1.100" in monitor.ip_activity
    
    def test_threat_level_calculation(self):
        """测试威胁级别计算"""
        monitor = SecurityMonitor(max_events=100)
        
        # 添加一些高危事件
        current_time = time.time()
        for i in range(5):
            event = SecurityEvent(
                event_type=SecurityEventType.SQL_INJECTION_ATTEMPT,
                level=SecurityLevel.HIGH,
                timestamp=current_time - i * 60,  # 每分钟一个事件
                client_ip=f"192.168.1.{100 + i}"
            )
            monitor.record_event(event)
        
        threat_level = monitor._calculate_threat_level()
        assert threat_level in ["HIGH", "MEDIUM"]  # 应该是高或中等威胁级别
    
    def test_security_score_calculation(self):
        """测试安全评分计算"""
        monitor = SecurityMonitor(max_events=100)
        
        # 初始评分应该是100
        initial_score = monitor._calculate_security_score()
        assert initial_score == 100
        
        # 添加一些安全事件
        current_time = time.time()
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILED,
            level=SecurityLevel.MEDIUM,
            timestamp=current_time,
            client_ip="192.168.1.100"
        )
        monitor.record_event(event)
        
        # 评分应该降低
        new_score = monitor._calculate_security_score()
        assert new_score < initial_score


class TestSecurityPolicies:
    """安全策略测试"""
    
    def test_password_policy_validation(self):
        """测试密码策略验证"""
        config = SecurityConfig()
        policies = SecurityPolicies(config)
        
        # 强密码
        strong_password = "MyStr0ng!P@ssw0rd"
        is_valid, errors = policies.validate_password_policy(strong_password)
        assert is_valid == True
        assert len(errors) == 0
        
        # 弱密码
        weak_password = "123"
        is_valid, errors = policies.validate_password_policy(weak_password)
        assert is_valid == False
        assert len(errors) > 0
    
    def test_weak_password_detection(self):
        """测试弱密码检测"""
        config = SecurityConfig()
        policies = SecurityPolicies(config)
        
        # 常见弱密码
        assert policies.is_weak_password("password") == True
        assert policies.is_weak_password("123456") == True
        assert policies.is_weak_password("admin") == True
        
        # 强密码
        assert policies.is_weak_password("MyStr0ng!P@ssw0rd") == False
    
    def test_file_upload_validation(self):
        """测试文件上传验证"""
        config = SecurityConfig()
        policies = SecurityPolicies(config)
        
        # 允许的文件类型
        assert policies.is_file_allowed("document.csv") == True
        assert policies.is_file_allowed("report.xlsx") == True
        assert policies.is_file_allowed("data.txt") == True
        
        # 不允许的文件类型
        assert policies.is_file_allowed("script.exe") == False
        assert policies.is_file_allowed("malware.bat") == False
        assert policies.is_file_allowed("") == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])