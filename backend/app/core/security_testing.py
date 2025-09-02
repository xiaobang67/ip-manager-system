"""
安全测试模块
提供安全漏洞扫描和测试功能
"""
import re
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class SecurityTester:
    """安全测试器"""
    
    def __init__(self):
        self.vulnerability_patterns = {
            'sql_injection': [
                r"(\bunion\b.*\bselect\b)|(\bselect\b.*\bunion\b)",
                r"(\binsert\b.*\binto\b)|(\bdelete\b.*\bfrom\b)",
                r"(\bdrop\b.*\btable\b)|(\bcreate\b.*\btable\b)",
                r"(\bexec\b.*\()|(\bexecute\b.*\()",
                r"'.*or.*'.*=.*'",
                r"'.*and.*'.*=.*'",
                r"--.*",
                r"/\*.*\*/"
            ],
            'xss': [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"on\w+\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
                r"<link[^>]*>",
                r"<meta[^>]*>"
            ],
            'path_traversal': [
                r"\.\./",
                r"\.\.\\",
                r"%2e%2e%2f",
                r"%2e%2e\\",
                r"..%2f",
                r"..%5c"
            ],
            'command_injection': [
                r"[;&|`]",
                r"\$\(",
                r"<%.*%>",
                r"\${.*}",
                r"`.*`"
            ],
            'ldap_injection': [
                r"\*\)",
                r"\(\|",
                r"\(&",
                r"\(!"
            ]
        }
        
        self.test_payloads = {
            'sql_injection': [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "1' OR 1=1 --",
                "admin'--",
                "' OR 'x'='x",
                "1; SELECT * FROM information_schema.tables"
            ],
            'xss': [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "';alert('XSS');//",
                "<iframe src=javascript:alert('XSS')></iframe>",
                "<body onload=alert('XSS')>"
            ],
            'path_traversal': [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
                "....//....//....//etc/passwd",
                "..%252f..%252f..%252fetc%252fpasswd"
            ],
            'command_injection': [
                "; ls -la",
                "| whoami",
                "& dir",
                "`id`",
                "$(whoami)",
                "; cat /etc/passwd",
                "| type C:\\Windows\\System32\\drivers\\etc\\hosts"
            ]
        }
    
    def scan_input_for_vulnerabilities(self, input_data: str) -> Dict[str, List[str]]:
        """扫描输入数据中的安全漏洞"""
        vulnerabilities = {}
        
        for vuln_type, patterns in self.vulnerability_patterns.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, input_data, re.IGNORECASE):
                    matches.append(pattern)
            
            if matches:
                vulnerabilities[vuln_type] = matches
        
        return vulnerabilities
    
    def test_input_validation(self, validator_func, test_type: str = 'all') -> Dict[str, List[Dict]]:
        """测试输入验证函数的安全性"""
        results = {}
        
        test_types = [test_type] if test_type != 'all' else list(self.test_payloads.keys())
        
        for vuln_type in test_types:
            if vuln_type not in self.test_payloads:
                continue
                
            results[vuln_type] = []
            
            for payload in self.test_payloads[vuln_type]:
                try:
                    # 测试验证函数是否能正确拒绝恶意输入
                    result = validator_func(payload)
                    
                    # 如果验证通过，说明存在安全漏洞
                    if result:
                        results[vuln_type].append({
                            'payload': payload,
                            'status': 'vulnerable',
                            'message': '验证函数未能检测到恶意输入'
                        })
                    else:
                        results[vuln_type].append({
                            'payload': payload,
                            'status': 'safe',
                            'message': '验证函数正确拒绝了恶意输入'
                        })
                        
                except Exception as e:
                    results[vuln_type].append({
                        'payload': payload,
                        'status': 'error',
                        'message': f'验证函数抛出异常: {str(e)}'
                    })
        
        return results
    
    def generate_security_report(self, test_results: Dict) -> str:
        """生成安全测试报告"""
        report = []
        report.append("=" * 60)
        report.append("安全测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        total_tests = 0
        vulnerable_tests = 0
        
        for vuln_type, results in test_results.items():
            report.append(f"漏洞类型: {vuln_type.upper()}")
            report.append("-" * 40)
            
            for result in results:
                total_tests += 1
                status_symbol = {
                    'vulnerable': '❌',
                    'safe': '✅',
                    'error': '⚠️'
                }.get(result['status'], '❓')
                
                if result['status'] == 'vulnerable':
                    vulnerable_tests += 1
                
                report.append(f"{status_symbol} {result['payload'][:50]}...")
                report.append(f"   状态: {result['status']}")
                report.append(f"   说明: {result['message']}")
                report.append("")
        
        report.append("=" * 60)
        report.append("测试总结")
        report.append("=" * 60)
        report.append(f"总测试数: {total_tests}")
        report.append(f"发现漏洞: {vulnerable_tests}")
        report.append(f"安全率: {((total_tests - vulnerable_tests) / total_tests * 100):.1f}%")
        
        return "\n".join(report)


class PasswordStrengthTester:
    """密码强度测试器"""
    
    def __init__(self):
        self.common_passwords = [
            "password", "123456", "password123", "admin", "qwerty",
            "abc123", "Password1", "welcome", "monkey", "1234567890"
        ]
        
        self.keyboard_patterns = [
            "qwerty", "asdf", "zxcv", "1234", "abcd"
        ]
    
    def test_password_strength(self, password: str) -> Dict[str, any]:
        """测试密码强度"""
        score = 0
        feedback = []
        
        # 长度检查
        if len(password) >= 12:
            score += 2
        elif len(password) >= 8:
            score += 1
        else:
            feedback.append("密码长度至少应为8位")
        
        # 字符类型检查
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        score += char_types
        
        if not has_lower:
            feedback.append("应包含小写字母")
        if not has_upper:
            feedback.append("应包含大写字母")
        if not has_digit:
            feedback.append("应包含数字")
        if not has_special:
            feedback.append("应包含特殊字符")
        
        # 常见密码检查
        if password.lower() in self.common_passwords:
            score -= 3
            feedback.append("不要使用常见密码")
        
        # 键盘模式检查
        password_lower = password.lower()
        for pattern in self.keyboard_patterns:
            if pattern in password_lower:
                score -= 1
                feedback.append("避免使用键盘模式")
                break
        
        # 重复字符检查
        if len(set(password)) < len(password) * 0.6:
            score -= 1
            feedback.append("避免过多重复字符")
        
        # 计算强度等级
        if score >= 7:
            strength = "强"
        elif score >= 5:
            strength = "中等"
        elif score >= 3:
            strength = "弱"
        else:
            strength = "很弱"
        
        return {
            'score': max(0, score),
            'strength': strength,
            'feedback': feedback,
            'is_strong': score >= 5
        }


class SecurityAuditor:
    """安全审计器"""
    
    def __init__(self):
        self.audit_rules = {
            'failed_login_threshold': 5,
            'suspicious_activity_threshold': 10,
            'rate_limit_threshold': 100,
            'session_timeout': 3600,
            'password_age_limit': 7776000  # 90天
        }
    
    def audit_user_activity(self, user_logs: List[Dict]) -> Dict[str, any]:
        """审计用户活动"""
        audit_result = {
            'suspicious_activities': [],
            'security_violations': [],
            'recommendations': []
        }
        
        # 统计失败登录次数
        failed_logins = sum(1 for log in user_logs if log.get('action') == 'login_failed')
        if failed_logins >= self.audit_rules['failed_login_threshold']:
            audit_result['security_violations'].append({
                'type': 'excessive_failed_logins',
                'count': failed_logins,
                'severity': 'high'
            })
        
        # 检查异常活动模式
        activity_times = [log.get('timestamp') for log in user_logs if log.get('timestamp')]
        if self._detect_unusual_activity_pattern(activity_times):
            audit_result['suspicious_activities'].append({
                'type': 'unusual_activity_pattern',
                'description': '检测到异常的活动时间模式'
            })
        
        # 检查权限提升尝试
        privilege_attempts = [log for log in user_logs if 'privilege' in log.get('action', '')]
        if privilege_attempts:
            audit_result['suspicious_activities'].append({
                'type': 'privilege_escalation_attempt',
                'count': len(privilege_attempts)
            })
        
        return audit_result
    
    def _detect_unusual_activity_pattern(self, timestamps: List[float]) -> bool:
        """检测异常活动模式"""
        if len(timestamps) < 10:
            return False
        
        # 检查是否有大量活动集中在短时间内
        timestamps.sort()
        for i in range(len(timestamps) - 9):
            if timestamps[i + 9] - timestamps[i] < 60:  # 1分钟内10次活动
                return True
        
        return False
    
    def generate_security_recommendations(self, audit_results: Dict) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        if audit_results.get('security_violations'):
            recommendations.append("立即审查安全违规行为")
            recommendations.append("考虑临时锁定相关账户")
        
        if audit_results.get('suspicious_activities'):
            recommendations.append("加强监控可疑活动")
            recommendations.append("启用额外的安全验证")
        
        recommendations.extend([
            "定期更新密码策略",
            "启用多因素认证",
            "定期进行安全培训",
            "保持系统和依赖项更新"
        ])
        
        return recommendations


class PenetrationTester:
    """渗透测试器"""
    
    def __init__(self):
        self.test_cases = {
            'authentication_bypass': [
                {'username': 'admin', 'password': "' OR '1'='1"},
                {'username': "admin'--", 'password': 'anything'},
                {'username': 'admin', 'password': 'admin'},
            ],
            'authorization_bypass': [
                {'endpoint': '/api/admin/users', 'method': 'GET'},
                {'endpoint': '/api/users/1', 'method': 'DELETE'},
                {'endpoint': '/api/system/config', 'method': 'PUT'},
            ],
            'input_validation': [
                {'field': 'ip_address', 'value': '192.168.1.1; rm -rf /'},
                {'field': 'subnet', 'value': '<script>alert("xss")</script>'},
                {'field': 'description', 'value': "'; DROP TABLE users; --"},
            ]
        }
    
    def run_penetration_tests(self, target_system) -> Dict[str, List[Dict]]:
        """运行渗透测试"""
        results = {}
        
        for test_category, test_cases in self.test_cases.items():
            results[test_category] = []
            
            for test_case in test_cases:
                try:
                    result = self._execute_test_case(target_system, test_category, test_case)
                    results[test_category].append(result)
                except Exception as e:
                    results[test_category].append({
                        'test_case': test_case,
                        'status': 'error',
                        'message': str(e)
                    })
        
        return results
    
    def _execute_test_case(self, target_system, category: str, test_case: Dict) -> Dict:
        """执行单个测试用例"""
        # 这里应该实现具体的测试逻辑
        # 由于这是示例代码，我们只返回模拟结果
        
        return {
            'test_case': test_case,
            'category': category,
            'status': 'passed',  # 或 'failed', 'error'
            'message': '测试通过，未发现安全漏洞',
            'timestamp': time.time()
        }


# 全局安全测试实例
security_tester = SecurityTester()
password_tester = PasswordStrengthTester()
security_auditor = SecurityAuditor()
penetration_tester = PenetrationTester()