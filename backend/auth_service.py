#!/usr/bin/env python3
"""
统一认证服务
确保所有密码操作都使用bcrypt哈希格式
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
from typing import Optional, Dict, Any
from app.core.security import verify_password, get_password_hash
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthService:
    """统一认证服务类"""
    
    def __init__(self):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'ipam_user'),
            'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
            'database': os.getenv('DB_NAME', 'ipam'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    def get_db_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 明文密码
            
        Returns:
            用户信息字典，认证失败返回None
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 查询用户
                cursor.execute(
                    "SELECT id, username, password_hash, email, role, is_active FROM users WHERE username = %s AND is_active = TRUE",
                    (username,)
                )
                user = cursor.fetchone()
                
                if not user:
                    logger.warning(f"用户不存在或已禁用: {username}")
                    return None
                
                # 验证密码
                if not verify_password(password, user['password_hash']):
                    logger.warning(f"密码验证失败: {username}")
                    return None
                
                logger.info(f"用户认证成功: {username}")
                return {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role'],
                    'is_active': user['is_active']
                }
        except Exception as e:
            logger.error(f"认证过程中发生错误: {e}")
            return None
        finally:
            connection.close()
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        修改用户密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            修改成功返回True，否则返回False
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 获取当前用户信息
                cursor.execute(
                    "SELECT id, username, password_hash FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cursor.fetchone()
                
                if not user:
                    logger.error(f"用户不存在: {user_id}")
                    return False
                
                # 验证旧密码
                if not verify_password(old_password, user['password_hash']):
                    logger.warning(f"旧密码验证失败: {user['username']}")
                    return False
                
                # 生成新密码哈希
                new_password_hash = get_password_hash(new_password)
                
                # 更新密码
                cursor.execute(
                    "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                    (new_password_hash, user_id)
                )
                connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"密码修改成功: {user['username']}")
                    return True
                else:
                    logger.error(f"密码更新失败: {user['username']}")
                    return False
                    
        except Exception as e:
            logger.error(f"修改密码过程中发生错误: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()
    
    def reset_password(self, username: str, new_password: str) -> bool:
        """
        重置用户密码（管理员操作）
        
        Args:
            username: 用户名
            new_password: 新密码
            
        Returns:
            重置成功返回True，否则返回False
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 生成新密码哈希
                new_password_hash = get_password_hash(new_password)
                
                # 更新密码
                cursor.execute(
                    "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s",
                    (new_password_hash, username)
                )
                connection.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"密码重置成功: {username}")
                    return True
                else:
                    logger.error(f"用户不存在: {username}")
                    return False
                    
        except Exception as e:
            logger.error(f"重置密码过程中发生错误: {e}")
            connection.rollback()
            return False
        finally:
            connection.close()
    
    def create_user(self, username: str, password: str, email: str = None, role: str = "user") -> Optional[int]:
        """
        创建新用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            role: 角色
            
        Returns:
            创建成功返回用户ID，否则返回None
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                # 检查用户名是否已存在
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    logger.error(f"用户名已存在: {username}")
                    return None
                
                # 生成密码哈希
                password_hash = get_password_hash(password)
                
                # 创建用户
                cursor.execute(
                    """
                    INSERT INTO users (username, password_hash, email, role, is_active, created_at)
                    VALUES (%s, %s, %s, %s, TRUE, CURRENT_TIMESTAMP)
                    """,
                    (username, password_hash, email, role)
                )
                connection.commit()
                
                user_id = cursor.lastrowid
                logger.info(f"用户创建成功: {username} (ID: {user_id})")
                return user_id
                
        except Exception as e:
            logger.error(f"创建用户过程中发生错误: {e}")
            connection.rollback()
            return None
        finally:
            connection.close()
    
    def verify_user_password(self, username: str, password: str) -> bool:
        """
        验证用户密码
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            验证成功返回True，否则返回False
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT password_hash FROM users WHERE username = %s AND is_active = TRUE",
                    (username,)
                )
                user = cursor.fetchone()
                
                if not user:
                    return False
                
                return verify_password(password, user['password_hash'])
                
        except Exception as e:
            logger.error(f"验证密码过程中发生错误: {e}")
            return False
        finally:
            connection.close()
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典，不存在返回None
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, role, is_active, created_at FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"获取用户信息过程中发生错误: {e}")
            return None
        finally:
            connection.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息字典，不存在返回None
        """
        connection = self.get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, email, role, is_active, created_at FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cursor.fetchone()
                return user
        except Exception as e:
            logger.error(f"获取用户信息过程中发生错误: {e}")
            return None
        finally:
            connection.close()

# 全局认证服务实例
auth_service = AuthService()

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """认证用户的便捷函数"""
    return auth_service.authenticate_user(username, password)

def change_user_password(user_id: int, old_password: str, new_password: str) -> bool:
    """修改用户密码的便捷函数"""
    return auth_service.change_password(user_id, old_password, new_password)

def reset_user_password(username: str, new_password: str) -> bool:
    """重置用户密码的便捷函数"""
    return auth_service.reset_password(username, new_password)

def create_new_user(username: str, password: str, email: str = None, role: str = "user") -> Optional[int]:
    """创建新用户的便捷函数"""
    return auth_service.create_user(username, password, email, role)

if __name__ == "__main__":
    # 测试认证服务
    print("=== 测试认证服务 ===")
    
    # 测试用户认证
    user = authenticate_user("admin", "admin")
    if user:
        print(f"✅ 用户认证成功: {user}")
    else:
        print("❌ 用户认证失败")
    
    # 测试密码验证
    if auth_service.verify_user_password("admin", "admin"):
        print("✅ 密码验证成功")
    else:
        print("❌ 密码验证失败")