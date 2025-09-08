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
                
                # 创建部门表
                cursor.execute("""
                    CREATE TABLE departments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL UNIQUE,
                        code VARCHAR(50) UNIQUE,
                        description TEXT,
                        manager VARCHAR(100),
                        contact_email VARCHAR(100),
                        contact_phone VARCHAR(50),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_name (name),
                        INDEX idx_code (code),
                        INDEX idx_is_active (is_active)
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
                
                # 插入初始数据
                departments_data = [
                    ('技术部', 'TECH', '负责系统开发和技术支持', '技术总监', 'tech@company.com', '010-12345678'),
                    ('运维部', 'OPS', '负责系统运维和基础设施管理', '运维经理', 'ops@company.com', '010-12345679'),
                    ('产品部', 'PRODUCT', '负责产品规划和设计', '产品经理', 'product@company.com', '010-12345680'),
                    ('市场部', 'MARKETING', '负责市场推广和品牌建设', '市场总监', 'marketing@company.com', '010-12345681'),
                    ('人事部', 'HR', '负责人力资源管理', '人事经理', 'hr@company.com', '010-12345682'),
                    ('财务部', 'FINANCE', '负责财务管理和会计核算', '财务经理', 'finance@company.com', '010-12345683'),
                    ('客服部', 'SERVICE', '负责客户服务和支持', '客服经理', 'service@company.com', '010-12345684')
                ]
                
                cursor.executemany("""
                    INSERT INTO departments (name, code, description, manager, contact_email, contact_phone, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, TRUE)
                """, departments_data)
                
                connection.commit()
                logger.info(f"成功插入 {len(departments_data)} 个部门")
            else:
                logger.info(f"部门表已有 {data_count} 条数据")
            
            # 显示当前部门列表
            cursor.execute("SELECT id, name, code, manager, is_active FROM departments ORDER BY name")
            departments = cursor.fetchall()
            
            logger.info("当前部门列表:")
            for dept in departments:
                status = "活跃" if dept['is_active'] else "停用"
                logger.info(f"  ID: {dept['id']}, 名称: {dept['name']}, 编码: {dept['code']}, 负责人: {dept['manager']}, 状态: {status}")
                
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
            
            cursor.execute("SELECT COUNT(*) as active FROM departments WHERE is_active = TRUE")
            active = cursor.fetchone()['active']
            
            logger.info(f"API测试结果: 总部门数={total}, 活跃部门数={active}")
            
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