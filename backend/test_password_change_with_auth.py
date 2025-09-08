#!/usr/bin/env python3
"""
测试带认证的密码修改功能
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def login_user(username, password):
    """用户登录并获取token"""
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            return result.get("access_token")
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None

def change_password_with_token(token, old_password, new_password):
    """使用token修改密码"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    change_data = {
        "old_password": old_password,
        "new_password": new_password
    }
    
    try:
        response = requests.put(f"{BASE_URL}/auth/password", json=change_data, headers=headers, timeout=10)
        return response.status_code, response.json() if response.status_code == 200 else response.text
    except Exception as e:
        return None, str(e)

def test_user_password_change(username, current_password, new_password):
    """测试用户密码修改"""
    print(f"\n=== 测试 {username} 用户密码修改 ===")
    
    # 1. 登录获取token
    print(f"1. 使用当前密码登录...")
    token = login_user(username, current_password)
    if not token:
        print("❌ 登录失败，无法继续测试")
        return False
    print(f"✅ 登录成功，获取到token: {token[:50]}...")
    
    # 2. 修改密码
    print(f"2. 修改密码...")
    status_code, result = change_password_with_token(token, current_password, new_password)
    if status_code == 200:
        print(f"✅ 密码修改成功: {result}")
    else:
        print(f"❌ 密码修改失败: {result}")
        return False
    
    # 3. 用新密码登录验证
    print(f"3. 使用新密码登录验证...")
    new_token = login_user(username, new_password)
    if new_token:
        print(f"✅ 新密码登录成功")
        return True
    else:
        print(f"❌ 新密码登录失败")
        return False

def test_wrong_token():
    """测试错误的token"""
    print(f"\n=== 测试错误的token ===")
    
    headers = {
        "Authorization": "Bearer invalid_token",
        "Content-Type": "application/json"
    }
    
    change_data = {
        "old_password": "any",
        "new_password": "any"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/auth/password", json=change_data, headers=headers, timeout=10)
        if response.status_code == 401:
            print("✅ 正确拒绝了无效token")
            return True
        else:
            print(f"❌ 意外响应: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 带认证的密码修改功能测试 ===")
    
    # 等待服务启动
    import time
    print("等待服务启动...")
    time.sleep(3)
    
    success_count = 0
    total_tests = 0
    
    # 测试错误token
    total_tests += 1
    if test_wrong_token():
        success_count += 1
    
    # 测试admin用户密码修改
    total_tests += 1
    if test_user_password_change("admin", "admin", "new_admin_pass"):
        success_count += 1
        
        # 恢复admin密码
        print("恢复admin密码...")
        admin_token = login_user("admin", "new_admin_pass")
        if admin_token:
            change_password_with_token(admin_token, "new_admin_pass", "admin")
            print("✅ admin密码已恢复")
    
    # 测试xiaobang用户密码修改
    total_tests += 1
    if test_user_password_change("xiaobang", "xiaobang", "new_xiaobang_pass"):
        success_count += 1
        
        # 恢复xiaobang密码
        print("恢复xiaobang密码...")
        xiaobang_token = login_user("xiaobang", "new_xiaobang_pass")
        if xiaobang_token:
            change_password_with_token(xiaobang_token, "new_xiaobang_pass", "xiaobang")
            print("✅ xiaobang密码已恢复")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✅ 所有测试通过，密码修改功能正常!")
    else:
        print("❌ 部分测试失败")

if __name__ == "__main__":
    main()