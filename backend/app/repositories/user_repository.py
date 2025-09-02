"""
用户数据访问层
实现用户相关的数据库操作
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User, UserRole, UserTheme
from app.core.security import get_password_hash, verify_password
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """
        根据ID获取用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            User: 用户对象，不存在返回None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
        
        Returns:
            User: 用户对象，不存在返回None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        根据邮箱获取用户
        
        Args:
            email: 邮箱地址
        
        Returns:
            User: 用户对象，不存在返回None
        """
        return self.db.query(User).filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[User]:
        """
        获取用户列表
        
        Args:
            skip: 跳过的记录数
            limit: 限制返回的记录数
            active_only: 是否只返回活跃用户
        
        Returns:
            List[User]: 用户列表
        """
        query = self.db.query(User)
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, username: str, password: str, email: Optional[str] = None, 
               role: UserRole = UserRole.USER) -> Optional[User]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 明文密码
            email: 邮箱地址
            role: 用户角色
        
        Returns:
            User: 创建的用户对象，创建失败返回None
        """
        try:
            # 检查用户名是否已存在
            if self.get_by_username(username):
                logger.warning(f"Username '{username}' already exists")
                return None
            
            # 检查邮箱是否已存在
            if email and self.get_by_email(email):
                logger.warning(f"Email '{email}' already exists")
                return None
            
            # 创建用户对象
            user = User(
                username=username,
                password_hash=get_password_hash(password),
                email=email,
                role=role,
                theme=UserTheme.LIGHT,
                is_active=True
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User '{username}' created successfully with ID {user.id}")
            return user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Failed to create user '{username}': {e}")
            return None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating user '{username}': {e}")
            return None
    
    def update(self, user_id: int, **kwargs) -> Optional[User]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段
        
        Returns:
            User: 更新后的用户对象，更新失败返回None
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return None
            
            # 更新允许的字段
            allowed_fields = ['email', 'role', 'theme', 'is_active']
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User {user_id} updated successfully")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user {user_id}: {e}")
            return None
    
    def update_password(self, user_id: int, new_password: str) -> bool:
        """
        更新用户密码
        
        Args:
            user_id: 用户ID
            new_password: 新密码（明文）
        
        Returns:
            bool: 更新成功返回True，失败返回False
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False
            
            user.password_hash = get_password_hash(new_password)
            self.db.commit()
            
            logger.info(f"Password updated for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update password for user {user_id}: {e}")
            return False
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 明文密码
        
        Returns:
            User: 认证成功返回用户对象，失败返回None
        """
        user = self.get_by_username(username)
        
        if not user:
            logger.warning(f"Authentication failed: user '{username}' not found")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user '{username}' is inactive")
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: invalid password for user '{username}'")
            return None
        
        logger.info(f"User '{username}' authenticated successfully")
        return user
    
    def deactivate(self, user_id: int) -> bool:
        """
        停用用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        return self.update(user_id, is_active=False) is not None
    
    def activate(self, user_id: int) -> bool:
        """
        激活用户
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 操作成功返回True，失败返回False
        """
        return self.update(user_id, is_active=True) is not None
    
    def delete(self, user_id: int) -> bool:
        """
        删除用户（物理删除）
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 删除成功返回True，失败返回False
        """
        try:
            user = self.get_by_id(user_id)
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False
            
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"User {user_id} deleted successfully")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete user {user_id}: {e}")
            return False
    
    def count(self, active_only: bool = True) -> int:
        """
        获取用户总数
        
        Args:
            active_only: 是否只统计活跃用户
        
        Returns:
            int: 用户总数
        """
        query = self.db.query(User)
        
        if active_only:
            query = query.filter(User.is_active == True)
        
        return query.count()