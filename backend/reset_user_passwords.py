#!/usr/bin/env python3
"""
重置用户密码为已知值 - 使用统一认证服务
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_service import auth_service, reset_user_password

def reset_user_passwords():
    """重置用户密码"""
    print("=== 重置用户密码（使用统一认证服务）===")
    
    # 用户密码映射
    user_passwords = {
        'admin': 'admin',
        'xiaobang': 'xiaobang'
    }
    
    for username, password in user_passwords.items():
        print(f"\n重置用户 {username} 的密码...")
        print(f"新密码: {password}")
        
        # 使用统一认证服务重置密码
        if reset_user_password(username, password):
            print(f"✅ 用户 {username} 密码重置成功")
        else:
            print(f"❌ 用户 {username} 密码重置失败")
    
    print("\n=== 重置完成 ===")
    
    # 验证重置结果
    print("\n=== 验证重置结果 ===")
    for username, password in user_passwords.items():
        print(f"\n验证用户: {username}")
        
        # 使用统一认证服务验证密码
        if auth_service.verify_user_password(username, password):
            print(f"✅ 密码验证成功: {password}")
        else:
            print(f"❌ 密码验证失败")
            
            # 尝试其他常见密码
            test_passwords = ['admin', 'password', 'password123']
            for test_pwd in test_passwords:
                if auth_service.verify_user_password(username, test_pwd):
                    print(f"✅ 实际密码是: {test_pwd}")
                    break
        
        # 获取用户信息
        user_info = auth_service.get_user_by_username(username)
        if user_info:
            print(f"用户信息: ID={user_info['id']}, 角色={user_info['role']}, 状态={'活跃' if user_info['is_active'] else '禁用'}")
        else:
            print(f"❌ 用户 {username} 不存在")

if __name__ == "__main__":
    reset_user_passwords()