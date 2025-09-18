#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端实际调用的API端点
"""
import requests
import json
import sys

# 配置
BASE_URL = "http://localhost:8000"
READONLY_USER = "readonly"
READONLY_PASSWORD = "readonly123"

def login():
    """使用只读账号登录获取token"""
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": READONLY_USER,
            "password": READONLY_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"❌ 只读账号登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def test_different_endpoints(token):
    """测试不同的搜索端点"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 测试不同的搜索端点")
    print("=" * 70)
    
    query = "李喆"
    skip = 20  # 第2页
    limit = 20
    
    endpoints = [
        {
            "name": "API扩展端点",
            "url": f"{BASE_URL}/api/ips/search",
            "description": "api_extensions.py中的搜索端点"
        },
        {
            "name": "主API端点", 
            "url": f"{BASE_URL}/ips/search",
            "description": "app/api/v1/endpoints/ips.py中的搜索端点"
        }
    ]
    
    for endpoint in endpoints:
        print(f"\n📡 测试 {endpoint['name']}")
        print(f"   URL: {endpoint['url']}")
        print(f"   说明: {endpoint['description']}")
        print("-" * 50)
        
        try:
            params = {
                "query": query,
                "skip": skip,
                "limit": limit
            }
            
            response = requests.get(
                endpoint['url'],
                headers=headers,
                params=params
            )
            
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查响应格式
                if isinstance(data, dict) and 'data' in data:
                    # 新格式：{data: [...], total: number}
                    results = data.get('data', [])
                    total = data.get('total', 0)
                    print(f"   响应格式: 标准格式 (data + total)")
                    print(f"   总记录数: {total}")
                    print(f"   当前页记录数: {len(results)}")
                elif isinstance(data, list):
                    # 旧格式：直接返回数组
                    results = data
                    print(f"   响应格式: 数组格式")
                    print(f"   当前页记录数: {len(results)}")
                else:
                    print(f"   响应格式: 未知格式")
                    print(f"   响应内容: {str(data)[:200]}...")
                    continue
                
                # 检查结果相关性
                if results:
                    relevant_count = 0
                    irrelevant_count = 0
                    
                    for result in results:
                        user_name = result.get('user_name', '')
                        assigned_to = result.get('assigned_to', '')
                        description = result.get('description', '')
                        
                        is_relevant = (
                            query in str(user_name) or 
                            query in str(assigned_to) or
                            (description and query in str(description))
                        )
                        
                        if is_relevant:
                            relevant_count += 1
                        else:
                            irrelevant_count += 1
                    
                    relevance_rate = (relevant_count / len(results)) * 100 if results else 0
                    print(f"   相关结果: {relevant_count} 条")
                    print(f"   无关结果: {irrelevant_count} 条")
                    print(f"   相关度: {relevance_rate:.1f}%")
                    
                    if irrelevant_count > 0:
                        print(f"   ⚠️  发现无关结果!")
                        # 显示前3个无关结果
                        irrelevant_results = [r for r in results 
                                            if not (query in str(r.get('user_name', '')) or 
                                                   query in str(r.get('assigned_to', '')) or
                                                   query in str(r.get('description', '')))]
                        for i, result in enumerate(irrelevant_results[:3], 1):
                            ip = result.get('ip_address', 'N/A')
                            user_name = result.get('user_name', 'N/A')
                            assigned_to = result.get('assigned_to', 'N/A')
                            print(f"      {i}. IP: {ip}, 用户: {user_name}, 分配给: {assigned_to}")
                    else:
                        print(f"   ✅ 所有结果都相关!")
                else:
                    print("   ℹ️  无结果")
                    
            elif response.status_code == 404:
                print(f"   ❌ 端点不存在")
            else:
                print(f"   ❌ 请求失败: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")

def test_nginx_routing():
    """测试Nginx路由配置"""
    print("\n🌐 测试Nginx路由配置")
    print("=" * 50)
    
    # 测试不同的路径
    test_urls = [
        f"{BASE_URL}/api/ips/search",
        f"{BASE_URL}/ips/search"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, params={"query": "test"})
            print(f"   {url}: {response.status_code}")
        except Exception as e:
            print(f"   {url}: 异常 - {e}")

def main():
    """主函数"""
    print("🚀 启动API端点测试")
    
    # 测试Nginx路由
    test_nginx_routing()
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取只读账号访问令牌，测试终止")
        sys.exit(1)
    
    print(f"✅ 只读账号登录成功")
    
    # 测试不同端点
    test_different_endpoints(token)
    
    print("\n" + "=" * 70)
    print("🎯 分析结论:")
    print("1. 如果两个端点返回不同的结果，说明前端可能调用了错误的端点")
    print("2. 如果只有一个端点有问题，说明问题在特定的实现中")
    print("3. 检查前端实际使用的是哪个端点")

if __name__ == "__main__":
    main()