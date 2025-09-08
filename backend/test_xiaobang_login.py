#!/usr/bin/env python3
"""
测试xiaobang用户登录
"""
import requests
import json

def test_xiaobang_login():
    """测试xiaobang用户登录"""
    print("=== 测试xiaobang用户登录 ===")
    
    login_data = {
        "username": "xiaobang",
        "password": "xiaobang"
    }
    
    try:
        response = requests.post("http://localhost:8000/api/auth/login", json=login_data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ xiaobang登录成功!")
            print(f"用户信息: {result.get('user', {})}")
            print(f"访问令牌: {result.get('access_token', 'N/A')[:50]}...")
            return True
        else:
            print("❌ 登录失败")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    test_xiaobang_login()