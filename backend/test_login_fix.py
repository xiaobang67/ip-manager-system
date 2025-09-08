#!/usr/bin/env python3
"""
测试登录修复
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_login(username, password):
    """测试登录"""
    print(f"\n=== 测试登录: {username} ===")
    
    login_data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 登录成功!")
            print(f"访问令牌: {result.get('access_token', 'N/A')[:50]}...")
            print(f"用户信息: {result.get('user', {})}")
            return True
        else:
            print("❌ 登录失败!")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保后端服务正在运行")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_wrong_password(username, wrong_password):
    """测试错误密码"""
    print(f"\n=== 测试错误密码: {username} ===")
    
    login_data = {
        "username": username,
        "password": wrong_password
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ 正确拒绝了错误密码!")
            return True
        elif response.status_code == 200:
            print("❌ 错误密码被接受了，这是安全漏洞!")
            return False
        else:
            print(f"❓ 意外的响应: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 登录功能测试 ===")
    
    # 测试正确的登录
    success_count = 0
    total_tests = 0
    
    # 测试admin用户正确密码
    total_tests += 1
    if test_login("admin", "admin"):
        success_count += 1
    
    # 测试xiaobang用户正确密码
    total_tests += 1
    if test_login("xiaobang", "xiaobang"):
        success_count += 1
    
    # 测试错误密码
    total_tests += 1
    if test_wrong_password("admin", "wrong_password"):
        success_count += 1
    
    total_tests += 1
    if test_wrong_password("xiaobang", "wrong_password"):
        success_count += 1
    
    # 测试不存在的用户
    total_tests += 1
    if test_wrong_password("nonexistent", "any_password"):
        success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✅ 所有测试通过，登录功能正常!")
    else:
        print("❌ 部分测试失败，请检查问题")

if __name__ == "__main__":
    main()