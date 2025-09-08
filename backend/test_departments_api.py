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
    print("测试登录...")
    
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"登录响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            print(f"登录成功，获取到token: {token[:20]}...")
            return token
        else:
            print(f"登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"登录请求失败: {e}")
        return None

def test_departments_api(token=None):
    """测试部门API"""
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    print("\n" + "="*50)
    print("测试部门API")
    print("="*50)
    
    # 测试获取部门列表
    print("\n1. 测试获取部门列表...")
    try:
        response = requests.get(f"{BASE_URL}/departments/", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            if 'departments' in data:
                print(f"获取到 {len(data['departments'])} 个部门")
                for dept in data['departments'][:3]:  # 只显示前3个
                    print(f"  - {dept['name']} ({dept['code']})")
            else:
                print("响应格式异常，未找到departments字段")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    # 测试获取部门统计
    print("\n2. 测试获取部门统计...")
    try:
        response = requests.get(f"{BASE_URL}/departments/statistics", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"统计数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    # 测试获取部门选项
    print("\n3. 测试获取部门选项...")
    try:
        response = requests.get(f"{BASE_URL}/departments/options", headers=headers)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"选项数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")
    
    # 测试创建部门
    print("\n4. 测试创建部门...")
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
        print(f"状态码: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"创建成功: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return data.get('id')
        else:
            print(f"创建失败: {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def test_without_auth():
    """测试不带认证的请求"""
    print("\n" + "="*50)
    print("测试不带认证的请求")
    print("="*50)
    
    try:
        response = requests.get(f"{BASE_URL}/departments/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
    except Exception as e:
        print(f"请求异常: {e}")

def main():
    print("部门API测试开始...")
    print(f"测试目标: {BASE_URL}")
    
    # 等待服务启动
    print("\n等待服务启动...")
    time.sleep(5)
    
    # 测试不带认证的请求
    test_without_auth()
    
    # 测试登录
    token = test_login()
    
    # 测试部门API
    if token:
        test_departments_api(token)
    else:
        print("无法获取认证token，跳过需要认证的测试")
        # 尝试不带认证的测试
        test_departments_api()
    
    print("\n" + "="*50)
    print("测试完成")
    print("="*50)

if __name__ == "__main__":
    main()