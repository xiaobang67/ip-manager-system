#!/usr/bin/env python3
"""
API端点测试脚本
用于验证后端API是否正常工作
"""

import requests
import json
import sys

# API基础URL
BASE_URL = "http://localhost:8000"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """测试API端点"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        elif method.upper() == 'PUT':
            response = requests.put(url, json=data, timeout=10)
        else:
            print(f"❌ 不支持的HTTP方法: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - 状态码: {response.status_code}")
            if response.content:
                try:
                    data = response.json()
                    if isinstance(data, dict) and len(data) > 0:
                        print(f"   📊 返回数据示例: {list(data.keys())[:5]}")
                    elif isinstance(data, list) and len(data) > 0:
                        print(f"   📊 返回列表长度: {len(data)}")
                except:
                    print(f"   📄 返回内容长度: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ {method} {endpoint} - 期望状态码: {expected_status}, 实际: {response.status_code}")
            if response.content:
                print(f"   错误信息: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - 连接错误: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试IPAM后端API端点...")
    print("=" * 60)
    
    # 测试基础端点
    print("\n📋 基础端点测试:")
    test_endpoint('GET', '/')
    test_endpoint('GET', '/health')
    
    # 测试统计端点
    print("\n📊 统计端点测试:")
    test_endpoint('GET', '/api/v1/stats')
    
    # 测试监控端点
    print("\n📈 监控端点测试:")
    test_endpoint('GET', '/api/monitoring/dashboard')
    test_endpoint('GET', '/api/monitoring/ip-utilization')
    test_endpoint('GET', '/api/monitoring/subnet-utilization')
    test_endpoint('GET', '/api/monitoring/allocation-trends')
    test_endpoint('GET', '/api/monitoring/top-utilized-subnets')
    test_endpoint('GET', '/api/monitoring/alerts/statistics')
    test_endpoint('GET', '/api/monitoring/alerts/history')
    
    # 测试网段管理端点
    print("\n🌐 网段管理端点测试:")
    test_endpoint('GET', '/api/v1/subnets')
    test_endpoint('GET', '/api/v1/subnets/1')
    
    # 测试IP地址管理端点
    print("\n🔢 IP地址管理端点测试:")
    test_endpoint('GET', '/api/v1/ip-addresses')
    test_endpoint('GET', '/api/v1/ip-addresses?subnet_id=1')
    
    # 测试认证端点
    print("\n🔐 认证端点测试:")
    login_data = {
        "username": "admin",
        "password": "admin"
    }
    test_endpoint('POST', '/api/auth/login', login_data)
    test_endpoint('GET', '/api/auth/verify')
    test_endpoint('GET', '/api/auth/profile')
    
    print("\n" + "=" * 60)
    print("✨ API端点测试完成!")

if __name__ == "__main__":
    main()