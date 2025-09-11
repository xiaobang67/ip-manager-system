"""
统一认证服务接口
确保所有认证操作使用相同的实现
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class AuthServiceInterface(ABC):
    """认证服务接口"""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        pass
    
    @abstractmethod
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        pass
    
    @abstractmethod
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """重置密码"""
        pass
    
    @abstractmethod
    def verify_password(self, username: str, password: str) -> bool:
        """验证密码"""
        pass
