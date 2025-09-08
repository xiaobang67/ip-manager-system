#!/usr/bin/env python3
"""
测试统一认证服务
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_service import auth_service, authenticate_user, reset_user_password, change_user_password

def test_unified_auth():
    """测试统一认证服务的所有功能"""
    print("=== 测试统一认证服务 ===")
    
    # 1. 测试用户认证
    print("\n1. 测试用户认证")
    test_users = [
        ('admin', 'admin'),
        ('xiaobang', 'xiaobang'),
        ('admin', 'wrong_password'),  # 错误密码测试
        ('nonexistent', 'password')   # 不存在用户测试
    ]
    
    for username, password in test_users:
        print(f"\n测试登录: {username} / {password}")
        user = authenticate_user(username, password)
        if user:
            print(f"✅ 认证成功: {user['username']} (ID: {user['id']}, 角色: {user['role']})")
        else:
            print(f"❌ 认证失败")
    
    # 2. 测试密码验证
    print("\n\n2. 测试密码验证")
    test_passwords = [
        ('admin', 'admin'),
        ('xiaobang', 'xiaobang'),
        ('admin', 'wrong_password')
    ]
    
    for username, password in test_passwords:
        print(f"\n验证密码: {username} / {password}")
        if auth_service.verify_user_password(username, password):
            print(f"✅ 密码验证成功")
        else:
            print(f"❌ 密码验证失败")
    
    # 3. 测试获取用户信息
    print("\n\n3. 测试获取用户信息")
    test_usernames = ['admin', 'xiaobang', 'nonexistent']
    
    for username in test_usernames:
        print(f"\n获取用户信息: {username}")
        user = auth_service.get_user_by_username(username)
        if user:
            print(f"✅ 用户信息: ID={user['id']}, 用户名={user['username']}, 角色={user['role']}, 状态={'活跃' if user['is_active'] else '禁用'}")
        else:
            print(f"❌ 用户不存在")
    
    # 4. 测试密码重置（管理员操作）
    print("\n\n4. 测试密码重置")
    print("重置admin用户密码为 'newpassword123'")
    if reset_user_password('admin', 'newpassword123'):
        print("✅ 密码重置成功")
        
        # 验证新密码
        print("验证新密码...")
        if auth_service.verify_user_password('admin', 'newpassword123'):
            print("✅ 新密码验证成功")
        else:
            print("❌ 新密码验证失败")
        
        # 恢复原密码
        print("恢复原密码...")
        if reset_user_password('admin', 'admin'):
            print("✅ 密码恢复成功")
        else:
            print("❌ 密码恢复失败")
    else:
        print("❌ 密码重置失败")
    
    # 5. 测试密码修改（用户操作）
    print("\n\n5. 测试密码修改")
    
    # 首先获取admin用户ID
    admin_user = auth_service.get_user_by_username('admin')
    if admin_user:
        user_id = admin_user['id']
        print(f"测试用户ID {user_id} 修改密码")
        
        # 测试正确的旧密码
        print("使用正确的旧密码修改...")
        if change_user_password(user_id, 'admin', 'newpassword456'):
            print("✅ 密码修改成功")
            
            # 验证新密码
            if auth_service.verify_user_password('admin', 'newpassword456'):
                print("✅ 新密码验证成功")
            else:
                print("❌ 新密码验证失败")
            
            # 恢复原密码
            if change_user_password(user_id, 'newpassword456', 'admin'):
                print("✅ 密码恢复成功")
            else:
                print("❌ 密码恢复失败")
        else:
            print("❌ 密码修改失败")
        
        # 测试错误的旧密码
        print("\n使用错误的旧密码修改...")
        if change_user_password(user_id, 'wrong_old_password', 'newpassword789'):
            print("❌ 不应该成功（旧密码错误）")
        else:
            print("✅ 正确拒绝了错误的旧密码")
    
    # 6. 测试创建新用户
    print("\n\n6. 测试创建新用户")
    test_username = 'testuser'
    test_password = 'testpass123'
    
    print(f"创建用户: {test_username}")
    user_id = auth_service.create_user(test_username, test_password, 'test@example.com', 'user')
    if user_id:
        print(f"✅ 用户创建成功，ID: {user_id}")
        
        # 测试新用户登录
        print("测试新用户登录...")
        user = authenticate_user(test_username, test_password)
        if user:
            print(f"✅ 新用户登录成功: {user['username']}")
        else:
            print("❌ 新用户登录失败")
        
        # 清理测试用户
        print("清理测试用户...")
        connection = auth_service.get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM users WHERE username = %s", (test_username,))
                connection.commit()
                print("✅ 测试用户已清理")
        except Exception as e:
            print(f"❌ 清理测试用户失败: {e}")
        finally:
            connection.close()
    else:
        print("❌ 用户创建失败")
    
    print("\n=== 统一认证服务测试完成 ===")

def check_password_hash_format():
    """检查数据库中所有用户的密码哈希格式"""
    print("\n=== 检查密码哈希格式 ===")
    
    connection = auth_service.get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()
            
            print(f"检查 {len(users)} 个用户的密码哈希格式:")
            
            bcrypt_count = 0
            other_count = 0
            
            for user in users:
                print(f"\n用户: {user['username']} (ID: {user['id']})")
                hash_value = user['password_hash']
                
                if hash_value.startswith('$2b$'):
                    print(f"✅ bcrypt哈希: {hash_value[:20]}...")
                    bcrypt_count += 1
                else:
                    print(f"❌ 非bcrypt哈希: {hash_value[:20]}...")
                    other_count += 1
            
            print(f"\n总结:")
            print(f"bcrypt哈希用户: {bcrypt_count}")
            print(f"其他格式用户: {other_count}")
            
            if other_count == 0:
                print("✅ 所有用户都使用bcrypt哈希格式")
            else:
                print("❌ 仍有用户使用非bcrypt哈希格式")
                
    except Exception as e:
        print(f"检查过程中发生错误: {e}")
    finally:
        connection.close()

if __name__ == "__main__":
    # 首先检查密码哈希格式
    check_password_hash_format()
    
    # 然后测试认证服务
    test_unified_auth()