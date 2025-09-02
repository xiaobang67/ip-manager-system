"""
认证服务
处理用户认证、token生成和验证等业务逻辑
"""
from typing import Optional, Tuple
from datetime import timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.core.security import (
    create_access_token, 
    create_refresh_token, 
    verify_token,
    validate_password_strength
)
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            User: 认证成功返回用户对象，失败返回None
        """
        return self.user_repo.authenticate(username, password)
    
    def login(self, username: str, password: str) -> Tuple[str, str, dict]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
        
        Returns:
            Tuple[str, str, dict]: (access_token, refresh_token, user_info)
        
        Raises:
            HTTPException: 认证失败时抛出异常
        """
        # 认证用户
        user = self.authenticate_user(username, password)
        if not user:
            logger.warning(f"Login failed for username: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成token数据
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value
        }
        
        # 生成访问令牌和刷新令牌
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)
        
        # 用户信息
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "theme": user.theme.value,
            "is_active": user.is_active
        }
        
        logger.info(f"User {username} logged in successfully")
        return access_token, refresh_token, user_info
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            str: 新的访问令牌
        
        Raises:
            HTTPException: 刷新令牌无效时抛出异常
        """
        # 验证刷新令牌
        payload = verify_token(refresh_token, token_type="refresh")
        if not payload:
            logger.warning("Invalid refresh token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户信息
        user_id = int(payload.get("sub"))
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            logger.warning(f"User {user_id} not found or inactive during token refresh")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被停用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 生成新的访问令牌
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role.value
        }
        
        new_access_token = create_access_token(data=token_data)
        
        logger.info(f"Access token refreshed for user {user.username}")
        return new_access_token
    
    def get_current_user(self, token: str) -> User:
        """
        根据访问令牌获取当前用户
        
        Args:
            token: 访问令牌
        
        Returns:
            User: 当前用户对象
        
        Raises:
            HTTPException: 令牌无效或用户不存在时抛出异常
        """
        # 验证访问令牌
        payload = verify_token(token, token_type="access")
        if not payload:
            logger.warning("Invalid access token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 获取用户信息
        user_id = int(payload.get("sub"))
        user = self.user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found during token validation")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Inactive user {user_id} attempted to access with valid token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户已被停用",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改用户密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            bool: 修改成功返回True
        
        Raises:
            HTTPException: 验证失败时抛出异常
        """
        # 获取用户
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证旧密码
        if not self.user_repo.authenticate(user.username, old_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码错误"
            )
        
        # 验证新密码强度
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 更新密码
        success = self.user_repo.update_password(user_id, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="密码更新失败"
            )
        
        logger.info(f"Password changed successfully for user {user_id}")
        return True
    
    def update_profile(self, user_id: int, email: Optional[str] = None, 
                      theme: Optional[str] = None) -> dict:
        """
        更新用户个人信息
        
        Args:
            user_id: 用户ID
            email: 邮箱地址
            theme: 主题设置
        
        Returns:
            dict: 更新后的用户信息
        
        Raises:
            HTTPException: 更新失败时抛出异常
        """
        # 准备更新数据
        update_data = {}
        if email is not None:
            update_data['email'] = email
        if theme is not None:
            update_data['theme'] = theme
        
        # 更新用户信息
        user = self.user_repo.update(user_id, **update_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在或更新失败"
            )
        
        # 返回更新后的用户信息
        user_info = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "theme": user.theme.value,
            "is_active": user.is_active
        }
        
        logger.info(f"Profile updated successfully for user {user_id}")
        return user_info
    
    def logout(self, token: str) -> bool:
        """
        用户登出
        注意：由于JWT是无状态的，这里主要是记录日志
        实际的token失效需要在客户端处理或使用token黑名单机制
        
        Args:
            token: 访问令牌
        
        Returns:
            bool: 登出成功返回True
        """
        try:
            # 验证token并获取用户信息用于日志记录
            payload = verify_token(token, token_type="access")
            if payload:
                username = payload.get("username", "unknown")
                logger.info(f"User {username} logged out successfully")
            else:
                logger.info("Logout attempt with invalid token")
            
            return True
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False