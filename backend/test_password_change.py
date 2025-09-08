#!/usr/bin/env python3
"""
测试密码修改功能
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_password_change():
    """测试密码修改功能"""
    print("=== 测试密码修改功能 ===")
    
    # 测试数据
    change_data = {
        "old_password": "admin",
        "new_password": "new_admin_password"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/auth/password", json=change_data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 密码修改成功!")
            print(f"响应: {result}")
            return True
        else:
            print("❌ 密码修改失败!")
            print(f"错误信息: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_wrong_old_password():
    """测试错误的旧密码"""
    print("\n=== 测试错误的旧密码 ===")
    
    change_data = {
        "old_password": "wrong_password",
        "new_password": "new_password"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/auth/password", json=change_data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ 正确拒绝了错误的旧密码!")
            return True
        else:
            print(f"❌ 意外的响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    # 等待服务启动
    import time
    print("等待服务启动...")
    time.sleep(3)
    
    success_count = 0
    total_tests = 0
    
    # 测试错误的旧密码
    total_tests += 1
    if test_wrong_old_password():
        success_count += 1
    
    # 测试正确的密码修改
    total_tests += 1
    if test_password_change():
        success_count += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")