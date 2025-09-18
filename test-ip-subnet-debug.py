#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试IP网段搜索问题
"""
import requests
import json
import sys

# 配置
BASE_URL = "http://localhost:8000"
TEST_USER = "admin"
TEST_PASSWORD = "XB@xb199167"

def login():
    """登录获取token"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": TEST_USER,
            "password": TEST_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def debug_ip_search(token):
    """调试IP搜索问题"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 调试IP网段搜索问题")
    print("=" * 60)
    
    # 测试不同的搜索查询
    test_queries = [
        "192.168.1",
        "192.168.1.0",
        "192.168.10", 
        "192.168.0",
        "172.30"
    ]
    
    for query in test_queries:
        print(f"\n📋 测试查询: '{query}'")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers=headers,
                params={
                    "query": query,
                    "limit": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                total = data.get('total', 0)
                
                print(f"   总数: {total} 条")
                print("   前10条结果:")
                
                # 分析结果
                correct_matches = 0
                incorrect_matches = 0
                
                for i, result in enumerate(results, 1):
                    ip = result.get('ip_address', 'N/A')
                    
                    # 检查是否是正确的匹配
                    if query == "192.168.1":
                        # 应该只匹配 192.168.1.x
                        is_correct = ip.startswith("192.168.1.") and not ip.startswith("192.168.10.")
                    elif query == "192.168.10":
                        # 应该只匹配 192.168.10.x
                        is_correct = ip.startswith("192.168.10.")
                    elif query == "192.168.0":
                        # 应该只匹配 192.168.0.x
                        is_correct = ip.startswith("192.168.0.")
                    elif query == "172.30":
                        # 应该只匹配 172.30.x.x
                        is_correct = ip.startswith("172.30.")
                    else:
                        is_correct = True
                    
                    if is_correct:
                        correct_matches += 1
                        status = "✅"
                    else:
                        incorrect_matches += 1
                        status = "❌"
                    
                    print(f"      {status} {i:2d}. {ip}")
                
                # 统计
                if results:
                    accuracy = correct_matches / len(results) * 100
                    print(f"   准确率: {accuracy:.1f}% ({correct_matches}/{len(results)})")
                    
            else:
                print(f"   ❌ 搜索失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ 搜索异常: {e}")

def main():
    """主函数"""
    print("🚀 启动IP网段搜索调试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        sys.exit(1)
    
    # 调试IP搜索
    debug_ip_search(token)

if __name__ == "__main__":
    main()