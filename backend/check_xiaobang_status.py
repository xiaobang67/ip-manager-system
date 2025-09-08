#!/usr/bin/env python3
"""
检查xiaobang用户状态和admin密码
"""
import sys
import os
import hashlib
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

def sha256_hash(password):
    """生成SHA256哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_admin_password():
    """检查admin用户的密码"""
    print("=== 检查admin用户密码 ===")
    
    admin_hash = "337f4c7c72d7cb65ffadc48e7f9b58b17d6e2fb6ea57d8f5ccc78ac8a21dc8c6"
    
    # 扩展密码列表
    test_passwords = [
        'admin', 'password', 'password123', '123456', 'xiaobang', 'user',
        'Admin', 'ADMIN', 'root', 'administrator', 'pass', '12345',
        'qwerty', 'abc123', 'admin123', 'test', 'guest', 'demo'
    ]
    
    print(f"admin用户当前哈希: {admin_hash}")
    
    for pwd in test_passwords:
        test_hash = sha256_hash(pwd)
        print(f"测试密码 '{pwd}': {test_hash}")
        if test_hash == admin_hash:
            print(f"✅ 找到匹配密码: {pwd}")
            return pwd
    
    print("❌ 未找到匹配的密码")
    return None

def check_xiaobang_login():
    """检查xiaobang用户登录"""
    print("\n=== 检查xiaobang用户登录 ===")
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT username, password_hash FROM users WHERE username = 'xiaobang'")
            user = cursor.fetchone()
            
            if user:
                print(f"xiaobang用户哈希: {user['password_hash']}")
                
                # 测试常见密码
                test_passwords = ['xiaobang', 'admin', 'password', 'password123']
                
                for pwd in test_passwords:
                    if verify_password(pwd, user['password_hash']):
                        print(f"✅ xiaobang用户密码是: {pwd}")
                        return pwd
                
                print("❌ 未找到xiaobang用户的密码")
            else:
                print("❌ xiaobang用户不存在")
                
    except Exception as e:
        print(f"错误: {e}")
    finally:
        connection.close()
    
    return None

def manual_fix_admin():
    """手动修复admin用户密码"""
    print("\n=== 手动修复admin用户密码 ===")
    
    # 直接设置admin密码为'admin'
    new_password = 'admin'
    new_hash = get_password_hash(new_password)
    
    print(f"将admin用户密码设置为: {new_password}")
    print(f"新的bcrypt哈希: {new_hash}")
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE username = 'admin'",
                (new_hash,)
            )
            connection.commit()
            
            if cursor.rowcount > 0:
                print("✅ admin用户密码已更新")
                
                # 验证更新
                cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
                user = cursor.fetchone()
                
                if verify_password(new_password, user['password_hash']):
                    print("✅ 密码验证成功")
                else:
                    print("❌ 密码验证失败")
            else:
                print("❌ 更新失败")
                
    except Exception as e:
        print(f"错误: {e}")
        connection.rollback()
    finally:
        connection.close()

if __name__ == "__main__":
    # 检查admin密码
    admin_pwd = check_admin_password()
    
    # 检查xiaobang登录
    xiaobang_pwd = check_xiaobang_login()
    
    # 如果找不到admin密码，手动修复
    if not admin_pwd:
        manual_fix_admin()