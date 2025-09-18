#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟前端分页请求，测试只读账号搜索"李喆"的分页问题
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

def simulate_frontend_pagination(token):
    """模拟前端的分页请求"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 模拟前端分页请求 - 搜索'李喆'")
    print("=" * 70)
    
    query = "李喆"
    page_size = 20  # 前端默认每页20条
    
    # 模拟前端的分页逻辑
    for page in range(1, 4):
        current_page = page
        skip = (current_page - 1) * page_size
        
        print(f"\n📄 第{page}页 (currentPage={current_page}, skip={skip}, limit={page_size}):")
        print("-" * 60)
        
        try:
            # 完全模拟前端的请求参数
            params = {
                "query": query,
                "skip": skip,
                "limit": page_size
            }
            
            print(f"   🔗 请求参数: {params}")
            
            response = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers=headers,
                params=params
            )
            
            print(f"   📡 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                total = data.get('total', 0)
                returned_skip = data.get('skip', 0)
                returned_limit = data.get('limit', 0)
                
                print(f"   📊 响应数据:")
                print(f"      总记录数: {total}")
                print(f"      返回skip: {returned_skip}")
                print(f"      返回limit: {returned_limit}")
                print(f"      当前页记录数: {len(results)}")
                
                if results:
                    print("   📋 结果详情:")
                    relevant_count = 0
                    irrelevant_count = 0
                    
                    for i, result in enumerate(results, 1):
                        ip = result.get('ip_address', 'N/A')
                        user_name = result.get('user_name', 'N/A')
                        assigned_to = result.get('assigned_to', 'N/A')
                        description = result.get('description', 'N/A')
                        
                        # 检查是否与"李喆"相关
                        is_relevant = (
                            query in str(user_name) or 
                            query in str(assigned_to) or
                            (description and query in str(description))
                        )
                        
                        if is_relevant:
                            status_icon = "✅"
                            relevant_count += 1
                        else:
                            status_icon = "❌"
                            irrelevant_count += 1
                        
                        print(f"      {status_icon} {i:2d}. IP: {ip}")
                        print(f"           用户名: {user_name}")
                        print(f"           分配给: {assigned_to}")
                        if description and description not in ['N/A', 'None', '']:
                            print(f"           描述: {description}")
                        print()
                    
                    # 统计本页相关性
                    relevance_rate = (relevant_count / len(results)) * 100 if results else 0
                    print(f"   📈 本页统计:")
                    print(f"      相关结果: {relevant_count} 条")
                    print(f"      无关结果: {irrelevant_count} 条")
                    print(f"      相关度: {relevance_rate:.1f}%")
                    
                    if irrelevant_count > 0:
                        print(f"      ⚠️  警告: 第{page}页发现{irrelevant_count}条无关结果!")
                    elif relevance_rate == 100:
                        print(f"      ✅ 第{page}页相关度完美!")
                else:
                    print("   ℹ️  本页无结果")
            else:
                print(f"   ❌ 搜索失败: {response.status_code}")
                print(f"   📄 错误详情: {response.text}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")

def test_different_page_sizes(token):
    """测试不同页面大小的分页"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔄 测试不同页面大小的分页")
    print("=" * 50)
    
    query = "李喆"
    page_sizes = [10, 20, 50]
    
    for page_size in page_sizes:
        print(f"\n📏 页面大小: {page_size}")
        print("-" * 30)
        
        # 测试第2页
        current_page = 2
        skip = (current_page - 1) * page_size
        
        try:
            params = {
                "query": query,
                "skip": skip,
                "limit": page_size
            }
            
            response = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                total = data.get('total', 0)
                
                print(f"   总记录数: {total}")
                print(f"   第2页记录数: {len(results)}")
                
                # 检查相关性
                relevant_count = sum(1 for result in results 
                                   if query in str(result.get('user_name', '')) or 
                                      query in str(result.get('assigned_to', '')) or
                                      query in str(result.get('description', '')))
                
                irrelevant_count = len(results) - relevant_count
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
                print(f"   ❌ 搜索失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {e}")

def main():
    """主函数"""
    print("🚀 启动前端分页请求模拟测试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取只读账号访问令牌，测试终止")
        sys.exit(1)
    
    print(f"✅ 只读账号登录成功")
    
    # 模拟前端分页请求
    simulate_frontend_pagination(token)
    
    # 测试不同页面大小
    test_different_page_sizes(token)
    
    print("\n" + "=" * 70)
    print("🎯 测试总结:")
    print("1. 如果第2页、第3页出现无关结果，说明分页逻辑有问题")
    print("2. 如果不同页面大小都有问题，说明是搜索逻辑的问题")
    print("3. 如果只有特定页面大小有问题，说明是分页计算的问题")

if __name__ == "__main__":
    main()