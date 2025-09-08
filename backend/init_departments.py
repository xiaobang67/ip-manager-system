#!/usr/bin/env python3
"""
部门表初始化脚本
确保部门表存在并包含基础数据
"""
import pymysql
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'ipam_user'),
    'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
    'database': os.getenv('DB_NAME', 'ipam'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'use_unicode': True
}

def create_departments_table():
    """创建部门表"""
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # 检查表是否存在
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_name = 'departments'
            """, (DB_CONFIG['database'],))
            
            table_exists = cursor.fetchone()['count'] > 0
            
            if not table_exists:
                logger.info("创建部门表...")
                
                # 创建部门表（简化版）
                cursor.execute("""
                    CREATE TABLE departments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        code VARCHAR(50) UNIQUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_name (name),
                        INDEX idx_code (code)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                logger.info("部门表创建成功")
            else:
                logger.info("部门表已存在")
            
            # 检查是否有数据
            cursor.execute("SELECT COUNT(*) as count FROM departments")
            data_count = cursor.fetchone()['count']
            
            if data_count == 0:
                logger.info("插入初始部门数据...")
                
                # 插入初始数据（简化版）
                departments_data = [
                    ('技术部', 'TECH'),
                    ('运维部', 'OPS'),
                    ('产品部', 'PRODUCT'),
                    ('市场部', 'MARKETING'),
                    ('人事部', 'HR'),
                    ('财务部', 'FINANCE'),
                    ('客服部', 'SERVICE')
                ]
                
                cursor.executemany("""
                    INSERT INTO departments (name, code)
                    VALUES (%s, %s)
                """, departments_data)
                
                connection.commit()
                logger.info(f"成功插入 {len(departments_data)} 个部门")
            else:
                logger.info(f"部门表已有 {data_count} 条数据")
            
            # 显示当前部门列表
            cursor.execute("SELECT id, name, code, created_at FROM departments ORDER BY name")
            departments = cursor.fetchall()
            
            logger.info("当前部门列表:")
            for dept in departments:
                logger.info(f"  ID: {dept['id']}, 名称: {dept['name']}, 编码: {dept['code']}, 创建时间: {dept['created_at']}")
                
    except Exception as e:
        logger.error(f"初始化部门表失败: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

def test_departments_api():
    """测试部门API"""
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        
        with connection.cursor() as cursor:
            # 测试查询
            cursor.execute("SELECT COUNT(*) as total FROM departments")
            total = cursor.fetchone()['total']
            
            logger.info(f"API测试结果: 总部门数={total}")
            
            # 测试搜索
            cursor.execute("SELECT * FROM departments WHERE name LIKE %s", ('%技术%',))
            search_results = cursor.fetchall()
            logger.info(f"搜索'技术'结果: {len(search_results)} 个部门")
            
    except Exception as e:
        logger.error(f"测试部门API失败: {e}")
        raise
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    logger.info("开始初始化部门表...")
    
    try:
        create_departments_table()
        test_departments_api()
        logger.info("部门表初始化完成!")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        exit(1)