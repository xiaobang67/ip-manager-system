#!/usr/bin/env python3
"""
更新管理员密码的脚本
"""
import sys
import os

# 添加项目路径
sys.path.append('/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.auth_user import AuthUser
from passlib.hash import bcrypt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('/app/config.env')

def update_admin_password():
    """更新管理员密码"""
    # 数据库连接
    db_host = os.getenv('DB_HOST', 'mysql')
    db_port = os.getenv('DB_PORT', '3306')
    db_user = os.getenv('DB_USER', 'ipuser')
    db_password = os.getenv('DB_PASSWORD', 'ippassword')
    db_name = os.getenv('DB_NAME', 'ip_management_system')
    
    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 查找管理员用户
        admin_user = session.query(AuthUser).filter_by(username='admin').first()
        if not admin_user:
            print("管理员用户不存在")
            return False
            
        # 生成新密码哈希
        new_password = "admin123"
        hashed_password = bcrypt.hash(new_password)
        
        # 更新密码
        admin_user.password_hash = hashed_password
        admin_user.is_ldap_user = False  # 确保是本地用户
        
        session.commit()
        print(f"管理员密码已更新，新密码: {new_password}")
        print(f"密码哈希: {hashed_password}")
        return True
        
    except Exception as e:
        print(f"更新密码时出错: {e}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    update_admin_password()