"""
输入验证模块
提供各种输入数据的验证功能，防止SQL注入和其他安全漏洞
"""
import re
import ipaddress
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, validator, Field
from fastapi import HTTPException, status
import html
import bleach
from urllib.parse import urlparse

# 允许的HTML标签（用于富文本内容）
ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
ALLOWED_ATTRIBUTES = {}

class InputValidator:
    """输入验证器类"""
    
    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """验证IP地址格式"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_subnet(subnet: str) -> bool:
        """验证子网格式"""
        try:
            ipaddress.ip_network(subnet, strict=False)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """验证MAC地址格式"""
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac))
    
    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """验证主机名格式"""
        if len(hostname) > 253:
            return False
        
        # 允许的字符：字母、数字、连字符、点
        pattern = r'^[a-zA-Z0-9.-]+$'
        if not re.match(pattern, hostname):
            return False
        
        # 检查每个标签
        labels = hostname.split('.')
        for label in labels:
            if len(label) > 63 or len(label) == 0:
                return False
            if label.startswith('-') or label.endswith('-'):
                return False
        
        return True
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """验证用户名格式"""
        # 用户名只能包含字母、数字、下划线，长度3-50
        pattern = r'^[a-zA-Z0-9_]{3,50}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """清理字符串，防止XSS攻击"""
        if not text:
            return ""
        
        # 限制长度
        text = text[:max_length]
        
        # HTML转义
        text = html.escape(text)
        
        # 移除潜在的脚本标签
        text = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        
        return text.strip()
    
    @staticmethod
    def validate_sql_safe_string(text: str) -> bool:
        """检查字符串是否包含SQL注入风险字符"""
        # 检查常见的SQL注入模式
        dangerous_patterns = [
            r"('|(\\')|(;)|(\\;))",  # 单引号和分号
            r"(--)|(/\\*.*\\*/)",     # SQL注释
            r"\\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\\b",  # SQL关键字
            r"\\b(script|javascript|vbscript|onload|onerror|onclick)\\b",  # 脚本相关
        ]
        
        text_lower = text.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    @staticmethod
    def validate_port(port: int) -> bool:
        """验证端口号"""
        return 1 <= port <= 65535
    
    @staticmethod
    def validate_vlan_id(vlan_id: int) -> bool:
        """验证VLAN ID"""
        return 1 <= vlan_id <= 4094


class SecureBaseModel(BaseModel):
    """安全的基础模型，包含通用验证"""
    
    class Config:
        # 禁止额外字段
        extra = "forbid"
        # 验证赋值
        validate_assignment = True
        # 使用枚举值
        use_enum_values = True


class IPAddressValidator(SecureBaseModel):
    """IP地址验证模型"""
    ip_address: str = Field(..., min_length=7, max_length=15)
    
    @validator('ip_address')
    def validate_ip(cls, v):
        if not InputValidator.validate_ip_address(v):
            raise ValueError('无效的IP地址格式')
        return v


class SubnetValidator(SecureBaseModel):
    """子网验证模型"""
    network: str = Field(..., min_length=9, max_length=18)
    
    @validator('network')
    def validate_network(cls, v):
        if not InputValidator.validate_subnet(v):
            raise ValueError('无效的子网格式')
        return v


class MacAddressValidator(SecureBaseModel):
    """MAC地址验证模型"""
    mac_address: str = Field(..., min_length=17, max_length=17)
    
    @validator('mac_address')
    def validate_mac(cls, v):
        if not InputValidator.validate_mac_address(v):
            raise ValueError('无效的MAC地址格式')
        return v


class HostnameValidator(SecureBaseModel):
    """主机名验证模型"""
    hostname: str = Field(..., min_length=1, max_length=253)
    
    @validator('hostname')
    def validate_hostname(cls, v):
        if not InputValidator.validate_hostname(v):
            raise ValueError('无效的主机名格式')
        return v


class UsernameValidator(SecureBaseModel):
    """用户名验证模型"""
    username: str = Field(..., min_length=3, max_length=50)
    
    @validator('username')
    def validate_username(cls, v):
        if not InputValidator.validate_username(v):
            raise ValueError('用户名只能包含字母、数字、下划线，长度3-50位')
        return v


class EmailValidator(SecureBaseModel):
    """邮箱验证模型"""
    email: str = Field(..., min_length=5, max_length=100)
    
    @validator('email')
    def validate_email(cls, v):
        if not InputValidator.validate_email(v):
            raise ValueError('无效的邮箱格式')
        return v


class TextValidator(SecureBaseModel):
    """文本验证模型"""
    text: str = Field(..., max_length=1000)
    
    @validator('text')
    def validate_text(cls, v):
        if not InputValidator.validate_sql_safe_string(v):
            raise ValueError('文本包含不安全字符')
        return InputValidator.sanitize_string(v)


def validate_request_data(data: Dict[str, Any], validators: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证请求数据
    
    Args:
        data: 请求数据
        validators: 验证器字典
    
    Returns:
        Dict: 验证后的数据
    
    Raises:
        HTTPException: 验证失败时抛出异常
    """
    validated_data = {}
    errors = []
    
    for field, validator in validators.items():
        if field in data:
            try:
                if hasattr(validator, 'validate'):
                    validated_data[field] = validator.validate(data[field])
                else:
                    validated_data[field] = validator(data[field])
            except ValueError as e:
                errors.append(f"{field}: {str(e)}")
    
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "数据验证失败", "errors": errors}
        )
    
    return validated_data


class RateLimitValidator:
    """请求频率限制验证器"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 3600):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = {}
    
    def is_allowed(self, client_ip: str) -> bool:
        """检查是否允许请求"""
        import time
        current_time = time.time()
        
        # 清理过期记录
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if any(t > current_time - self.time_window for t in timestamps)
        }
        
        # 检查当前IP的请求次数
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # 过滤时间窗口内的请求
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if t > current_time - self.time_window
        ]
        
        # 检查是否超过限制
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # 记录当前请求
        self.requests[client_ip].append(current_time)
        return True


# 全局速率限制器实例
rate_limiter = RateLimitValidator()