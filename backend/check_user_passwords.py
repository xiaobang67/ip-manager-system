#!/usr/bin/env python3
"""
检查数据库中用户密码的哈希状态
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
from app.core.security import verify_password, get_password_hash

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        port=3306,
        user='ipam_user',
        password='ipam_pass123',
        database='ipam',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def check_user_passwords():
    """检查用户密码状态"""
    print("=== 检查数据库中用户密码状态 ===")
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 获取所有用户
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()
            
            print(f"找到 {len(users)} 个用户:")
            
            for user in users:
                print(f"\n用户: {user['username']} (ID: {user['id']})")
                print(f"密码哈希: {user['password_hash']}")
                
                # 检查是否是bcrypt哈希
                if user['password_hash'].startswith('$2b$'):
                    print("✅ 使用bcrypt哈希")
                    
                    # 测试常见密码
                    common_passwords = ['admin', 'password', 'password123', '123456']
                    for pwd in common_passwords:
                        if verify_password(pwd, user['password_hash']):
                            print(f"✅ 密码是: {pwd}")
                            break
                    else:
                        print("❓ 未找到匹配的常见密码")
                else:
                    print("❌ 未使用bcrypt哈希，可能是明文或其他格式")
                    
                    # 如果是明文，需要更新
                    if user['password_hash'] in ['admin', 'password', 'password123']:
                        print(f"⚠️  发现明文密码: {user['password_hash']}")
                        new_hash = get_password_hash(user['password_hash'])
                        print(f"建议更新为: {new_hash}")
                        
                        # 更新密码哈希
                        cursor.execute(
                            "UPDATE users SET password_hash = %s WHERE id = %s",
                            (new_hash, user['id'])
                        )
                        print("✅ 已更新密码哈希")
            
            connection.commit()
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    check_user_passwords()