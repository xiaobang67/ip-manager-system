#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索精准度改进
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

def test_search_precision(token):
    """测试搜索精准度"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 测试搜索精准度改进")
    print("=" * 50)
    
    # 测试用例
    test_cases = [
        {
            "name": "中文姓名精确搜索",
            "query": "李喆",
            "description": "搜索中文姓名，应该优先显示精确匹配的结果"
        },
        {
            "name": "中文姓名模糊搜索",
            "query": "李",
            "description": "搜索中文姓氏，应该显示所有包含'李'的用户"
        },
        {
            "name": "IP地址精确搜索",
            "query": "192.168.1.100",
            "description": "搜索完整IP地址，应该只返回精确匹配"
        },
        {
            "name": "IP网段搜索 - C类网段",
            "query": "192.168.1",
            "description": "搜索192.168.1网段，应该只返回192.168.1.x，不包括192.168.10.x等"
        },
        {
            "name": "IP网段搜索 - 带.0后缀",
            "query": "192.168.1.0",
            "description": "搜索192.168.1.0网段，应该只返回192.168.1.x"
        },
        {
            "name": "IP网段搜索 - B类网段",
            "query": "192.168",
            "description": "搜索192.168网段，应该返回所有192.168.x.x"
        },
        {
            "name": "英文用户名搜索",
            "query": "admin",
            "description": "搜索英文用户名，应该优先精确匹配"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print(f"   查询: '{test_case['query']}'")
        print(f"   说明: {test_case['description']}")
        
        try:
            # 执行搜索
            response = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers=headers,
                params={
                    "query": test_case['query'],
                    "limit": 10
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                total = data.get('total', 0)
                
                print(f"   ✅ 搜索成功，找到 {total} 条记录")
                
                if results:
                    print("   📊 前5条结果:")
                    for j, result in enumerate(results[:5], 1):
                        ip = result.get('ip_address', 'N/A')
                        user_name = result.get('user_name', 'N/A')
                        assigned_to = result.get('assigned_to', 'N/A')
                        
                        # 检查匹配度
                        exact_match = ""
                        if test_case['query'] == user_name or test_case['query'] == assigned_to:
                            exact_match = " [精确匹配]"
                        elif test_case['query'] == ip:
                            exact_match = " [IP精确匹配]"
                        
                        print(f"      {j}. IP: {ip}, 用户: {user_name}, 分配给: {assigned_to}{exact_match}")
                else:
                    print("   ℹ️  未找到匹配结果")
                    
            else:
                print(f"   ❌ 搜索失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ 搜索异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 搜索精准度测试完成")
    print("\n💡 优化说明:")
    print("1. 中文查询优先在用户相关字段中搜索")
    print("2. 精确匹配的结果排在前面")
    print("3. IP地址查询只进行精确匹配")
    print("4. 避免在不相关字段中进行模糊匹配")

def main():
    """主函数"""
    print("🚀 启动搜索精准度测试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        sys.exit(1)
    
    # 测试搜索精准度
    test_search_precision(token)

if __name__ == "__main__":
    main()