#!/usr/bin/env python3
"""
时区验证脚本 - 检查数据库时区设置和时间数据
"""

import pymysql
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'ipam_user',
    'password': 'ipam_pass123',
    'database': 'ipam',
    'charset': 'utf8mb4'
}

def verify_timezone():
    """验证时区设置和数据"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        logger.info("数据库连接成功")
        
        with connection.cursor() as cursor:
            # 检查MySQL时区设置
            logger.info("\n=== MySQL时区设置 ===")
            cursor.execute("SELECT @@global.time_zone, @@session.time_zone, NOW()")
            result = cursor.fetchone()
            logger.info(f"全局时区: {result[0]}")
            logger.info(f"会话时区: {result[1]}")
            logger.info(f"当前数据库时间: {result[2]}")
            
            # 检查系统时间
            logger.info(f"系统当前时间: {datetime.now()}")
            
            # 检查各表的时间数据样本
            logger.info("\n=== 数据库时间数据样本 ===")
            
            # 用户表
            cursor.execute("SELECT username, created_at, updated_at FROM users ORDER BY created_at DESC LIMIT 3")
            users = cursor.fetchall()
            logger.info("\n用户表最新记录:")
            for user in users:
                logger.info(f"  用户: {user[0]}, 创建时间: {user[1]}, 更新时间: {user[2]}")
            
            # IP地址表
            cursor.execute("SELECT ip_address, allocated_at, created_at FROM ip_addresses WHERE allocated_at IS NOT NULL ORDER BY created_at DESC LIMIT 3")
            ips = cursor.fetchall()
            logger.info("\n已分配IP地址记录:")
            for ip in ips:
                logger.info(f"  IP: {ip[0]}, 分配时间: {ip[1]}, 创建时间: {ip[2]}")
            
            # 子网表
            cursor.execute("SELECT network, created_at, updated_at FROM subnets ORDER BY created_at DESC LIMIT 3")
            subnets = cursor.fetchall()
            logger.info("\n子网表最新记录:")
            for subnet in subnets:
                logger.info(f"  网段: {subnet[0]}, 创建时间: {subnet[1]}, 更新时间: {subnet[2]}")
            
            # 统计各表记录数
            logger.info("\n=== 数据统计 ===")
            tables = ['users', 'subnets', 'ip_addresses', 'audit_logs', 'alert_history']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"{table} 表记录数: {count}")
        
        connection.close()
        logger.info("\n验证完成！")
        
    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")

if __name__ == "__main__":
    verify_timezone()