#!/usr/bin/env python3
"""
测试通过用户管理界面创建只读用户的功能
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "XB@xb199167"

def test_readonly_user_creation():
    """测试只读用户创建功能"""
    
    # 1. 管理员登录
    print("1. 管理员登录...")
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ 管理员登录失败: {response.text}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 管理员登录成功")
    
    # 2. 获取可用角色列表
    print("\n2. 获取可用角色列表...")
    response = requests.get(f"{BASE_URL}/api/users/roles/available", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取角色列表失败: {response.text}")
        return False
    
    roles_response = response.json()
    print("✅ 可用角色列表:")
    
    # 处理不同的响应格式
    if isinstance(roles_response, dict) and "roles" in roles_response:
        roles = roles_response["roles"]
    elif isinstance(roles_response, list):
        roles = roles_response
    else:
        roles = []
    
    for role in roles:
        print(f"   - {role['value']}: {role['label']}")
    
    # 检查是否包含只读角色
    readonly_role_exists = any(role["value"] == "readonly" for role in roles)
    if not readonly_role_exists:
        print("❌ 只读角色不在可用角色列表中")
        return False
    print("✅ 只读角色已包含在可用角色列表中")
    
    # 3. 创建只读用户
    print("\n3. 创建只读用户...")
    import time
    timestamp = int(time.time())
    readonly_user_data = {
        "username": f"readonly_test_{timestamp}",
        "password": "readonly123",
        "email": f"readonly{timestamp}@test.com",
        "role": "readonly"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/", json=readonly_user_data, headers=headers)
    if response.status_code not in [200, 201]:
        print(f"❌ 创建只读用户失败: {response.text}")
        return False
    
    created_user = response.json()
    print(f"✅ 只读用户创建成功: {created_user['username']} (ID: {created_user['id']})")
    
    # 4. 验证用户角色
    print("\n4. 验证用户角色...")
    response = requests.get(f"{BASE_URL}/api/users/{created_user['id']}", headers=headers)
    if response.status_code != 200:
        print(f"❌ 获取用户信息失败: {response.text}")
        return False
    
    user_info = response.json()
    if user_info["role"] != "readonly":
        print(f"❌ 用户角色不正确: 期望 'readonly', 实际 '{user_info['role']}'")
        return False
    
    print(f"✅ 用户角色验证成功: {user_info['role']}")
    
    # 5. 测试只读用户登录
    print("\n5. 测试只读用户登录...")
    readonly_login_data = {
        "username": "readonly_test_user",
        "password": "readonly123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=readonly_login_data)
    if response.status_code != 200:
        print(f"❌ 只读用户登录失败: {response.text}")
        return False
    
    readonly_token = response.json()["access_token"]
    readonly_headers = {"Authorization": f"Bearer {readonly_token}"}
    print("✅ 只读用户登录成功")
    
    # 6. 测试只读用户权限
    print("\n6. 测试只读用户权限...")
    
    # 测试访问IP列表（应该成功）
    response = requests.get(f"{BASE_URL}/api/ips/search", headers=readonly_headers)
    if response.status_code != 200:
        print(f"❌ 只读用户访问IP列表失败: {response.text}")
        return False
    print("✅ 只读用户可以访问IP列表")
    
    # 测试创建IP（应该失败）
    ip_data = {
        "subnet_id": 1,
        "preferred_ip": "192.168.1.100",
        "user_name": "test",
        "device_type": "desktop",
        "assigned_to": "IT部门"
    }
    response = requests.post(f"{BASE_URL}/api/ips/allocate", json=ip_data, headers=readonly_headers)
    if response.status_code == 200 or response.status_code == 201:
        print("❌ 只读用户不应该能够创建IP")
        return False
    print("✅ 只读用户无法创建IP（权限正确）")
    
    print("\n🎉 所有测试通过！只读用户创建和权限控制功能正常工作。")
    return True

if __name__ == "__main__":
    try:
        success = test_readonly_user_creation()
        if success:
            print("\n✅ 测试完成：只读用户功能正常")
        else:
            print("\n❌ 测试失败：只读用户功能存在问题")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")