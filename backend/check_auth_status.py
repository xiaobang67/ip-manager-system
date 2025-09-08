#!/usr/bin/env python3
"""
检查认证服务状态
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pymysql
    print("✅ pymysql 模块可用")
except ImportError as e:
    print(f"❌ pymysql 模块不可用: {e}")
    sys.exit(1)

try:
    from app.core.security import verify_password, get_password_hash
    print("✅ security 模块可用")
except ImportError as e:
    print(f"❌ security 模块不可用: {e}")
    print("请确保 app/core/security.py 文件存在")
    sys.exit(1)

def check_database_connection():
    """检查数据库连接"""
    print("\n=== 检查数据库连接 ===")
    
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='ipam_user',
            password='ipam_pass123',
            database='ipam',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        print("✅ 数据库连接成功")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM users")
            result = cursor.fetchone()
            print(f"✅ 用户表中有 {result['count']} 个用户")
            
            # 检查用户密码哈希格式
            cursor.execute("SELECT username, password_hash FROM users LIMIT 5")
            users = cursor.fetchall()
            
            print("\n用户密码哈希格式:")
            for user in users:
                hash_type = "bcrypt" if user['password_hash'].startswith('$2b$') else "其他"
                print(f"- {user['username']}: {hash_type} ({user['password_hash'][:20]}...)")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

def test_password_functions():
    """测试密码函数"""
    print("\n=== 测试密码函数 ===")
    
    test_password = "test123"
    
    try:
        # 测试密码哈希生成
        hash_value = get_password_hash(test_password)
        print(f"✅ 密码哈希生成成功: {hash_value[:30]}...")
        
        # 测试密码验证
        if verify_password(test_password, hash_value):
            print("✅ 密码验证成功")
        else:
            print("❌ 密码验证失败")
            
        # 测试错误密码
        if not verify_password("wrong_password", hash_value):
            print("✅ 错误密码正确被拒绝")
        else:
            print("❌ 错误密码被错误接受")
            
        return True
        
    except Exception as e:
        print(f"❌ 密码函数测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 认证服务状态检查 ===")
    
    db_ok = check_database_connection()
    pwd_ok = test_password_functions()
    
    if db_ok and pwd_ok:
        print("\n✅ 认证服务基础组件都正常，可以继续测试统一认证服务")
    else:
        print("\n❌ 存在问题，请先解决基础组件问题")