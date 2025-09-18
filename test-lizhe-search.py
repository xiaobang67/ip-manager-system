#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门测试"李喆"搜索精准度
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

def test_lizhe_search(token):
    """测试李喆搜索的精准度"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 测试'李喆'搜索精准度")
    print("=" * 60)
    
    try:
        # 搜索"李喆"
        response = requests.get(
            f"{BASE_URL}/api/ips/search",
            headers=headers,
            params={
                "query": "李喆",
                "limit": 20  # 获取更多结果进行分析
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', [])
            total = data.get('total', 0)
            
            print(f"✅ 搜索成功，总共找到 {total} 条记录")
            print(f"📊 显示前 {min(len(results), 20)} 条结果:")
            print()
            
            # 分析搜索结果
            exact_matches = 0
            partial_matches = 0
            irrelevant_results = 0
            
            for i, result in enumerate(results, 1):
                ip = result.get('ip_address', 'N/A')
                user_name = result.get('user_name', 'N/A')
                assigned_to = result.get('assigned_to', 'N/A')
                description = result.get('description', 'N/A')
                
                # 分析匹配类型
                match_type = ""
                is_relevant = False
                
                if user_name == "李喆" or assigned_to == "李喆":
                    match_type = "🎯 精确匹配"
                    exact_matches += 1
                    is_relevant = True
                elif "李喆" in str(user_name) or "李喆" in str(assigned_to):
                    match_type = "🔍 部分匹配"
                    partial_matches += 1
                    is_relevant = True
                elif "李喆" in str(description):
                    match_type = "📝 描述匹配"
                    partial_matches += 1
                    is_relevant = True
                else:
                    match_type = "❓ 无关结果"
                    irrelevant_results += 1
                
                # 显示结果
                relevance_indicator = "✅" if is_relevant else "❌"
                print(f"{relevance_indicator} {i:2d}. {match_type}")
                print(f"      IP地址: {ip}")
                print(f"      用户名: {user_name}")
                print(f"      分配给: {assigned_to}")
                if description and description != 'N/A' and description != 'None':
                    print(f"      描述: {description}")
                print()
            
            # 统计分析
            print("=" * 60)
            print("📈 搜索结果分析:")
            print(f"   🎯 精确匹配: {exact_matches} 条 ({exact_matches/len(results)*100:.1f}%)")
            print(f"   🔍 部分匹配: {partial_matches} 条 ({partial_matches/len(results)*100:.1f}%)")
            print(f"   ❓ 无关结果: {irrelevant_results} 条 ({irrelevant_results/len(results)*100:.1f}%)")
            
            # 精准度评估
            relevant_results = exact_matches + partial_matches
            precision = relevant_results / len(results) * 100 if results else 0
            
            print(f"\n🎯 搜索精准度: {precision:.1f}%")
            
            if precision >= 90:
                print("✅ 搜索精准度优秀！")
            elif precision >= 70:
                print("⚠️  搜索精准度良好，但仍有改进空间")
            else:
                print("❌ 搜索精准度需要进一步优化")
                
        else:
            print(f"❌ 搜索失败: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ 搜索异常: {e}")

def main():
    """主函数"""
    print("🚀 启动'李喆'搜索精准度专项测试")
    
    # 登录
    token = login()
    if not token:
        print("❌ 无法获取访问令牌，测试终止")
        sys.exit(1)
    
    # 测试李喆搜索
    test_lizhe_search(token)
    
    print("\n💡 优化建议:")
    print("1. 精确匹配的结果应该排在最前面")
    print("2. 避免返回与搜索关键词无关的IP地址")
    print("3. 优先在用户名和分配人字段中搜索")
    print("4. 减少在描述等次要字段中的模糊匹配")

if __name__ == "__main__":
    main()