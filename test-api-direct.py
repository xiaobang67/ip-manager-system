#!/usr/bin/env python3
"""
直接测试API端点
"""
import requests
import json

# 配置
BASE_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "XB@xb199167"

def test_api():
    """测试API端点"""
    
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
    
    # 2. 直接测试角色API
    print("\n2. 直接测试角色API...")
    response = requests.get(f"{BASE_URL}/api/users/roles/available", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    if response.status_code == 200:
        roles_data = response.json()
        print(f"解析后的数据: {json.dumps(roles_data, indent=2, ensure_ascii=False)}")
    
    return True

if __name__ == "__main__":
    test_api()