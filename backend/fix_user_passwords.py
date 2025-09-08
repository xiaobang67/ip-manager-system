#!/usr/bin/env python3
"""
修复用户密码哈希 - 使用统一认证服务
"""
import sys
import os
import hashlib
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pymysql
from auth_service import auth_service, reset_user_password
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

def sha256_hash(password):
    """生成SHA256哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def fix_user_passwords():
    """修复用户密码哈希"""
    print("=== 修复用户密码哈希（使用统一认证服务）===")
    
    # 常见密码列表
    common_passwords = ['admin', 'password', 'password123', '123456', 'xiaobang', 'user']
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # 获取所有用户
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()
            
            print(f"找到 {len(users)} 个用户:")
            
            for user in users:
                print(f"\n处理用户: {user['username']} (ID: {user['id']})")
                print(f"当前哈希: {user['password_hash']}")
                
                # 检查是否已经是bcrypt哈希
                if user['password_hash'].startswith('$2b$'):
                    print(f"✅ 用户 {user['username']} 已使用bcrypt哈希，跳过")
                    continue
                
                # 尝试匹配常见密码的SHA256哈希
                original_password = None
                for pwd in common_passwords:
                    if sha256_hash(pwd) == user['password_hash']:
                        original_password = pwd
                        print(f"✅ 找到原始密码: {pwd}")
                        break
                
                if not original_password:
                    # 尝试用户名作为密码
                    if sha256_hash(user['username']) == user['password_hash']:
                        original_password = user['username']
                        print(f"✅ 密码是用户名: {user['username']}")
                
                if original_password:
                    # 使用统一认证服务重置密码
                    if reset_user_password(user['username'], original_password):
                        print(f"✅ 已更新用户 {user['username']} 的密码哈希")
                    else:
                        print(f"❌ 更新用户 {user['username']} 的密码哈希失败")
                else:
                    print(f"❌ 无法确定用户 {user['username']} 的原始密码")
            
            print("\n=== 修复完成 ===")
            
            # 验证修复结果
            print("\n=== 验证修复结果 ===")
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()
            
            for user in users:
                print(f"\n用户: {user['username']}")
                if user['password_hash'].startswith('$2b$'):
                    print("✅ 使用bcrypt哈希")
                    
                    # 测试密码
                    test_passwords = ['admin', user['username'], 'password123']
                    for pwd in test_passwords:
                        if auth_service.verify_user_password(user['username'], pwd):
                            print(f"✅ 密码验证成功: {pwd}")
                            break
                else:
                    print("❌ 仍未使用bcrypt哈希")
                    
    except Exception as e:
        print(f"错误: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    fix_user_passwords()