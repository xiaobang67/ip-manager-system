#!/usr/bin/env python3
"""
添加只读角色的数据库迁移脚本
"""
import sys
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """运行迁移脚本"""
    try:
        # 直接使用数据库连接字符串，避免配置文件问题
        from sqlalchemy import create_engine, text
        
        # 从环境变量或默认值构建数据库URL
        mysql_user = os.getenv('MYSQL_USER', 'ipam_user')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'ipam_pass123')
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = os.getenv('MYSQL_PORT', '3306')
        mysql_database = os.getenv('MYSQL_DATABASE', 'ipam')
        
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        logger.info(f"连接数据库: {mysql_host}:{mysql_port}/{mysql_database}")
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 检查是否已经有readonly角色的用户
                result = conn.execute(text("SELECT COUNT(*) as count FROM users WHERE role = 'readonly'"))
                readonly_count = result.fetchone().count
                
                if readonly_count > 0:
                    logger.info(f"数据库中已存在 {readonly_count} 个只读用户，跳过迁移")
                    trans.rollback()
                    return
                
                # 更新用户表的role枚举类型（MySQL）
                logger.info("更新用户表的角色枚举类型...")
                
                # 对于MySQL，需要修改枚举类型
                conn.execute(text("""
                    ALTER TABLE users 
                    MODIFY COLUMN role ENUM('admin', 'manager', 'user', 'readonly') 
                    DEFAULT 'user'
                """))
                
                logger.info("角色枚举类型更新成功")
                
                # 提交事务
                trans.commit()
                logger.info("只读角色迁移完成")
                
            except Exception as e:
                trans.rollback()
                logger.error(f"迁移失败，已回滚: {e}")
                raise
                
    except Exception as e:
        logger.error(f"迁移脚本执行失败: {e}")
        raise

if __name__ == "__main__":
    run_migration()