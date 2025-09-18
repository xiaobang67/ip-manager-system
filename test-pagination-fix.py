#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试分页功能修复
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

def test_pagination_fix(token):
    """测试分页功能修复"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 测试'李喆'搜索的分页功能")
    print("=" * 60)
    
    query = "李喆"
    page_size = 5  # 每页5条记录，方便测试
    
    try:
        # 获取第一页
        print(f"📄 第1页 (前{page_size}条记录):")
        response = requests.get(
            f"{BASE_URL}/api/ips/search",
            headers=headers,
            params={
                "query": query,
                "limit": page_size,
                "skip": 0
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            total = data.get('total', 0)
            
            print(f"   总记录数: {total}")
            print("   结果:")
            
            for i, result in enumerate(results, 1):
                ip = result.get('ip_address', 'N/A')
                user_name = result.get('user_name', 'N/A')
                assigned_to = result.get('assigned_to', 'N/A')
                
                # 检查是否与搜索关键词相关
                is_relevant = query in str(user_name) or query in str(assigned_to)
                status = "✅" if is_relevant else "❌"
                
                print(f"      {status} {i}. IP: {ip}, 用户: {user_name}, 分配给: {assigned_to}")
        
        # 获取第二页
        print(f"\n📄 第2页 (第{page_size+1}-{page_size*2}条记录):")
        response = requests.get(
            f"{BASE_URL}/api/ips/search",
            headers=headers,
            params={
                "query": query,
                "limit": page_size,
                "skip": page_size
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            
            print("   结果:")
            
            for i, result in enumerate(results, 1):
                ip = result.get('ip_address', 'N/A')
                user_name = result.get('user_name', 'N/A')
                assigned_to = result.get('assigned_to', 'N/A')
                
                # 检查是否与搜索关键词相关
                is_relevant = query in str(user_name) or query in str(assigned_to)
                status = "✅" if is_relevant else "❌"
                
                print(f"      {status} {i}. IP: {ip}, 用户: {user_name}, 分配给: {assigned_to}")
        
        # 获取第三页
        print(f"\n📄 第3页 (第{page_size*2+1}-{page_size*3}条记录):")
        response = requests.get(
            f"{BASE_URL}/api/ips/search",
            headers=headers,
            params={
                "query": query,
                "limit": page_size,
                "skip": page_size * 2
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            
            print("   结果:")
            
            for i, result in enumerate(results, 1):
                ip = result.get('ip_address', 'N/A')
                user_name = result.get('user_name', 'N/A')
                assigned_to = result.get('assigned_to', 'N/A')
                
                # 检查是否与搜索关键词相关
                is_relevant = query in str(user_name) or query in str(assigned_to)
                status = "✅" if is_relevant else "❌"
                
                print(f"      {status} {i}. IP: {ip}, 用户: {user_name}, 分配给: {assigned_to}")
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主函数"""
    print("🚀 启动分页功能修复测试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        sys.exit(1)
    
    # 测试分页功能
    test_pagination_fix(token)
    
    print("\n" + "=" * 60)
    print("💡 期望结果:")
    print("   - 所有页面的结果都应该包含'李喆'")
    print("   - 不应该出现与'李喆'无关的IP地址")
    print("   - 精确匹配的结果应该排在前面")

if __name__ == "__main__":
    main()