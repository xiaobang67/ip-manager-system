#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试只读账号分页修复效果
"""
import requests
import json
import sys
import time

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

def test_pagination_consistency(token):
    """测试分页一致性"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 测试分页一致性修复效果")
    print("=" * 70)
    
    query = "李喆"
    page_size = 20
    
    # 收集所有页面的结果
    all_results = []
    page_results = {}
    
    try:
        # 测试前5页
        for page in range(1, 6):
            skip = (page - 1) * page_size
            
            print(f"\n📄 测试第{page}页 (skip={skip}, limit={page_size}):")
            
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
                print(f"   当前页记录数: {len(results)}")
                
                if results:
                    page_results[page] = results
                    all_results.extend(results)
                    
                    # 检查相关性
                    relevant_count = 0
                    irrelevant_count = 0
                    irrelevant_ips = []
                    
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
                            irrelevant_ips.append(result.get('ip_address', 'N/A'))
                    
                    relevance_rate = (relevant_count / len(results)) * 100 if results else 0
                    print(f"   相关结果: {relevant_count} 条")
                    print(f"   无关结果: {irrelevant_count} 条")
                    print(f"   相关度: {relevance_rate:.1f}%")
                    
                    if irrelevant_count > 0:
                        print(f"   ⚠️  发现无关结果: {', '.join(irrelevant_ips[:5])}")
                        if len(irrelevant_ips) > 5:
                            print(f"      ... 还有 {len(irrelevant_ips) - 5} 个")
                    else:
                        print(f"   ✅ 所有结果都相关!")
                else:
                    print("   ℹ️  本页无结果")
                    break
            else:
                print(f"   ❌ 请求失败: {response.status_code}")
                break
                
            # 短暂延迟，避免请求过快
            time.sleep(0.1)
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False
    
    # 分析整体结果
    print(f"\n📊 整体分析:")
    print(f"   总共测试页数: {len(page_results)}")
    print(f"   总共获取记录: {len(all_results)}")
    
    if all_results:
        # 检查是否有重复的IP地址
        ip_addresses = [result.get('ip_address') for result in all_results]
        unique_ips = set(ip_addresses)
        
        print(f"   唯一IP地址数: {len(unique_ips)}")
        
        if len(ip_addresses) != len(unique_ips):
            print(f"   ⚠️  发现重复IP地址!")
            # 找出重复的IP
            seen = set()
            duplicates = set()
            for ip in ip_addresses:
                if ip in seen:
                    duplicates.add(ip)
                else:
                    seen.add(ip)
            print(f"   重复的IP: {', '.join(list(duplicates)[:10])}")
        else:
            print(f"   ✅ 没有重复IP地址")
        
        # 检查整体相关性
        total_relevant = 0
        total_irrelevant = 0
        
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
                total_relevant += 1
            else:
                total_irrelevant += 1
        
        overall_relevance = (total_relevant / len(all_results)) * 100 if all_results else 0
        print(f"   整体相关度: {overall_relevance:.1f}%")
        
        if total_irrelevant == 0:
            print(f"   🎉 修复成功！所有结果都相关!")
            return True
        else:
            print(f"   ❌ 仍有问题：{total_irrelevant} 条无关结果")
            return False
    else:
        print(f"   ℹ️  没有获取到任何结果")
        return False

def test_different_queries(token):
    """测试不同查询的分页一致性"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔄 测试不同查询的分页一致性")
    print("=" * 50)
    
    test_queries = ["李喆", "192.168.1", "admin", "研发中心"]
    
    for query in test_queries:
        print(f"\n🔍 测试查询: '{query}'")
        print("-" * 30)
        
        try:
            # 测试第2页
            params = {
                "query": query,
                "skip": 20,
                "limit": 10
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
                
                if results:
                    # 检查相关性
                    relevant_count = sum(1 for result in results 
                                       if query in str(result.get('user_name', '')) or 
                                          query in str(result.get('assigned_to', '')) or
                                          query in str(result.get('ip_address', '')) or
                                          query in str(result.get('description', '')))
                    
                    irrelevant_count = len(results) - relevant_count
                    relevance_rate = (relevant_count / len(results)) * 100 if results else 0
                    
                    print(f"   相关结果: {relevant_count} 条")
                    print(f"   无关结果: {irrelevant_count} 条")
                    print(f"   相关度: {relevance_rate:.1f}%")
                    
                    if irrelevant_count == 0:
                        print(f"   ✅ 查询 '{query}' 分页正常")
                    else:
                        print(f"   ⚠️  查询 '{query}' 分页有问题")
                else:
                    print(f"   ℹ️  查询 '{query}' 无结果")
            else:
                print(f"   ❌ 查询 '{query}' 请求失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 查询 '{query}' 异常: {e}")

def main():
    """主函数"""
    print("🚀 启动只读账号分页修复测试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取只读账号访问令牌，测试终止")
        sys.exit(1)
    
    print(f"✅ 只读账号登录成功")
    
    # 测试分页一致性
    success = test_pagination_consistency(token)
    
    # 测试不同查询
    test_different_queries(token)
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 测试结果: 分页修复成功!")
        print("✅ 只读账号搜索分页功能正常工作")
    else:
        print("❌ 测试结果: 分页仍有问题")
        print("🔧 需要进一步检查和修复")
    
    print("\n💡 修复说明:")
    print("1. 修复了只读用户搜索时未保存搜索参数的问题")
    print("2. 现在分页时会保持搜索状态，不会显示无关结果")
    print("3. 前端已重新构建，修复应该生效")

if __name__ == "__main__":
    main()