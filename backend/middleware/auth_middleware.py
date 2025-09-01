"""
JWT认证中间件
"""
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging
from typing import List

from services.auth_service import auth_service
from database.connection import SessionLocal

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT认证中间件
    自动验证需要认证的路径
    """
    
    # 不需要认证的路径
    EXCLUDED_PATHS = [
        "/",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/health",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/dashboard/stats",
        "/api/v1/dashboard/recent-activities",
    ]
    
    # 需要认证的路径前缀
    PROTECTED_PREFIXES = [
        "/api/v1/departments",
        "/api/v1/users", 
        "/api/v1/network-segments",
        "/api/v1/ip-addresses",
        "/api/v1/reserved-addresses",
        "/api/v1/auth/me",
        "/api/v1/auth/logout",
        "/api/v1/auth/change-password",
        "/api/v1/auth/users",
        "/api/v1/auth/groups",
        "/api/v1/auth/stats",
    ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 检查是否需要认证
        if self._is_protected_path(path):
            # 验证JWT令牌
            auth_result = await self._verify_jwt_token(request)
            if auth_result["success"]:
                # 将用户信息添加到请求中
                request.state.current_user = auth_result["user"]
                request.state.user_id = auth_result["user"].id
                request.state.username = auth_result["user"].username
            else:
                return JSONResponse(
                    status_code=401,
                    content={
                        "success": False,
                        "message": auth_result["message"],
                        "code": 401
                    }
                )
        
        response = await call_next(request)
        return response

    def _is_protected_path(self, path: str) -> bool:
        """检查路径是否需要认证"""
        # 如果是仪表盘相关API，不需要认证
        if path.startswith("/api/v1/dashboard"):
            return False
            
        # 检查排除路径
        for excluded_path in self.EXCLUDED_PATHS:
            if path == excluded_path or path.startswith(excluded_path + "/"):
                return False
        
        # 检查保护路径前缀
        for prefix in self.PROTECTED_PREFIXES:
            if path.startswith(prefix):
                return True
                
        return False

    async def _verify_jwt_token(self, request: Request) -> dict:
        """验证JWT令牌"""
        try:
            # 获取Authorization头
            authorization = request.headers.get("Authorization")
            if not authorization:
                return {
                    "success": False,
                    "message": "缺少认证令牌"
                }
            
            # 检查Bearer格式
            if not authorization.startswith("Bearer "):
                return {
                    "success": False,
                    "message": "无效的认证格式"
                }
            
            # 提取令牌（去掉"Bearer "前缀）
            token = authorization[7:]
            
            # 验证令牌并获取用户
            db = SessionLocal()
            try:
                user = auth_service.get_user_by_token(db, token)
                if not user:
                    return {
                        "success": False,
                        "message": "无效的认证令牌"
                    }
                
                if not user.is_active:
                    return {
                        "success": False,
                        "message": "用户账户已被禁用"
                    }
                
                return {
                    "success": True,
                    "user": user
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"JWT令牌验证错误: {e}")
            return {
                "success": False,
                "message": "令牌验证失败"
            }


# 可选的装饰器方式（如果不使用中间件）
from functools import wraps
from fastapi import Depends
from sqlalchemy.orm import Session
from database.connection import get_db

security = HTTPBearer()

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # 这里可以添加额外的认证逻辑
        return await f(*args, **kwargs)
    return wrapper

def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # 从kwargs中获取current_user
        current_user = kwargs.get('current_user')
        if not current_user or not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理员权限"
            )
        return await f(*args, **kwargs)
    return wrapper

def require_superuser(f):
    """超级用户权限装饰器"""
    @wraps(f)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user or not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要超级用户权限"
            )
        return await f(*args, **kwargs)
    return wrapper

# 权限检查函数
def check_permission(user, required_permission: str) -> bool:
    """检查用户权限"""
    if user.is_superuser:
        return True
    
    if required_permission == "admin" and user.is_admin:
        return True
    
    # 这里可以添加更复杂的权限逻辑
    # 比如基于用户组的权限检查
    
    return False

def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """从令牌获取当前用户的依赖函数"""
    token = credentials.credentials
    user = auth_service.get_user_by_token(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_admin_user(current_user=Depends(get_current_user_from_token)):
    """获取当前管理员用户的依赖函数"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

def get_current_superuser(current_user=Depends(get_current_user_from_token)):
    """获取当前超级用户的依赖函数"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级用户权限"
        )
    return current_user