#!/usr/bin/env python3
"""
生成测试IP地址数据的脚本
"""
import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api"

# 登录获取token
def login():
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"登录失败: {response.text}")
        return None

# 创建网段
def create_subnet(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    subnet_data = {
        "network": "192.168.1.0/24",
        "netmask": "255.255.255.0",
        "description": "测试网段",
        "vlan_id": 100,
        "gateway": "192.168.1.1",
        "dns_servers": ["8.8.8.8", "8.8.4.4"]
    }
    
    response = requests.post(f"{BASE_URL}/subnets", json=subnet_data, headers=headers)
    if response.status_code == 200:
        subnet = response.json()
        print(f"创建网段成功: {subnet['network']}")
        return subnet["id"]
    else:
        print(f"创建网段失败: {response.text}")
        return None

# 同步网段IP地址
def sync_subnet_ips(token, subnet_id):
    headers = {"Authorization": f"Bearer {token}"}
    
    sync_data = {
        "subnet_id": subnet_id,
        "network": "192.168.1.0/24"
    }
    
    response = requests.post(f"{BASE_URL}/ips/sync", json=sync_data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"同步IP地址成功: 新增{result['added']}个IP地址")
        return True
    else:
        print(f"同步IP地址失败: {response.text}")
        return False

# 分配一些IP地址
def allocate_test_ips(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取可用IP地址
    response = requests.get(f"{BASE_URL}/ips/search?status=available&limit=10", headers=headers)
    if response.status_code != 200:
        print(f"获取可用IP失败: {response.text}")
        return
    
    available_ips = response.json()
    if not available_ips:
        print("没有可用的IP地址")
        return
    
    # 分配前5个IP地址
    test_allocations = [
        {
            "preferred_ip": available_ips[0]["ip_address"],
            "subnet_id": available_ips[0]["subnet_id"],
            "hostname": "web-server-01",
            "mac_address": "00:11:22:33:44:55",
            "device_type": "server",
            "location": "机房A",
            "assigned_to": "技术部",
            "description": "Web服务器"
        },
        {
            "preferred_ip": available_ips[1]["ip_address"],
            "subnet_id": available_ips[1]["subnet_id"],
            "hostname": "db-server-01",
            "mac_address": "00:11:22:33:44:56",
            "device_type": "server",
            "location": "机房A",
            "assigned_to": "技术部",
            "description": "数据库服务器"
        },
        {
            "preferred_ip": available_ips[2]["ip_address"],
            "subnet_id": available_ips[2]["subnet_id"],
            "hostname": "workstation-01",
            "mac_address": "00:11:22:33:44:57",
            "device_type": "workstation",
            "location": "办公区B",
            "assigned_to": "产品部",
            "description": "产品经理工作站"
        }
    ]
    
    for allocation in test_allocations:
        response = requests.post(f"{BASE_URL}/ips/allocate", json=allocation, headers=headers)
        if response.status_code == 200:
            result = response.json()
            print(f"分配IP成功: {result['ip_address']} -> {result['hostname']}")
        else:
            print(f"分配IP失败: {response.text}")

def main():
    print("开始生成测试数据...")
    
    # 登录
    token = login()
    if not token:
        return
    
    print("登录成功")
    
    # 创建网段
    subnet_id = create_subnet(token)
    if not subnet_id:
        return
    
    # 同步IP地址
    if not sync_subnet_ips(token, subnet_id):
        return
    
    # 分配测试IP
    allocate_test_ips(token)
    
    print("测试数据生成完成!")

if __name__ == "__main__":
    main()