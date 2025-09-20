#!/usr/bin/env python3
"""
测试只读用户网段限制功能
验证只读用户只能查询192.168.10.0/23网段的IP地址
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"

def test_readonly_user_subnet_limit():
    """测试只读用户的网段限制"""
    print("=== 测试只读用户网段限制功能 ===")
    
    # 1. 登录只读用户
    print("\n1. 登录只读用户...")
    try:
        # 使用现有的只读用户
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "xiaobang",
            "password": "XB@xb199167"
        })
        
        if login_response.status_code == 200:
            print("✅ 只读用户已存在，登录成功")
            token_data = login_response.json()
            readonly_token = token_data["access_token"]
        else:
            print("❌ 只读用户不存在或登录失败")
            return
            
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 2. 测试管理员用户（对比）
    print("\n2. 测试管理员用户搜索（对比）...")
    try:
        admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        if admin_login.status_code == 200:
            admin_token = admin_login.json()["access_token"]
            
            # 管理员搜索所有IP
            admin_search = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers={"Authorization": f"Bearer {admin_token}"},
                params={"limit": 100}
            )
            
            if admin_search.status_code == 200:
                admin_results = admin_search.json()
                print(f"✅ 管理员可以查看 {admin_results.get('total', 0)} 个IP地址")
                
                # 显示一些IP地址示例
                if admin_results.get('data'):
                    print("   管理员可见的IP地址示例:")
                    for ip in admin_results['data'][:5]:
                        print(f"   - {ip['ip_address']}")
            else:
                print(f"❌ 管理员搜索失败: {admin_search.status_code}")
        else:
            print("❌ 管理员登录失败")
            
    except Exception as e:
        print(f"❌ 管理员测试失败: {e}")
    
    # 3. 测试只读用户搜索
    print("\n3. 测试只读用户搜索...")
    try:
        # 只读用户搜索所有IP
        readonly_search = requests.get(
            f"{BASE_URL}/api/ips/search",
            headers={"Authorization": f"Bearer {readonly_token}"},
            params={"limit": 100}
        )
        
        if readonly_search.status_code == 200:
            readonly_results = readonly_search.json()
            print(f"✅ 只读用户可以查看 {readonly_results.get('total', 0)} 个IP地址")
            
            # 验证所有IP都在允许的网段内
            allowed_prefixes = ['192.168.10.', '192.168.11.']
            all_in_allowed_range = True
            
            if readonly_results.get('data'):
                print("   只读用户可见的IP地址:")
                for ip in readonly_results['data']:
                    ip_addr = ip['ip_address']
                    is_allowed = any(ip_addr.startswith(prefix) for prefix in allowed_prefixes)
                    
                    if is_allowed:
                        print(f"   ✅ {ip_addr} (允许)")
                    else:
                        print(f"   ❌ {ip_addr} (不应该可见!)")
                        all_in_allowed_range = False
                
                if all_in_allowed_range:
                    print("✅ 网段限制正常工作：只读用户只能看到192.168.10.0/23网段的IP")
                else:
                    print("❌ 网段限制失效：只读用户看到了不应该看到的IP地址")
            else:
                print("   没有找到IP地址数据")
                
        else:
            print(f"❌ 只读用户搜索失败: {readonly_search.status_code}")
            print(f"   响应内容: {readonly_search.text}")
            
    except Exception as e:
        print(f"❌ 只读用户测试失败: {e}")
    
    # 4. 测试特定搜索
    print("\n4. 测试只读用户特定搜索...")
    test_queries = [
        "192.168.10",      # 允许的网段
        "192.168.11",      # 允许的网段
        "192.168.1",       # 不允许的网段
        "10.0.0",          # 不允许的网段
    ]
    
    for query in test_queries:
        try:
            search_response = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers={"Authorization": f"Bearer {readonly_token}"},
                params={"query": query, "limit": 10}
            )
            
            if search_response.status_code == 200:
                results = search_response.json()
                count = results.get('total', 0)
                
                if query.startswith('192.168.10') or query.startswith('192.168.11'):
                    print(f"   ✅ 搜索 '{query}': 找到 {count} 个结果 (允许)")
                else:
                    if count == 0:
                        print(f"   ✅ 搜索 '{query}': 找到 {count} 个结果 (正确限制)")
                    else:
                        print(f"   ❌ 搜索 '{query}': 找到 {count} 个结果 (应该被限制)")
            else:
                print(f"   ❌ 搜索 '{query}' 失败: {search_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 搜索 '{query}' 异常: {e}")

if __name__ == "__main__":
    test_readonly_user_subnet_limit()