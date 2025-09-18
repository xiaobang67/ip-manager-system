"""
FastAPI依赖注入模块
包含认证和权限验证的依赖项
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user import User, UserRole
import logging

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    获取认证服务实例
    
    Args:
        db: 数据库会话
    
    Returns:
        AuthService: 认证服务实例
    """
    return AuthService(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    获取当前认证用户
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务
    
    Returns:
        User: 当前用户对象
    
    Raises:
        HTTPException: 认证失败时抛出异常
    """
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_current_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 当前活跃用户对象
    
    Raises:
        HTTPException: 用户未激活时抛出异常
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户已被停用"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    角色权限装饰器工厂
    
    Args:
        required_role: 所需的用户角色
    
    Returns:
        function: 权限检查依赖函数
    """
    def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        """
        检查用户角色权限
        
        Args:
            current_user: 当前用户
        
        Returns:
            User: 有权限的用户对象
        
        Raises:
            HTTPException: 权限不足时抛出异常
        """
        # 定义角色层级
        role_hierarchy = {
            UserRole.READONLY: 0,
            UserRole.USER: 1,
            UserRole.MANAGER: 2,
            UserRole.ADMIN: 3
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 999)
        
        if user_level < required_level:
            logger.warning(
                f"User {current_user.username} (role: {current_user.role}) "
                f"attempted to access resource requiring role: {required_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        
        return current_user
    
    return check_role


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    要求管理员权限
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 管理员用户对象
    
    Raises:
        HTTPException: 非管理员时抛出异常
    """
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            f"User {current_user.username} (role: {current_user.role}) "
            f"attempted to access admin-only resource"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


def require_manager_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """
    要求管理员或经理权限
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 有权限的用户对象
    
    Raises:
        HTTPException: 权限不足时抛出异常
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER]:
        logger.warning(
            f"User {current_user.username} (role: {current_user.role}) "
            f"attempted to access manager/admin resource"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员或经理权限"
        )
    return current_user


def require_write_permission(current_user: User = Depends(get_current_active_user)) -> User:
    """
    要求写权限（非只读用户）
    
    Args:
        current_user: 当前用户
    
    Returns:
        User: 有写权限的用户对象
    
    Raises:
        HTTPException: 只读用户时抛出异常
    """
    if current_user.role == UserRole.READONLY:
        logger.warning(
            f"User {current_user.username} (role: {current_user.role}) "
            f"attempted to access write operation"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只读用户无法执行此操作"
        )
    return current_user


# 可选的用户依赖（不强制认证）
def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    获取可选的当前用户（不强制认证）
    
    Args:
        credentials: HTTP认证凭据（可选）
        auth_service: 认证服务
    
    Returns:
        Optional[User]: 当前用户对象，未认证时返回None
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user = auth_service.get_current_user(token)
        return user
    except HTTPException:
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_optional_user: {e}")
        return None