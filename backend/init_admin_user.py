#!/usr/bin/env python3
"""
初始化管理员用户脚本
用于创建系统的第一个管理员用户
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User, UserRole, UserTheme
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user():
    """创建管理员用户"""
    db: Session = SessionLocal()
    
    try:
        # 检查是否已存在管理员用户
        existing_admin = db.query(User).filter(User.role == "admin").first()
        if existing_admin:
            logger.info(f"管理员用户已存在: {existing_admin.username}")
            return existing_admin
        
        # 检查是否已存在admin用户名
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            logger.info("用户名 'admin' 已存在，更新为管理员角色")
            existing_user.role = "admin"
            existing_user.is_active = True
            db.commit()
            db.refresh(existing_user)
            return existing_user
        
        # 创建新的管理员用户
        admin_user = User(
            username="admin",
            password_hash=get_password_hash("admin123"),  # 默认密码
            email="admin@example.com",
            role="admin",
            theme="light",
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info(f"管理员用户创建成功: {admin_user.username} (ID: {admin_user.id})")
        logger.info("默认密码: admin123")
        logger.info("请登录后立即修改密码！")
        
        return admin_user
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建管理员用户失败: {e}")
        raise
    finally:
        db.close()


def create_test_users():
    """创建测试用户"""
    db: Session = SessionLocal()
    
    try:
        test_users = [
            {
                "username": "manager",
                "password": "manager123",
                "email": "manager@example.com",
                "role": "manager"
            },
            {
                "username": "user1",
                "password": "user123",
                "email": "user1@example.com",
                "role": "user"
            },
            {
                "username": "user2",
                "password": "user123",
                "email": "user2@example.com",
                "role": "user"
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if existing_user:
                logger.info(f"用户已存在: {existing_user.username}")
                continue
            
            # 创建新用户
            new_user = User(
                username=user_data["username"],
                password_hash=get_password_hash(user_data["password"]),
                email=user_data["email"],
                role=user_data["role"],
                theme="light",
                is_active=True
            )
            
            db.add(new_user)
            created_users.append(new_user)
        
        if created_users:
            db.commit()
            for user in created_users:
                db.refresh(user)
                logger.info(f"测试用户创建成功: {user.username} (ID: {user.id})")
        
        return created_users
        
    except Exception as e:
        db.rollback()
        logger.error(f"创建测试用户失败: {e}")
        raise
    finally:
        db.close()


def show_user_statistics():
    """显示用户统计信息"""
    db: Session = SessionLocal()
    
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        admin_users = db.query(User).filter(User.role == "admin").count()
        manager_users = db.query(User).filter(User.role == "manager").count()
        regular_users = db.query(User).filter(User.role == "user").count()
        
        logger.info("=== 用户统计信息 ===")
        logger.info(f"总用户数: {total_users}")
        logger.info(f"活跃用户: {active_users}")
        logger.info(f"管理员: {admin_users}")
        logger.info(f"经理: {manager_users}")
        logger.info(f"普通用户: {regular_users}")
        
        # 显示所有用户列表
        all_users = db.query(User).all()
        logger.info("=== 用户列表 ===")
        for user in all_users:
            status = "活跃" if user.is_active else "停用"
            logger.info(f"ID: {user.id}, 用户名: {user.username}, 角色: {user.role.value}, 状态: {status}")
        
    except Exception as e:
        logger.error(f"获取用户统计信息失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("开始初始化用户数据...")
    
    # 创建管理员用户
    admin_user = create_admin_user()
    
    # 创建测试用户
    test_users = create_test_users()
    
    # 显示统计信息
    show_user_statistics()
    
    logger.info("用户初始化完成！")
    logger.info("可以使用以下账号登录测试:")
    logger.info("管理员: admin / admin123")
    logger.info("经理: manager / manager123")
    logger.info("用户: user1 / user123")