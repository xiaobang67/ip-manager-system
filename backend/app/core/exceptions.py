"""
自定义异常类和全局错误处理
"""
import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time

logger = logging.getLogger(__name__)


class IPAMException(Exception):
    """IPAM系统基础异常"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(IPAMException):
    """数据验证异常"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class NotFoundError(IPAMException):
    """资源不存在异常"""
    def __init__(self, resource: str, identifier: Any = None):
        message = f"{resource}不存在"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class ConflictError(IPAMException):
    """资源冲突异常"""
    def __init__(self, message: str, conflicting_resource: str = None):
        super().__init__(message, "CONFLICT")
        self.conflicting_resource = conflicting_resource


class AuthenticationError(IPAMException):
    """认证异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, "AUTHENTICATION_ERROR")


class AuthorizationError(IPAMException):
    """授权异常"""
    def __init__(self, message: str = "权限不足", required_permission: str = None):
        super().__init__(message, "AUTHORIZATION_ERROR")
        self.required_permission = required_permission


class DatabaseError(IPAMException):
    """数据库异常"""
    def __init__(self, message: str, operation: str = None):
        super().__init__(message, "DATABASE_ERROR")
        self.operation = operation


class BusinessLogicError(IPAMException):
    """业务逻辑异常"""
    def __init__(self, message: str, business_rule: str = None):
        super().__init__(message, "BUSINESS_LOGIC_ERROR")
        self.business_rule = business_rule


class SecurityError(IPAMException):
    """安全异常"""
    def __init__(self, message: str, security_issue: str = None):
        super().__init__(message, "SECURITY_ERROR")
        self.security_issue = security_issue


class RateLimitError(IPAMException):
    """速率限制异常"""
    def __init__(self, message: str = "请求过于频繁"):
        super().__init__(message, "RATE_LIMIT_ERROR")


class ExternalServiceError(IPAMException):
    """外部服务异常"""
    def __init__(self, message: str, service: str = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.service = service


class ErrorHandler:
    """全局错误处理器"""
    
    def __init__(self):
        self.error_logger = logging.getLogger("error_handler")
        self.setup_logger()
    
    def setup_logger(self):
        """设置错误日志记录器"""
        handler = logging.FileHandler("logs/errors.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.error_logger.addHandler(handler)
        self.error_logger.setLevel(logging.ERROR)
    
    def log_error(self, error: Exception, request: Request = None, extra_info: Dict[str, Any] = None):
        """记录错误信息"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time(),
            "traceback": traceback.format_exc()
        }
        
        if request:
            error_info.update({
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            })
        
        if extra_info:
            error_info.update(extra_info)
        
        self.error_logger.error(f"Error occurred: {error_info}")
    
    async def handle_ipam_exception(self, request: Request, exc: IPAMException) -> JSONResponse:
        """处理IPAM自定义异常"""
        self.log_error(exc, request)
        
        status_code_map = {
            "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "NOT_FOUND": status.HTTP_404_NOT_FOUND,
            "CONFLICT": status.HTTP_409_CONFLICT,
            "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
            "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
            "DATABASE_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "BUSINESS_LOGIC_ERROR": status.HTTP_400_BAD_REQUEST,
            "SECURITY_ERROR": status.HTTP_403_FORBIDDEN,
            "RATE_LIMIT_ERROR": status.HTTP_429_TOO_MANY_REQUESTS,
            "EXTERNAL_SERVICE_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        
        status_code = status_code_map.get(exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "timestamp": time.time()
                }
            }
        )
    
    async def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """处理FastAPI验证错误"""
        self.log_error(exc, request)
        
        errors = []
        for error in exc.errors():
            field_path = " -> ".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field_path,
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "请求数据验证失败",
                    "details": {"validation_errors": errors},
                    "timestamp": time.time()
                }
            }
        )
    
    async def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """处理HTTP异常"""
        self.log_error(exc, request)
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "timestamp": time.time()
                }
            }
        )
    
    async def handle_generic_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """处理通用异常"""
        self.log_error(exc, request)
        
        # 在生产环境中不暴露详细错误信息
        from app.core.config import settings
        
        if settings.ENVIRONMENT == "development":
            error_detail = str(exc)
        else:
            error_detail = "服务器内部错误"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": error_detail,
                    "timestamp": time.time()
                }
            }
        )


# 全局错误处理器实例
error_handler = ErrorHandler()


# 异常处理函数
async def ipam_exception_handler(request: Request, exc: IPAMException) -> JSONResponse:
    """IPAM异常处理器"""
    return await error_handler.handle_ipam_exception(request, exc)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """验证异常处理器"""
    return await error_handler.handle_validation_error(request, exc)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    return await error_handler.handle_http_exception(request, exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    return await error_handler.handle_generic_exception(request, exc)


class ErrorResponse:
    """标准错误响应格式"""
    
    @staticmethod
    def create_error_response(
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """创建标准错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or {},
                    "timestamp": time.time()
                }
            }
        )
    
    @staticmethod
    def validation_error(message: str, field_errors: list = None) -> JSONResponse:
        """验证错误响应"""
        return ErrorResponse.create_error_response(
            code="VALIDATION_ERROR",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field_errors": field_errors or []}
        )
    
    @staticmethod
    def not_found_error(resource: str, identifier: Any = None) -> JSONResponse:
        """资源不存在错误响应"""
        message = f"{resource}不存在"
        if identifier:
            message += f": {identifier}"
        
        return ErrorResponse.create_error_response(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    @staticmethod
    def conflict_error(message: str) -> JSONResponse:
        """冲突错误响应"""
        return ErrorResponse.create_error_response(
            code="CONFLICT",
            message=message,
            status_code=status.HTTP_409_CONFLICT
        )
    
    @staticmethod
    def unauthorized_error(message: str = "认证失败") -> JSONResponse:
        """未授权错误响应"""
        return ErrorResponse.create_error_response(
            code="UNAUTHORIZED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )
    
    @staticmethod
    def forbidden_error(message: str = "权限不足") -> JSONResponse:
        """禁止访问错误响应"""
        return ErrorResponse.create_error_response(
            code="FORBIDDEN",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )
    
    @staticmethod
    def rate_limit_error(message: str = "请求过于频繁") -> JSONResponse:
        """速率限制错误响应"""
        return ErrorResponse.create_error_response(
            code="RATE_LIMIT_EXCEEDED",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )
    
    @staticmethod
    def server_error(message: str = "服务器内部错误") -> JSONResponse:
        """服务器错误响应"""
        return ErrorResponse.create_error_response(
            code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )