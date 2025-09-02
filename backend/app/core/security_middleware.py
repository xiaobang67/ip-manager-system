"""
安全中间件模块
提供XSS防护、CSRF保护、安全头设置等功能
"""
import secrets
import time
from typing import Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import json
from .validators import rate_limiter

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.csrf_tokens: Dict[str, float] = {}
        self.failed_attempts: Dict[str, list] = {}
        self.blocked_ips: Dict[str, float] = {}
    
    async def dispatch(self, request: Request, call_next):
        # 获取客户端IP
        client_ip = self.get_client_ip(request)
        
        # 检查IP是否被阻止
        if self.is_ip_blocked(client_ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "IP地址已被临时阻止"}
            )
        
        # 速率限制检查
        if not rate_limiter.is_allowed(client_ip):
            self.record_failed_attempt(client_ip)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "请求过于频繁，请稍后再试"}
            )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 添加安全头
            self.add_security_headers(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            self.record_failed_attempt(client_ip)
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def add_security_headers(self, response: Response):
        """添加安全响应头"""
        # XSS保护
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 内容类型嗅探保护
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 点击劫持保护
        response.headers["X-Frame-Options"] = "DENY"
        
        # 内容安全策略
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # HSTS (仅在HTTPS环境下)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # 引用策略
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 权限策略
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
    
    def record_failed_attempt(self, client_ip: str):
        """记录失败尝试"""
        current_time = time.time()
        
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []
        
        self.failed_attempts[client_ip].append(current_time)
        
        # 清理过期记录（1小时）
        self.failed_attempts[client_ip] = [
            t for t in self.failed_attempts[client_ip]
            if current_time - t < 3600
        ]
        
        # 如果失败次数过多，阻止IP
        if len(self.failed_attempts[client_ip]) >= 10:
            self.blocked_ips[client_ip] = current_time + 3600  # 阻止1小时
            logger.warning(f"IP {client_ip} blocked due to too many failed attempts")
    
    def is_ip_blocked(self, client_ip: str) -> bool:
        """检查IP是否被阻止"""
        if client_ip in self.blocked_ips:
            if time.time() < self.blocked_ips[client_ip]:
                return True
            else:
                # 解除阻止
                del self.blocked_ips[client_ip]
        return False


class CSRFProtection:
    """CSRF保护类"""
    
    def __init__(self):
        self.tokens: Dict[str, float] = {}
        self.token_lifetime = 3600  # 1小时
    
    def generate_token(self, session_id: str) -> str:
        """生成CSRF令牌"""
        token = secrets.token_urlsafe(32)
        self.tokens[token] = time.time()
        return token
    
    def validate_token(self, token: str) -> bool:
        """验证CSRF令牌"""
        if not token or token not in self.tokens:
            return False
        
        # 检查令牌是否过期
        if time.time() - self.tokens[token] > self.token_lifetime:
            del self.tokens[token]
            return False
        
        return True
    
    def cleanup_expired_tokens(self):
        """清理过期令牌"""
        current_time = time.time()
        expired_tokens = [
            token for token, timestamp in self.tokens.items()
            if current_time - timestamp > self.token_lifetime
        ]
        
        for token in expired_tokens:
            del self.tokens[token]


class XSSProtection:
    """XSS保护类"""
    
    @staticmethod
    def sanitize_input(data: any) -> any:
        """清理输入数据，防止XSS攻击"""
        if isinstance(data, str):
            return XSSProtection._sanitize_string(data)
        elif isinstance(data, dict):
            return {key: XSSProtection.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [XSSProtection.sanitize_input(item) for item in data]
        else:
            return data
    
    @staticmethod
    def _sanitize_string(text: str) -> str:
        """清理字符串"""
        if not text:
            return text
        
        # 移除或转义危险字符
        dangerous_chars = {
            '&': '&amp;',  # 必须先处理&符号
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;'
        }
        
        for char, replacement in dangerous_chars.items():
            text = text.replace(char, replacement)
        
        return text


class InputSanitizer:
    """输入清理器"""
    
    @staticmethod
    def sanitize_json_input(request_data: dict) -> dict:
        """清理JSON输入数据"""
        sanitized = {}
        
        for key, value in request_data.items():
            # 清理键名
            clean_key = InputSanitizer._clean_key(key)
            
            # 清理值
            if isinstance(value, str):
                sanitized[clean_key] = XSSProtection._sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[clean_key] = InputSanitizer.sanitize_json_input(value)
            elif isinstance(value, list):
                sanitized[clean_key] = [
                    XSSProtection._sanitize_string(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[clean_key] = value
        
        return sanitized
    
    @staticmethod
    def _clean_key(key: str) -> str:
        """清理字典键名"""
        # 只允许字母、数字、下划线
        import re
        return re.sub(r'[^a-zA-Z0-9_]', '', key)


class SecurityLogger:
    """安全日志记录器"""
    
    def __init__(self):
        self.logger = logging.getLogger("security")
        
        # 配置安全日志处理器
        handler = logging.FileHandler("logs/security.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_security_event(self, event_type: str, client_ip: str, details: dict):
        """记录安全事件"""
        log_data = {
            "event_type": event_type,
            "client_ip": client_ip,
            "timestamp": time.time(),
            "details": details
        }
        
        self.logger.info(json.dumps(log_data))
    
    def log_failed_login(self, username: str, client_ip: str):
        """记录登录失败"""
        self.log_security_event("failed_login", client_ip, {
            "username": username,
            "action": "login_attempt"
        })
    
    def log_suspicious_activity(self, client_ip: str, activity: str, details: dict):
        """记录可疑活动"""
        self.log_security_event("suspicious_activity", client_ip, {
            "activity": activity,
            **details
        })
    
    def log_rate_limit_exceeded(self, client_ip: str):
        """记录速率限制超出"""
        self.log_security_event("rate_limit_exceeded", client_ip, {
            "action": "rate_limit_check"
        })


# 全局实例
csrf_protection = CSRFProtection()
security_logger = SecurityLogger()


async def validate_csrf_token(request: Request):
    """CSRF令牌验证依赖"""
    # 对于GET请求不需要CSRF验证
    if request.method == "GET":
        return True
    
    token = request.headers.get("X-CSRF-Token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="缺少CSRF令牌"
        )
    
    if not csrf_protection.validate_token(token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无效的CSRF令牌"
        )
    
    return True


def get_csrf_token() -> str:
    """获取CSRF令牌"""
    return csrf_protection.generate_token("session")