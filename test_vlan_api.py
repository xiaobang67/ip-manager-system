#!/usr/bin/env python3
"""
测试VLAN API
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api"

def test_vlan_api():
    """测试VLAN API"""
    print("=== 测试VLAN API ===")
    
    # 1. 先登录获取token
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    
    try:
        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"登录响应状态: {login_response.status_code}")
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get("access_token")
            print(f"获取到token: {token[:20]}...")
            
            # 设置认证头
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # 2. 测试获取所有网段
            print("\n--- 测试获取所有网段 ---")
            subnets_response = requests.get(f"{BASE_URL}/subnets", headers=headers)
            print(f"获取网段响应状态: {subnets_response.status_code}")
            
            if subnets_response.status_code == 200:
                subnets_data = subnets_response.json()
                print(f"网段数量: {len(subnets_data.get('subnets', []))}")
                
                # 显示所有网段的VLAN ID
                for subnet in subnets_data.get('subnets', []):
                    print(f"  - 网段: {subnet['network']}, VLAN ID: {subnet.get('vlan_id', 'None')}")
            
            # 3. 测试VLAN搜索（使用搜索端点）
            print("\n--- 测试VLAN搜索 ---")
            test_vlan_ids = [220, 100, 200, 300, 105, 99, 101, 10, 996]
            
            for vlan_id in test_vlan_ids:
                print(f"\n测试VLAN ID: {vlan_id}")
                # 使用搜索端点进行VLAN过滤
                search_params = {"vlan_id": vlan_id}
                vlan_response = requests.get(f"{BASE_URL}/subnets/search", params=search_params, headers=headers)
                print(f"响应状态: {vlan_response.status_code}")
                
                if vlan_response.status_code == 200:
                    vlan_data = vlan_response.json()
                    # 处理不同的响应格式
                    subnets = []
                    if isinstance(vlan_data, dict) and 'subnets' in vlan_data:
                        subnets = vlan_data['subnets']
                    elif isinstance(vlan_data, list):
                        subnets = vlan_data
                    
                    print(f"找到 {len(subnets)} 个网段")
                    for subnet in subnets:
                        print(f"  - {subnet['network']}: {subnet.get('description', 'No description')} (VLAN: {subnet.get('vlan_id', 'None')})")
                else:
                    print(f"错误: {vlan_response.text}")
        else:
            print(f"登录失败: {login_response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    test_vlan_api()