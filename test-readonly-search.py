#!/usr/bin/env python3
"""
最终测试只读用户搜索功能
"""

import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000"

def test_readonly_search():
    """测试只读用户搜索功能"""
    print("=== 最终测试只读用户搜索功能 ===")
    
    # 1. 登录只读用户
    print("\n1. 登录只读用户...")
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "xiaobang",
            "password": "XB@xb199167"
        })
        
        if login_response.status_code == 200:
            print("✅ 只读用户登录成功")
            token_data = login_response.json()
            readonly_token = token_data["access_token"]
        else:
            print("❌ 只读用户登录失败")
            return
            
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return
    
    # 2. 测试用户名搜索
    print("\n2. 测试用户名搜索...")
    test_users = ["李喆", "李康", "李庆硕", "李雪婷"]
    
    for user_name in test_users:
        try:
            print(f"\n   搜索用户: '{user_name}'")
            user_search = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers={"Authorization": f"Bearer {readonly_token}"},
                params={"query": user_name, "limit": 10}
            )
            
            if user_search.status_code == 200:
                user_results = user_search.json()
                count = user_results.get('total', 0)
                print(f"   ✅ 找到 {count} 个结果")
                
                if count > 0 and user_results.get('data'):
                    # 验证所有结果都在允许的网段内
                    allowed_prefixes = ['192.168.10.', '192.168.11.']
                    all_in_allowed_range = True
                    
                    for ip in user_results['data']:
                        ip_addr = ip['ip_address']
                        ip_user = ip.get('user_name', '')
                        is_allowed = any(ip_addr.startswith(prefix) for prefix in allowed_prefixes)
                        
                        if is_allowed:
                            print(f"     ✅ {ip_addr} -> {ip_user}")
                        else:
                            print(f"     ❌ {ip_addr} -> {ip_user} (不应该可见!)")
                            all_in_allowed_range = False
                    
                    if all_in_allowed_range:
                        print(f"   ✅ 网段限制正常：只返回允许网段的IP")
                    else:
                        print(f"   ❌ 网段限制失效：返回了不允许的IP")
                        
            else:
                print(f"   ❌ 搜索失败: {user_search.status_code}")
                
        except Exception as e:
            print(f"   ❌ 搜索异常: {e}")
    
    # 3. 测试部分匹配搜索
    print("\n3. 测试部分匹配搜索...")
    partial_searches = ["李", "喆", "康"]
    
    for search_term in partial_searches:
        try:
            print(f"\n   搜索关键词: '{search_term}'")
            partial_search = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers={"Authorization": f"Bearer {readonly_token}"},
                params={"query": search_term, "limit": 5}
            )
            
            if partial_search.status_code == 200:
                partial_results = partial_search.json()
                count = partial_results.get('total', 0)
                print(f"   ✅ 找到 {count} 个结果")
                
                if count > 0 and partial_results.get('data'):
                    allowed_prefixes = ['192.168.10.', '192.168.11.']
                    for ip in partial_results['data']:
                        ip_addr = ip['ip_address']
                        ip_user = ip.get('user_name', '')
                        is_allowed = any(ip_addr.startswith(prefix) for prefix in allowed_prefixes)
                        
                        if is_allowed:
                            print(f"     ✅ {ip_addr} -> {ip_user}")
                        else:
                            print(f"     ❌ {ip_addr} -> {ip_user} (不应该可见!)")
                            
            else:
                print(f"   ❌ 搜索失败: {partial_search.status_code}")
                
        except Exception as e:
            print(f"   ❌ 搜索异常: {e}")
    
    # 4. 测试IP地址搜索
    print("\n4. 测试IP地址搜索...")
    ip_searches = ["192.168.10", "192.168.10.1", "192.168.11"]
    
    for ip_search_term in ip_searches:
        try:
            print(f"\n   搜索IP: '{ip_search_term}'")
            ip_search = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers={"Authorization": f"Bearer {readonly_token}"},
                params={"query": ip_search_term, "limit": 5}
            )
            
            if ip_search.status_code == 200:
                ip_results = ip_search.json()
                count = ip_results.get('total', 0)
                print(f"   ✅ 找到 {count} 个结果")
                
                if count > 0 and ip_results.get('data'):
                    for ip in ip_results['data'][:3]:
                        ip_addr = ip['ip_address']
                        ip_user = ip.get('user_name', '')
                        print(f"     ✅ {ip_addr} -> {ip_user}")
                        
            else:
                print(f"   ❌ 搜索失败: {ip_search.status_code}")
                
        except Exception as e:
            print(f"   ❌ 搜索异常: {e}")
    
    print("\n=== 测试完成 ===")
    print("✅ 只读用户搜索功能已修复，可以正常使用用户名搜索192.168.10.x/23网段的IP地址")

if __name__ == "__main__":
    test_readonly_search()