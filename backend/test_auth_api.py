#!/usr/bin/env python3
"""
测试认证API端点
"""
import requests
import json
import sys

# API基础URL
BASE_URL = "http://localhost:8000"

def test_login_api():
    """测试登录API"""
    print("=== 测试登录API ===")
    
    # 测试用例
    test_cases = [
        {"username": "admin", "password": "admin", "should_succeed": True},
        {"username": "xiaobang", "password": "xiaobang", "should_succeed": True},
        {"username": "admin", "password": "wrong_password", "should_succeed": False},
        {"username": "nonexistent", "password": "password", "should_succeed": False}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['username']} / {test_case['password']}")
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={
                    "username": test_case["username"],
                    "password": test_case["password"]
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 登录成功")
                print(f"访问令牌: {data.get('access_token', 'N/A')[:50]}...")
                print(f"用户信息: {data.get('user', {})}")
                
                if test_case["should_succeed"]:
                    print("✅ 符合预期（应该成功）")
                    return data.get('access_token')  # 返回token用于后续测试
                else:
                    print("❌ 不符合预期（不应该成功）")
            else:
                print("❌ 登录失败")
                if response.headers.get('content-type', '').startswith('application/json'):
                    error_data = response.json()
                    print(f"错误信息: {error_data.get('detail', 'N/A')}")
                
                if not test_case["should_succeed"]:
                    print("✅ 符合预期（应该失败）")
                else:
                    print("❌ 不符合预期（应该成功）")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")
    
    return None

def test_change_password_api(access_token):
    """测试修改密码API"""
    print("\n\n=== 测试修改密码API ===")
    
    if not access_token:
        print("❌ 没有有效的访问令牌，跳过密码修改测试")
        return
    
    # 测试用例
    test_cases = [
        {
            "old_password": "admin",
            "new_password": "newpassword123",
            "description": "正确的旧密码"
        },
        {
            "old_password": "wrong_password",
            "new_password": "newpassword456",
            "description": "错误的旧密码"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['description']}")
        
        try:
            response = requests.put(
                f"{BASE_URL}/api/auth/password",
                json={
                    "old_password": test_case["old_password"],
                    "new_password": test_case["new_password"]
                },
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                timeout=10
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 密码修改成功: {data.get('message', 'N/A')}")
                
                if i == 1:  # 第一个测试用例应该成功
                    print("✅ 符合预期")
                    # 恢复原密码
                    print("恢复原密码...")
                    restore_response = requests.put(
                        f"{BASE_URL}/api/auth/password",
                        json={
                            "old_password": test_case["new_password"],
                            "new_password": "admin"
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {access_token}"
                        },
                        timeout=10
                    )
                    if restore_response.status_code == 200:
                        print("✅ 密码已恢复")
                    else:
                        print("❌ 密码恢复失败")
                else:
                    print("❌ 不符合预期（不应该成功）")
            else:
                print("❌ 密码修改失败")
                if response.headers.get('content-type', '').startswith('application/json'):
                    error_data = response.json()
                    print(f"错误信息: {error_data.get('detail', 'N/A')}")
                
                if i == 2:  # 第二个测试用例应该失败
                    print("✅ 符合预期（应该失败）")
                else:
                    print("❌ 不符合预期（应该成功）")
                    
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求异常: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
        except Exception as e:
            print(f"❌ 其他错误: {e}")

def test_profile_api(access_token):
    """测试用户资料API"""
    print("\n\n=== 测试用户资料API ===")
    
    if not access_token:
        print("❌ 没有有效的访问令牌，跳过用户资料测试")
        return
    
    # 测试获取用户资料
    print("\n1. 测试获取用户资料")
    try:
        response = requests.get(
            f"{BASE_URL}/api/auth/profile",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 获取用户资料成功")
            print(f"用户信息: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print("❌ 获取用户资料失败")
            if response.headers.get('content-type', '').startswith('application/json'):
                error_data = response.json()
                print(f"错误信息: {error_data.get('detail', 'N/A')}")
                
    except Exception as e:
        print(f"❌ 获取用户资料时发生错误: {e}")

def check_server_status():
    """检查服务器状态"""
    print("=== 检查服务器状态 ===")
    
    try:
        # 检查健康状态
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"健康检查状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 服务器运行正常")
            print(f"服务状态: {data.get('status', 'N/A')}")
            print(f"组件状态: {data.get('components', {})}")
            return True
        else:
            print("❌ 服务器状态异常")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器正在运行")
        print(f"尝试连接: {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ 检查服务器状态时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("=== 认证API测试工具 ===")
    print(f"测试目标: {BASE_URL}")
    
    # 检查服务器状态
    if not check_server_status():
        print("\n请先启动IPAM后端服务器，然后重新运行此测试。")
        print("启动命令: python enhanced_main.py")
        sys.exit(1)
    
    # 测试登录API
    access_token = test_login_api()
    
    # 测试修改密码API
    test_change_password_api(access_token)
    
    # 测试用户资料API
    test_profile_api(access_token)
    
    print("\n=== 认证API测试完成 ===")

if __name__ == "__main__":
    main()