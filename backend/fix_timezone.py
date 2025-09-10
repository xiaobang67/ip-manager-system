#!/usr/bin/env python3
"""
时区修复脚本 - 将数据库中的时间字段从UTC调整为北京时间(UTC+8)
"""

import os
import sys
import pymysql
from datetime import datetime, timedelta
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('timezone_fix.log'),
        logging.StreamHandler()
    ]
)
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

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        logger.info("数据库连接成功")
        return connection
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def backup_tables(connection):
    """备份相关表的数据"""
    logger.info("开始备份数据...")
    
    backup_queries = [
        "CREATE TABLE IF NOT EXISTS users_backup AS SELECT * FROM users;",
        "CREATE TABLE IF NOT EXISTS subnets_backup AS SELECT * FROM subnets;", 
        "CREATE TABLE IF NOT EXISTS ip_addresses_backup AS SELECT * FROM ip_addresses;",
        "CREATE TABLE IF NOT EXISTS audit_logs_backup AS SELECT * FROM audit_logs;",
        "CREATE TABLE IF NOT EXISTS alert_history_backup AS SELECT * FROM alert_history;"
    ]
    
    try:
        with connection.cursor() as cursor:
            for query in backup_queries:
                cursor.execute(query)
            connection.commit()
        logger.info("数据备份完成")
        return True
    except Exception as e:
        logger.error(f"数据备份失败: {e}")
        return False

def fix_timezone_for_table(connection, table_name, time_columns):
    """修复指定表的时区问题"""
    logger.info(f"开始修复表 {table_name} 的时区...")
    
    try:
        with connection.cursor() as cursor:
            # 获取需要更新的记录数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_records = cursor.fetchone()[0]
            logger.info(f"表 {table_name} 共有 {total_records} 条记录需要处理")
            
            if total_records == 0:
                logger.info(f"表 {table_name} 没有数据，跳过")
                return True
            
            # 构建更新SQL
            set_clauses = []
            for col in time_columns:
                set_clauses.append(f"{col} = DATE_ADD({col}, INTERVAL 8 HOUR)")
            
            update_sql = f"""
                UPDATE {table_name} 
                SET {', '.join(set_clauses)}
                WHERE {time_columns[0]} IS NOT NULL
            """
            
            logger.info(f"执行SQL: {update_sql}")
            cursor.execute(update_sql)
            
            affected_rows = cursor.rowcount
            connection.commit()
            
            logger.info(f"表 {table_name} 时区修复完成，影响 {affected_rows} 条记录")
            return True
            
    except Exception as e:
        logger.error(f"修复表 {table_name} 时区失败: {e}")
        connection.rollback()
        return False

def set_mysql_timezone(connection):
    """设置MySQL时区为北京时间"""
    logger.info("设置MySQL时区为北京时间...")
    
    try:
        with connection.cursor() as cursor:
            # 设置会话时区
            cursor.execute("SET time_zone = '+08:00'")
            
            # 验证时区设置
            cursor.execute("SELECT @@session.time_zone, NOW()")
            result = cursor.fetchone()
            logger.info(f"当前时区: {result[0]}, 当前时间: {result[1]}")
            
        connection.commit()
        logger.info("MySQL时区设置完成")
        return True
        
    except Exception as e:
        logger.error(f"设置MySQL时区失败: {e}")
        return False

def verify_fix(connection):
    """验证修复结果"""
    logger.info("验证时区修复结果...")
    
    verification_queries = [
        ("用户表最新记录", "SELECT username, created_at, updated_at FROM users ORDER BY created_at DESC LIMIT 3"),
        ("IP地址表最新记录", "SELECT ip_address, allocated_at, created_at FROM ip_addresses WHERE allocated_at IS NOT NULL ORDER BY created_at DESC LIMIT 3"),
        ("子网表最新记录", "SELECT network, created_at, updated_at FROM subnets ORDER BY created_at DESC LIMIT 3")
    ]
    
    try:
        with connection.cursor() as cursor:
            for desc, query in verification_queries:
                logger.info(f"\n{desc}:")
                cursor.execute(query)
                results = cursor.fetchall()
                for row in results:
                    logger.info(f"  {row}")
        
        return True
        
    except Exception as e:
        logger.error(f"验证失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("开始执行时区修复脚本")
    logger.info("=" * 50)
    
    # 获取数据库连接
    connection = get_db_connection()
    if not connection:
        logger.error("无法连接数据库，退出")
        sys.exit(1)
    
    try:
        # 1. 设置MySQL时区
        if not set_mysql_timezone(connection):
            logger.error("设置MySQL时区失败，退出")
            sys.exit(1)
        
        # 2. 备份数据
        if not backup_tables(connection):
            logger.error("数据备份失败，退出")
            sys.exit(1)
        
        # 3. 修复各表的时区
        tables_to_fix = [
            ('users', ['created_at', 'updated_at']),
            ('subnets', ['created_at', 'updated_at']),
            ('ip_addresses', ['allocated_at', 'created_at', 'updated_at']),
            ('audit_logs', ['created_at']),
            ('alert_history', ['created_at', 'resolved_at']),
            ('alert_rules', ['created_at']),
            ('tags', ['created_at']),
            ('custom_fields', ['created_at']),
            ('system_configs', ['updated_at'])
        ]
        
        success_count = 0
        for table_name, time_columns in tables_to_fix:
            if fix_timezone_for_table(connection, table_name, time_columns):
                success_count += 1
            else:
                logger.error(f"修复表 {table_name} 失败")
        
        logger.info(f"成功修复 {success_count}/{len(tables_to_fix)} 个表")
        
        # 4. 验证修复结果
        verify_fix(connection)
        
        logger.info("=" * 50)
        logger.info("时区修复脚本执行完成")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"脚本执行过程中发生错误: {e}")
        sys.exit(1)
    
    finally:
        if connection:
            connection.close()
            logger.info("数据库连接已关闭")

if __name__ == "__main__":
    main()