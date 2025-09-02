"""
安全配置模块
定义系统安全相关的配置和策略
"""
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
import os


class SecurityConfig(BaseSettings):
    """安全配置类"""
    
    # 密码策略
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL_CHARS: bool = True
    PASSWORD_MAX_AGE_DAYS: int = 90
    PASSWORD_HISTORY_COUNT: int = 5
    
    # 账户锁定策略
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 30
    
    # 会话安全
    SESSION_TIMEOUT_MINUTES: int = 60
    CONCURRENT_SESSIONS_LIMIT: int = 3
    
    # 速率限制
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100
    RATE_LIMIT_BURST_SIZE: int = 20
    
    # IP阻止策略
    IP_BLOCK_THRESHOLD: int = 10
    IP_BLOCK_DURATION_HOURS: int = 1
    
    # CSRF保护
    CSRF_TOKEN_LIFETIME_MINUTES: int = 60
    CSRF_COOKIE_SECURE: bool = True
    CSRF_COOKIE_HTTPONLY: bool = True
    
    # 内容安全策略
    CSP_DEFAULT_SRC: List[str] = ["'self'"]
    CSP_SCRIPT_SRC: List[str] = ["'self'", "'unsafe-inline'", "'unsafe-eval'"]
    CSP_STYLE_SRC: List[str] = ["'self'", "'unsafe-inline'"]
    CSP_IMG_SRC: List[str] = ["'self'", "data:", "https:"]
    CSP_FONT_SRC: List[str] = ["'self'", "https:"]
    CSP_CONNECT_SRC: List[str] = ["'self'"]
    
    # 文件上传安全
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: List[str] = [".csv", ".xlsx", ".txt"]
    SCAN_UPLOADED_FILES: bool = True
    
    # 日志安全
    LOG_SENSITIVE_DATA: bool = False
    SECURITY_LOG_RETENTION_DAYS: int = 90
    
    # 加密设置
    ENCRYPTION_ALGORITHM: str = "AES-256-GCM"
    KEY_ROTATION_DAYS: int = 30
    
    # 审计设置
    AUDIT_ALL_REQUESTS: bool = True
    AUDIT_FAILED_REQUESTS: bool = True
    AUDIT_SENSITIVE_OPERATIONS: bool = True
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = True


class SecurityPolicies:
    """安全策略类"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
    
    def validate_password_policy(self, password: str) -> tuple[bool, List[str]]:
        """验证密码是否符合安全策略"""
        errors = []
        
        if len(password) < self.config.PASSWORD_MIN_LENGTH:
            errors.append(f"密码长度至少{self.config.PASSWORD_MIN_LENGTH}位")
        
        if self.config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("密码必须包含至少一个大写字母")
        
        if self.config.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("密码必须包含至少一个小写字母")
        
        if self.config.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            errors.append("密码必须包含至少一个数字")
        
        if self.config.PASSWORD_REQUIRE_SPECIAL_CHARS:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("密码必须包含至少一个特殊字符")
        
        return len(errors) == 0, errors
    
    def is_weak_password(self, password: str) -> bool:
        """检查是否为弱密码"""
        weak_passwords = [
            "password", "123456", "admin", "root", "user",
            "qwerty", "abc123", "password123", "admin123"
        ]
        
        return password.lower() in weak_passwords
    
    def get_csp_header(self) -> str:
        """生成内容安全策略头"""
        policies = [
            f"default-src {' '.join(self.config.CSP_DEFAULT_SRC)}",
            f"script-src {' '.join(self.config.CSP_SCRIPT_SRC)}",
            f"style-src {' '.join(self.config.CSP_STYLE_SRC)}",
            f"img-src {' '.join(self.config.CSP_IMG_SRC)}",
            f"font-src {' '.join(self.config.CSP_FONT_SRC)}",
            f"connect-src {' '.join(self.config.CSP_CONNECT_SRC)}",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        return "; ".join(policies)
    
    def is_file_allowed(self, filename: str) -> bool:
        """检查文件是否允许上传"""
        if not filename:
            return False
        
        extension = os.path.splitext(filename)[1].lower()
        return extension in self.config.ALLOWED_FILE_EXTENSIONS
    
    def get_security_headers(self) -> Dict[str, str]:
        """获取安全响应头"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": self.get_csp_header(),
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }


class ThreatDetection:
    """威胁检测类"""
    
    def __init__(self):
        self.suspicious_patterns = [
            # SQL注入模式
            r"(\bunion\b.*\bselect\b)|(\bselect\b.*\bunion\b)",
            r"(\binsert\b.*\binto\b)|(\bdelete\b.*\bfrom\b)",
            r"(\bdrop\b.*\btable\b)|(\bcreate\b.*\btable\b)",
            r"(\bexec\b.*\()|(\bexecute\b.*\()",
            
            # XSS模式
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            
            # 路径遍历
            r"\.\./",
            r"\.\.\\",
            
            # 命令注入
            r"[;&|`]",
            r"\$\(",
            r"<%.*%>",
        ]
    
    def detect_threats(self, input_data: str) -> List[str]:
        """检测输入数据中的威胁"""
        import re
        threats = []
        
        input_lower = input_data.lower()
        
        for i, pattern in enumerate(self.suspicious_patterns):
            if re.search(pattern, input_lower, re.IGNORECASE):
                threat_types = [
                    "SQL注入", "SQL注入", "SQL注入", "SQL注入",  # 0-3
                    "XSS攻击", "XSS攻击", "XSS攻击", "XSS攻击",  # 4-7
                    "路径遍历", "路径遍历",                      # 8-9
                    "命令注入", "命令注入", "命令注入"           # 10-12
                ]
                if i < len(threat_types):
                    threats.append(threat_types[i])
        
        return list(set(threats))  # 去重
    
    def is_suspicious_request(self, request_data: Dict) -> bool:
        """检查请求是否可疑"""
        # 检查请求大小
        if len(str(request_data)) > 100000:  # 100KB
            return True
        
        # 检查嵌套深度
        def get_depth(obj, depth=0):
            if isinstance(obj, dict):
                return max(get_depth(v, depth + 1) for v in obj.values()) if obj else depth
            elif isinstance(obj, list):
                return max(get_depth(item, depth + 1) for item in obj) if obj else depth
            return depth
        
        if get_depth(request_data) > 10:
            return True
        
        # 检查字符串内容
        for key, value in request_data.items():
            if isinstance(value, str):
                threats = self.detect_threats(value)
                if threats:
                    return True
        
        return False


# 全局安全配置实例
security_config = SecurityConfig()
security_policies = SecurityPolicies(security_config)
threat_detection = ThreatDetection()