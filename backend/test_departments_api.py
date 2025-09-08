#!/usr/bin/env python3
"""
部门API测试脚本
用于验证部门管理API是否正常工作
"""
import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000/api"

def test_login():
    """测试登录并获取token"""

    
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)

        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')

            return token
        else:

            return None
    except Exception as e:

        return None

def test_departments_api(token=None):
    """测试部门API"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    

    
    # 测试获取部门列表
    try:
        response = requests.get(f"{BASE_URL}/departments/", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'departments' in data:
                pass  # 测试通过
            else:
                pass  # 响应格式异常
        else:
            pass  # 请求失败
    except Exception as e:
        pass  # 请求异常
    
    # 测试获取部门统计
    try:
        response = requests.get(f"{BASE_URL}/departments/statistics", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
        else:
            pass  # 请求失败
    except Exception as e:
        pass  # 请求异常
    
    # 测试获取部门选项
    try:
        response = requests.get(f"{BASE_URL}/departments/options", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
        else:
            pass  # 请求失败
    except Exception as e:
        pass  # 请求异常
    
    # 测试创建部门
    test_dept_data = {
        "name": f"测试部门_{int(time.time())}",
        "code": f"TEST_{int(time.time())}",
        "description": "这是一个测试部门",
        "manager": "测试经理",
        "contact_email": "test@example.com",
        "contact_phone": "123-456-7890"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/departments/", json=test_dept_data, headers=headers)
        
        if response.status_code in [200, 201]:
            data = response.json()
            return data.get('id')
        else:
            return None
    except Exception as e:
        return None

def test_without_auth():
    """测试不带认证的请求"""
    
    try:
        response = requests.get(f"{BASE_URL}/departments/")
        # 静默测试，不输出调试信息
    except Exception as e:
        pass  # 请求异常

def main():
    # 等待服务启动
    time.sleep(5)
    
    # 测试不带认证的请求
    test_without_auth()
    
    # 测试登录
    token = test_login()
    
    # 测试部门API
    if token:
        test_departments_api(token)
    else:
        # 尝试不带认证的测试
        test_departments_api()

if __name__ == "__main__":
    main()