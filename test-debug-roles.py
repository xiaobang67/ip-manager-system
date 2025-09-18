#!/usr/bin/env python3
"""
测试调试角色API端点
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "XB@xb199167"

def test_debug_roles():
    """测试调试角色API"""
    
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
    
    # 2. 测试调试端点
    endpoints = [
        "/api/users/roles/debug",
        "/api/users/roles/available",
        "/api/users/roles/test"
    ]
    
    for endpoint in endpoints:
        print(f"\n测试端点: {endpoint}")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"错误响应: {response.text}")
        except Exception as e:
            print(f"请求失败: {e}")

if __name__ == "__main__":
    test_debug_roles()