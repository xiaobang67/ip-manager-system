#!/usr/bin/env python3
"""
数据库连接测试脚本
"""
import os
import sys
sys.path.append('./backend')

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('./backend/.env')

# 构建数据库连接字符串
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_user = os.getenv('DB_USER', 'root')
db_password = os.getenv('DB_PASSWORD', 'rootpassword')
db_name = os.getenv('DB_NAME', 'ip_management_system')

database_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

print(f"测试数据库连接...")
print(f"连接字符串: mysql+pymysql://{db_user}:****@{db_host}:{db_port}/{db_name}")

try:
    # 创建引擎
    engine = create_engine(database_url)
    
    # 测试连接
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ 数据库连接成功!")
        
        # 测试admin用户查询
        result = connection.execute(text("SELECT username, is_admin, is_active, password_hash FROM auth_users WHERE username='admin'"))
        row = result.fetchone()
        if row:
            print(f"✅ 找到admin用户: username={row[0]}, is_admin={row[1]}, is_active={row[2]}")
            stored_hash = row[3]
            print(f"数据库中的哈希: {stored_hash}")
        else:
            print("❌ 未找到admin用户")
            stored_hash = None
            
        # 测试密码验证
        if stored_hash:
            import bcrypt
            test_password = "admin123"
            
            if bcrypt.checkpw(test_password.encode('utf-8'), stored_hash.encode('utf-8')):
                print("✅ 密码验证成功!")
            else:
                print("❌ 密码验证失败!")
        else:
            print("❌ 无法进行密码验证")
            
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")