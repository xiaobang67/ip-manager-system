#!/usr/bin/env python3
"""
检查数据库中的用户信息
"""

import pymysql
import os

def check_users():
    """检查数据库中的用户"""
    
    # 数据库配置
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'ipam_user'),
        'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
        'database': os.getenv('DB_NAME', 'ipam'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    try:
        connection = pymysql.connect(**db_config)
        print("✅ 数据库连接成功")
        
        with connection.cursor() as cursor:
            # 查询所有用户
            cursor.execute("SELECT id, username, email, role, is_active, created_at FROM users")
            users = cursor.fetchall()
            
            print(f"\n数据库中共有 {len(users)} 个用户：")
            print("-" * 80)
            for user in users:
                print(f"ID: {user['id']}")
                print(f"用户名: {user['username']}")
                print(f"邮箱: {user['email']}")
                print(f"角色: {user['role']}")
                print(f"状态: {'激活' if user['is_active'] else '禁用'}")
                print(f"创建时间: {user['created_at']}")
                print("-" * 80)
        
        connection.close()
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")

def reset_admin_password():
    """重置admin用户密码为admin123"""
    
    # 数据库配置
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'ipam_user'),
        'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
        'database': os.getenv('DB_NAME', 'ipam'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    
    try:
        connection = pymysql.connect(**db_config)
        print("✅ 数据库连接成功")
        
        # 生成admin123的bcrypt哈希
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        password_hash = pwd_context.hash("admin123")
        
        with connection.cursor() as cursor:
            # 更新admin用户密码
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = 'admin'",
                (password_hash,)
            )
            connection.commit()
            
            if cursor.rowcount > 0:
                print("✅ admin用户密码已重置为 admin123")
            else:
                print("❌ 未找到admin用户")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ 重置密码失败: {e}")

if __name__ == "__main__":
    print("选择操作：")
    print("1. 查看用户信息")
    print("2. 重置admin密码为admin123")
    
    choice = input("请输入选择 (1/2): ").strip()
    
    if choice == "1":
        check_users()
    elif choice == "2":
        reset_admin_password()
        print("密码重置完成，现在查看用户信息：")
        check_users()
    else:
        print("无效选择")