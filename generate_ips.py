#!/usr/bin/env python3
"""
为现有网段生成IP地址的脚本
"""
import pymysql
import ipaddress
import os
from datetime import datetime

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'ipam_user',
    'password': 'ipam_pass123',
    'database': 'ipam',
    'port': 3306,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def generate_ips_for_subnet(subnet_id, network, netmask):
    """为网段生成IP地址"""
    try:
        # 创建网络对象
        net = ipaddress.IPv4Network(f"{network}/{netmask}", strict=False)
        
        print(f"为网段 {network}/{netmask} 生成IP地址...")
        print(f"网段包含 {net.num_addresses} 个地址")
        
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        
        try:
            with connection.cursor() as cursor:
                # 批量插入IP地址
                ip_data = []
                for ip in net.hosts():  # 排除网络地址和广播地址
                    ip_data.append((
                        str(ip),
                        subnet_id,
                        'available',  # 默认状态为可用
                        datetime.now(),
                        datetime.now()
                    ))
                
                # 分批插入，避免一次插入过多数据
                batch_size = 1000
                total_inserted = 0
                
                for i in range(0, len(ip_data), batch_size):
                    batch = ip_data[i:i + batch_size]
                    
                    cursor.executemany("""
                        INSERT INTO ip_addresses (ip_address, subnet_id, status, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, batch)
                    
                    total_inserted += len(batch)
                    print(f"已插入 {total_inserted}/{len(ip_data)} 个IP地址")
                
                connection.commit()
                print(f"成功为网段 {network}/{netmask} 生成了 {total_inserted} 个IP地址")
                
        finally:
            connection.close()
            
    except Exception as e:
        print(f"生成IP地址失败: {e}")

def main():
    """主函数"""
    try:
        # 连接数据库获取网段信息
        connection = pymysql.connect(**DB_CONFIG)
        
        try:
            with connection.cursor() as cursor:
                # 获取所有网段
                cursor.execute("SELECT id, network, netmask FROM subnets")
                subnets = cursor.fetchall()
                
                print(f"找到 {len(subnets)} 个网段")
                
                for subnet in subnets:
                    subnet_id = subnet['id']
                    network = subnet['network']
                    netmask = subnet['netmask']
                    
                    # 检查是否已经有IP地址
                    cursor.execute("SELECT COUNT(*) as count FROM ip_addresses WHERE subnet_id = %s", (subnet_id,))
                    ip_count = cursor.fetchone()['count']
                    
                    if ip_count > 0:
                        print(f"网段 {network}/{netmask} 已有 {ip_count} 个IP地址，跳过")
                        continue
                    
                    # 生成IP地址
                    generate_ips_for_subnet(subnet_id, network, netmask)
                    
        finally:
            connection.close()
            
    except Exception as e:
        print(f"脚本执行失败: {e}")

if __name__ == "__main__":
    main()