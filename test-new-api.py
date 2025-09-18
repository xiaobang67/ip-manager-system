#!/usr/bin/env python3
"""
测试新的用户创建API
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "XB@xb199167"

def test_user_creation():
    """测试用户创建API"""
    
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
    
    # 2. 创建只读用户
    print("\n2. 创建只读用户...")
    readonly_user_data = {
        "username": "readonly_test_user_2",
        "password": "readonly123",
        "email": "readonly2@test.com",
        "role": "readonly"
    }
    
    response = requests.post(f"{BASE_URL}/api/users/", json=readonly_user_data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code in [200, 201]:
        created_user = response.json()
        print(f"✅ 只读用户创建成功: {json.dumps(created_user, indent=2, ensure_ascii=False)}")
        return True
    else:
        print(f"❌ 创建只读用户失败")
        return False

if __name__ == "__main__":
    test_user_creation()