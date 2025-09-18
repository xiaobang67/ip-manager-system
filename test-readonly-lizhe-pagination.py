#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试只读账号搜索"李喆"的分页问题
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

def test_lizhe_pagination(token):
    """测试李喆搜索的分页问题"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 测试只读账号搜索'李喆'的分页问题")
    print("=" * 70)
    
    query = "李喆"
    page_size = 10  # 每页10条记录
    
    try:
        # 测试前3页
        for page in range(1, 4):
            skip = (page - 1) * page_size
            
            print(f"\n📄 第{page}页 (skip={skip}, limit={page_size}):")
            print("-" * 50)
            
            response = requests.get(
                f"{BASE_URL}/api/ips/search",
                headers=headers,
                params={
                    "query": query,
                    "limit": page_size,
                    "skip": skip
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                total = data.get('total', 0)
                
                print(f"   总记录数: {total}")
                print(f"   当前页记录数: {len(results)}")
                
                if results:
                    print("   结果详情:")
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
                    print(f"   📊 本页统计:")
                    print(f"      相关结果: {relevant_count} 条")
                    print(f"      无关结果: {irrelevant_count} 条")
                    print(f"      相关度: {relevance_rate:.1f}%")
                    
                    if relevance_rate < 50:
                        print(f"      ⚠️  警告: 第{page}页相关度过低!")
                    elif relevance_rate == 100:
                        print(f"      ✅ 第{page}页相关度完美!")
                else:
                    print("   ℹ️  本页无结果")
            else:
                print(f"   ❌ 搜索失败: {response.status_code} - {response.text}")
                
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def test_search_consistency(token):
    """测试搜索结果的一致性"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔄 测试搜索结果一致性")
    print("=" * 50)
    
    query = "李喆"
    
    try:
        # 获取所有结果（不分页）
        response = requests.get(
            f"{BASE_URL}/api/ips/search",
            headers=headers,
            params={
                "query": query,
                "limit": 1000  # 获取大量结果
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            all_results = data.get('data', [])
            total = data.get('total', 0)
            
            print(f"📊 搜索统计:")
            print(f"   总记录数: {total}")
            print(f"   实际返回: {len(all_results)}")
            
            # 分析所有结果的相关性
            relevant_results = []
            irrelevant_results = []
            
            for result in all_results:
                user_name = result.get('user_name', '')
                assigned_to = result.get('assigned_to', '')
                description = result.get('description', '')
                
                is_relevant = (
                    query in str(user_name) or 
                    query in str(assigned_to) or
                    (description and query in str(description))
                )
                
                if is_relevant:
                    relevant_results.append(result)
                else:
                    irrelevant_results.append(result)
            
            print(f"\n📈 相关性分析:")
            print(f"   相关结果: {len(relevant_results)} 条 ({len(relevant_results)/len(all_results)*100:.1f}%)")
            print(f"   无关结果: {len(irrelevant_results)} 条 ({len(irrelevant_results)/len(all_results)*100:.1f}%)")
            
            if irrelevant_results:
                print(f"\n❌ 发现无关结果示例:")
                for i, result in enumerate(irrelevant_results[:5], 1):
                    ip = result.get('ip_address', 'N/A')
                    user_name = result.get('user_name', 'N/A')
                    assigned_to = result.get('assigned_to', 'N/A')
                    print(f"   {i}. IP: {ip}, 用户: {user_name}, 分配给: {assigned_to}")
            
        else:
            print(f"❌ 搜索失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")

def main():
    """主函数"""
    print("🚀 启动只读账号'李喆'搜索分页问题测试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取只读账号访问令牌，测试终止")
        sys.exit(1)
    
    print(f"✅ 只读账号登录成功")
    
    # 测试分页问题
    test_lizhe_pagination(token)
    
    # 测试搜索一致性
    test_search_consistency(token)
    
    print("\n" + "=" * 70)
    print("🎯 问题诊断:")
    print("1. 检查第2页、第3页是否出现与'李喆'无关的结果")
    print("2. 验证搜索逻辑是否在分页时保持一致")
    print("3. 确认只读账号的权限是否影响搜索结果")
    
    print("\n💡 可能的原因:")
    print("1. 搜索SQL查询在分页时参数传递错误")
    print("2. 相关性排序逻辑在分页时不一致")
    print("3. 只读账号的数据访问权限问题")

if __name__ == "__main__":
    main()