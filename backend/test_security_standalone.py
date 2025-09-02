"""
独立安全功能测试
不依赖数据库和外部服务的安全功能测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import time
from app.core.validators import InputValidator
from app.core.security_middleware import XSSProtection, CSRFProtection
from app.core.security_config import SecurityPolicies, SecurityConfig, ThreatDetection
from app.core.security_testing import SecurityTester, PasswordStrengthTester
from app.core.security_monitoring import SecurityEvent, SecurityEventType, SecurityLevel, SecurityMonitor


def test_input_validation():
    """测试输入验证"""
    print("测试输入验证...")
    
    # 测试IP地址验证
    assert InputValidator.validate_ip_address("192.168.1.1") == True
    assert InputValidator.validate_ip_address("256.256.256.256") == False
    print("✓ IP地址验证测试通过")
    
    # 测试子网验证
    assert InputValidator.validate_subnet("192.168.1.0/24") == True
    assert InputValidator.validate_subnet("192.168.1.0/33") == False
    print("✓ 子网验证测试通过")
    
    # 测试MAC地址验证
    assert InputValidator.validate_mac_address("00:11:22:33:44:55") == True
    assert InputValidator.validate_mac_address("invalid_mac") == False
    print("✓ MAC地址验证测试通过")
    
    # 测试SQL注入检测
    assert InputValidator.validate_sql_safe_string("normal text") == True
    assert InputValidator.validate_sql_safe_string("'; DROP TABLE users; --") == False
    print("✓ SQL注入检测测试通过")


def test_xss_protection():
    """测试XSS防护"""
    print("\n测试XSS防护...")
    
    # 测试字符串清理
    dirty_string = "<script>alert('xss')</script>"
    clean_string = XSSProtection._sanitize_string(dirty_string)
    assert "<script>" not in clean_string
    assert "&lt;script&gt;" in clean_string
    print("✓ XSS字符串清理测试通过")
    
    # 测试嵌套数据清理
    dirty_data = {
        "name": "<script>alert('xss')</script>",
        "description": "Normal text"
    }
    clean_data = XSSProtection.sanitize_input(dirty_data)
    assert "<script>" not in clean_data["name"]
    assert clean_data["description"] == "Normal text"
    print("✓ XSS嵌套数据清理测试通过")


def test_csrf_protection():
    """测试CSRF保护"""
    print("\n测试CSRF保护...")
    
    csrf = CSRFProtection()
    
    # 测试令牌生成
    token1 = csrf.generate_token("session1")
    token2 = csrf.generate_token("session2")
    assert token1 != token2
    assert len(token1) > 20
    print("✓ CSRF令牌生成测试通过")
    
    # 测试令牌验证
    assert csrf.validate_token(token1) == True
    assert csrf.validate_token("invalid_token") == False
    print("✓ CSRF令牌验证测试通过")


def test_security_testing():
    """测试安全测试工具"""
    print("\n测试安全测试工具...")
    
    tester = SecurityTester()
    
    # 测试漏洞扫描
    sql_injection = "'; DROP TABLE users; --"
    vulnerabilities = tester.scan_input_for_vulnerabilities(sql_injection)
    assert 'sql_injection' in vulnerabilities
    print("✓ SQL注入漏洞扫描测试通过")
    
    xss_payload = "<script>alert('xss')</script>"
    vulnerabilities = tester.scan_input_for_vulnerabilities(xss_payload)
    assert 'xss' in vulnerabilities
    print("✓ XSS漏洞扫描测试通过")
    
    # 测试安全输入
    safe_input = "normal text input"
    vulnerabilities = tester.scan_input_for_vulnerabilities(safe_input)
    assert len(vulnerabilities) == 0
    print("✓ 安全输入扫描测试通过")


def test_password_security():
    """测试密码安全"""
    print("\n测试密码安全...")
    
    tester = PasswordStrengthTester()
    
    # 测试强密码
    strong_password = "MyStr0ng!P@ssw0rd"
    result = tester.test_password_strength(strong_password)
    assert result['is_strong'] == True
    print("✓ 强密码测试通过")
    
    # 测试弱密码
    weak_password = "123456"
    result = tester.test_password_strength(weak_password)
    assert result['is_strong'] == False
    print("✓ 弱密码测试通过")
    
    # 测试常见密码
    common_password = "password"
    result = tester.test_password_strength(common_password)
    assert result['is_strong'] == False
    print("✓ 常见密码检测测试通过")


def test_threat_detection():
    """测试威胁检测"""
    print("\n测试威胁检测...")
    
    detector = ThreatDetection()
    
    # 测试SQL注入检测
    sql_threat = "'; DROP TABLE users; --"
    threats = detector.detect_threats(sql_threat)
    assert "SQL注入" in threats
    print("✓ SQL注入威胁检测测试通过")
    
    # 测试XSS检测
    xss_threat = "<script>alert('xss')</script>"
    threats = detector.detect_threats(xss_threat)
    assert "XSS攻击" in threats
    print("✓ XSS威胁检测测试通过")
    
    # 测试安全输入
    safe_input = "This is a normal input"
    threats = detector.detect_threats(safe_input)
    assert len(threats) == 0
    print("✓ 安全输入威胁检测测试通过")


def test_security_monitoring():
    """测试安全监控"""
    print("\n测试安全监控...")
    
    # 测试安全事件创建
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
    print("✓ 安全事件创建测试通过")
    
    # 测试事件转换
    event_dict = event.to_dict()
    assert event_dict['event_type'] == 'login_failed'
    assert event_dict['level'] == 'medium'
    print("✓ 安全事件转换测试通过")
    
    # 测试安全监控器
    monitor = SecurityMonitor(max_events=100)
    monitor.record_event(event)
    
    assert len(monitor.events) == 1
    assert monitor.event_counts[SecurityEventType.LOGIN_FAILED] == 1
    print("✓ 安全监控器测试通过")


def test_security_policies():
    """测试安全策略"""
    print("\n测试安全策略...")
    
    config = SecurityConfig()
    policies = SecurityPolicies(config)
    
    # 测试密码策略
    strong_password = "MyStr0ng!P@ssw0rd"
    is_valid, errors = policies.validate_password_policy(strong_password)
    assert is_valid == True
    assert len(errors) == 0
    print("✓ 强密码策略验证测试通过")
    
    weak_password = "123"
    is_valid, errors = policies.validate_password_policy(weak_password)
    assert is_valid == False
    assert len(errors) > 0
    print("✓ 弱密码策略验证测试通过")
    
    # 测试弱密码检测
    assert policies.is_weak_password("password") == True
    assert policies.is_weak_password("MyStr0ng!P@ssw0rd") == False
    print("✓ 弱密码检测测试通过")
    
    # 测试文件上传验证
    assert policies.is_file_allowed("document.csv") == True
    assert policies.is_file_allowed("script.exe") == False
    print("✓ 文件上传验证测试通过")


def run_all_tests():
    """运行所有测试"""
    print("开始运行安全功能测试...\n")
    
    try:
        test_input_validation()
        test_xss_protection()
        test_csrf_protection()
        test_security_testing()
        test_password_security()
        test_threat_detection()
        test_security_monitoring()
        test_security_policies()
        
        print("\n" + "="*50)
        print("✅ 所有安全功能测试通过！")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)