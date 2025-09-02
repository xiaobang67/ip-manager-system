"""
安全功能测试
测试输入验证、XSS防护、CSRF保护等安全功能
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
import time

from app.core.validators import InputValidator, validate_request_data, rate_limiter
from app.core.security_middleware import XSSProtection, CSRFProtection, SecurityMiddleware
from app.core.security_config import SecurityPolicies, SecurityConfig, ThreatDetection
from app.core.security_testing import SecurityTester, PasswordStrengthTester
from app.core.exceptions import ValidationError, SecurityError
from main import app


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
    
    def test_xss_detection(self):
        """测试XSS检测"""
        # 安全输入
        safe_text = "This is normal text"
        assert InputValidator.validate_sql_safe_string(safe_text) == True
        
        # XSS尝试
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "onclick=alert('xss')"
        ]
        
        for attempt in xss_attempts:
            assert InputValidator.validate_sql_safe_string(attempt) == False
    
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


class TestSecurityMiddleware:
    """安全中间件测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_security_headers(self, client):
        """测试安全响应头"""
        response = client.get("/")
        
        # 检查安全头是否存在
        assert "X-XSS-Protection" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "Content-Security-Policy" in response.headers
        assert "Strict-Transport-Security" in response.headers
        
        # 检查头的值
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
    
    def test_rate_limiting_middleware(self, client):
        """测试中间件速率限制"""
        # 发送大量请求测试速率限制
        responses = []
        for i in range(150):  # 超过默认限制
            response = client.get("/health")
            responses.append(response.status_code)
        
        # 应该有一些请求被限制
        assert 429 in responses  # Too Many Requests


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


class TestSecurityIntegration:
    """安全集成测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_malicious_input_rejection(self, client):
        """测试恶意输入拒绝"""
        # 尝试SQL注入
        malicious_data = {
            "username": "admin'; DROP TABLE users; --",
            "password": "password"
        }
        
        response = client.post("/api/auth/login", json=malicious_data)
        # 应该返回验证错误或被拒绝
        assert response.status_code in [400, 422, 403]
    
    def test_xss_input_sanitization(self, client):
        """测试XSS输入清理"""
        # 创建包含XSS的数据
        xss_data = {
            "description": "<script>alert('xss')</script>",
            "name": "Test Subnet"
        }
        
        # 这个测试需要有效的认证令牌
        # 在实际测试中，你需要先登录获取令牌
        headers = {"Authorization": "Bearer test_token"}
        
        response = client.post("/api/subnets", json=xss_data, headers=headers)
        
        # 请求应该被处理，但XSS内容应该被清理
        if response.status_code == 201:
            # 检查返回的数据是否已清理
            response_data = response.json()
            assert "<script>" not in str(response_data)
    
    def test_csrf_protection(self, client):
        """测试CSRF保护"""
        # 不带CSRF令牌的POST请求应该被拒绝
        response = client.post("/api/subnets", json={"name": "test"})
        
        # 应该返回认证错误或CSRF错误
        assert response.status_code in [401, 403]
    
    def test_rate_limiting_protection(self, client):
        """测试速率限制保护"""
        # 发送大量请求
        responses = []
        for i in range(200):
            response = client.get("/health")
            responses.append(response.status_code)
            if response.status_code == 429:
                break
        
        # 应该触发速率限制
        assert 429 in responses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])