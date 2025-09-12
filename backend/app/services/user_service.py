"""
用户管理服务
处理用户管理相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.models.user import User, UserRole, UserTheme
from app.core.security import validate_password_strength
import logging

logger = logging.getLogger(__name__)


class UserService:
    """用户管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def get_users(self, skip: int = 0, limit: int = 100, 
                  active_only: bool = True, role_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        获取用户列表
        
        Args:
            skip: 跳过的记录数
            limit: 限制返回的记录数
            active_only: 是否只返回活跃用户
            role_filter: 角色过滤器
        
        Returns:
            Dict[str, Any]: 包含用户列表和总数的字典
        """
        try:
            # 获取用户列表
            users = self.user_repo.get_all(skip=skip, limit=limit, active_only=active_only)
            
            # 如果有角色过滤器，进行过滤
            if role_filter:
                try:
                    filter_role = UserRole(role_filter)
                    users = [user for user in users if user.role == filter_role]
                except ValueError:
                    logger.warning(f"Invalid role filter: {role_filter}")
            
            # 转换为响应格式
            user_list = []
            for user in users:
                user_list.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.value,
                    "theme": user.theme.value,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                })
            
            # 获取总数
            total = self.user_repo.count(active_only=active_only)
            
            return {
                "users": user_list,
                "total": total,
                "skip": skip,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户列表失败"
            )
    
    def get_user_by_id(self, user_id: int) -> Dict[str, Any]:
        """
        根据ID获取用户详情
        
        Args:
            user_id: 用户ID
        
        Returns:
            Dict[str, Any]: 用户详情
        
        Raises:
            HTTPException: 用户不存在时抛出404错误
        """
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "theme": user.theme.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    
    def create_user(self, username: str, password: str, email: Optional[str] = None,
                   role: str = "user") -> Dict[str, Any]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱地址
            role: 用户角色
        
        Returns:
            Dict[str, Any]: 创建的用户信息
        
        Raises:
            HTTPException: 创建失败时抛出错误
        """
        # 验证用户名
        if len(username) < 3 or len(username) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名长度必须在3-50个字符之间"
            )
        
        # 验证密码强度
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 验证角色
        try:
            user_role = UserRole(role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的用户角色"
            )
        
        # 检查用户名是否已存在
        if self.user_repo.get_by_username(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        # 检查邮箱是否已存在
        if email and self.user_repo.get_by_email(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱地址已存在"
            )
        
        # 创建用户
        user = self.user_repo.create(
            username=username,
            password=password,
            email=email,
            role=user_role
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户失败"
            )
        
        logger.info(f"User {username} created successfully by admin")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "theme": user.theme.value,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    
    def update_user(self, user_id: int, username: Optional[str] = None,
                   email: Optional[str] = None, role: Optional[str] = None,
                   theme: Optional[str] = None, is_active: Optional[bool] = None) -> Dict[str, Any]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱地址
            role: 用户角色
            theme: 主题设置
            is_active: 是否激活
        
        Returns:
            Dict[str, Any]: 更新后的用户信息
        
        Raises:
            HTTPException: 更新失败时抛出错误
        """
        # 检查用户是否存在
        existing_user = self.user_repo.get_by_id(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 准备更新数据
        update_data = {}
        
        # 验证并设置用户名
        if username is not None:
            if len(username) < 3 or len(username) > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名长度必须在3-50个字符之间"
                )
            
            # 检查用户名是否已被其他用户使用
            existing_username_user = self.user_repo.get_by_username(username)
            if existing_username_user and existing_username_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
            
            # 注意：用户名更新需要特殊处理，因为repository中没有直接支持
            # 这里我们需要手动更新
            existing_user.username = username
        
        # 验证并设置邮箱
        if email is not None:
            # 检查邮箱是否已被其他用户使用
            existing_email_user = self.user_repo.get_by_email(email)
            if existing_email_user and existing_email_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱地址已存在"
                )
            update_data['email'] = email
        
        # 验证并设置角色
        if role is not None:
            try:
                user_role = UserRole(role)
                update_data['role'] = user_role
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的用户角色"
                )
        
        # 验证并设置主题
        if theme is not None:
            try:
                user_theme = UserTheme(theme)
                update_data['theme'] = user_theme
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的主题设置"
                )
        
        # 设置激活状态
        if is_active is not None:
            update_data['is_active'] = is_active
        
        # 执行更新
        try:
            if username is not None:
                # 如果更新了用户名，需要手动提交
                self.db.commit()
                self.db.refresh(existing_user)
            
            if update_data:
                updated_user = self.user_repo.update(user_id, **update_data)
                if not updated_user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="更新用户失败"
                    )
            else:
                updated_user = existing_user
            
            logger.info(f"User {user_id} updated successfully")
            
            return {
                "id": updated_user.id,
                "username": updated_user.username,
                "email": updated_user.email,
                "role": updated_user.role.value,
                "theme": updated_user.theme.value,
                "is_active": updated_user.is_active,
                "updated_at": updated_user.updated_at.isoformat() if updated_user.updated_at else None
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户失败"
            )
    
    def delete_user(self, user_id: int, current_user_id: int) -> bool:
        """
        删除用户
        
        Args:
            user_id: 要删除的用户ID
            current_user_id: 当前操作用户ID
        
        Returns:
            bool: 删除成功返回True
        
        Raises:
            HTTPException: 删除失败时抛出错误
        """
        # 检查用户是否存在
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 防止用户删除自己
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己的账号"
            )
        
        # 执行删除
        success = self.user_repo.delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除用户失败"
            )
        
        logger.info(f"User {user_id} deleted successfully by user {current_user_id}")
        return True
    
    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """
        重置用户密码（管理员功能）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
        
        Returns:
            bool: 重置成功返回True
        
        Raises:
            HTTPException: 重置失败时抛出错误
        """
        # 检查用户是否存在
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证新密码强度
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 重置密码
        success = self.user_repo.update_password(user_id, new_password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="重置密码失败"
            )
        
        logger.info(f"Password reset for user {user_id} by admin")
        return True
    
    def toggle_user_status(self, user_id: int, current_user_id: int) -> Dict[str, Any]:
        """
        切换用户激活状态
        
        Args:
            user_id: 用户ID
            current_user_id: 当前操作用户ID
        
        Returns:
            Dict[str, Any]: 更新后的用户信息
        
        Raises:
            HTTPException: 操作失败时抛出错误
        """
        # 检查用户是否存在
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 防止用户停用自己
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能停用自己的账号"
            )
        
        # 切换状态
        new_status = not user.is_active
        updated_user = self.user_repo.update(user_id, is_active=new_status)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户状态失败"
            )
        
        action = "激活" if new_status else "停用"
        logger.info(f"User {user_id} {action} by user {current_user_id}")
        
        return {
            "id": updated_user.id,
            "username": updated_user.username,
            "is_active": updated_user.is_active,
            "message": f"用户已{action}"
        }
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        获取用户统计信息
        
        Returns:
            Dict[str, Any]: 用户统计数据
        """
        try:
            total_users = self.user_repo.count(active_only=False)
            active_users = self.user_repo.count(active_only=True)
            inactive_users = total_users - active_users
            
            # 按角色统计
            all_users = self.user_repo.get_all(skip=0, limit=1000, active_only=False)
            role_stats = {}
            
            # 初始化所有角色计数为0
            for role in UserRole:
                role_stats[role.value] = 0
            
            # 统计每个用户的角色
            for user in all_users:
                user_role = user.role
                # 处理角色可能是枚举对象或字符串的情况
                if isinstance(user_role, UserRole):
                    role_key = user_role.value
                else:
                    role_key = str(user_role)
                
                if role_key in role_stats:
                    role_stats[role_key] += 1
                else:
                    # 如果遇到未知角色，也记录下来
                    role_stats[role_key] = 1
            
            logger.info(f"User statistics: total={total_users}, active={active_users}, roles={role_stats}")
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "role_distribution": role_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取用户统计信息失败"
            )