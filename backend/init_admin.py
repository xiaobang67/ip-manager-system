#!/usr/bin/env python3
"""
初始化管理员用户脚本
"""
import sys
import os
import logging
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_session
from models.auth_user import AuthUser
from services.auth_service import auth_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_admin_user():
    """初始化管理员用户"""
    db = next(get_db_session())
    try:
        # 检查是否已存在admin用户
        admin = db.query(AuthUser).filter_by(username="admin").first()
        
        if admin:
            logger.info("管理员用户已存在，正在更新密码...")
            admin.password_hash = auth_service.hash_password("admin123")
            admin.is_active = True
            admin.is_admin = True
            admin.is_superuser = True
            admin.display_name = "系统管理员"
        else:
            logger.info("创建管理员用户...")
            admin = AuthUser(
                username="admin",
                password_hash=auth_service.hash_password("admin123"),
                display_name="系统管理员",
                is_active=True,
                is_admin=True,
                is_superuser=True,
                is_ldap_user=False
            )
            db.add(admin)
        
        db.commit()
        logger.info("管理员用户初始化成功")
        logger.info("用户名: admin")
        logger.info("密码: admin123")
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化管理员用户失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_admin_user()