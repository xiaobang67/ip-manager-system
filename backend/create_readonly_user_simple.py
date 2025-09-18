#!/usr/bin/env python3
"""
创建只读用户的简化脚本
"""
import os
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_password_hash(password: str) -> str:
    """简单的密码哈希函数"""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    except ImportError:
        # 如果没有bcrypt，使用简单的哈希（仅用于测试）
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def create_readonly_user(username: str = "readonly", password: str = "readonly123", email: str = "readonly@example.com"):
    """创建只读用户"""
    try:
        # 从环境变量或默认值构建数据库URL
        mysql_user = os.getenv('MYSQL_USER', 'ipam_user')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'ipam_pass123')
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = os.getenv('MYSQL_PORT', '3306')
        mysql_database = os.getenv('MYSQL_DATABASE', 'ipam')
        
        database_url = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}"
        logger.info(f"连接数据库: {mysql_host}:{mysql_port}/{mysql_database}")
        
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # 检查用户是否已存在
            result = db.execute(text("SELECT COUNT(*) as count FROM users WHERE username = :username"), {"username": username})
            user_count = result.fetchone().count
            
            if user_count > 0:
                logger.info(f"用户 {username} 已存在，跳过创建")
                return
            
            # 创建只读用户
            hashed_password = get_password_hash(password)
            
            insert_sql = text("""
                INSERT INTO users (username, password_hash, email, role, is_active, created_at, updated_at)
                VALUES (:username, :password_hash, :email, 'readonly', 1, NOW(), NOW())
            """)
            
            db.execute(insert_sql, {
                "username": username,
                "password_hash": hashed_password,
                "email": email
            })
            
            db.commit()
            
            logger.info(f"只读用户创建成功:")
            logger.info(f"  用户名: {username}")
            logger.info(f"  密码: {password}")
            logger.info(f"  邮箱: {email}")
            logger.info(f"  角色: readonly")
            
        except Exception as e:
            db.rollback()
            logger.error(f"创建只读用户失败: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"创建只读用户脚本执行失败: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='创建只读用户')
    parser.add_argument('--username', default='readonly', help='用户名 (默认: readonly)')
    parser.add_argument('--password', default='readonly123', help='密码 (默认: readonly123)')
    parser.add_argument('--email', default='readonly@example.com', help='邮箱 (默认: readonly@example.com)')
    
    args = parser.parse_args()
    
    create_readonly_user(args.username, args.password, args.email)