#!/usr/bin/env python3
"""
修复密码哈希格式问题
将数据库中的旧格式密码哈希转换为bcrypt格式
"""

import pymysql
import os
import hashlib
import logging
from passlib.context import CryptContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    """获取数据库连接"""
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '3306')),
        'user': os.getenv('DB_USER', 'ipam_user'),
        'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
        'database': os.getenv('DB_NAME', 'ipam'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }
    return pymysql.connect(**db_config)

def check_password_format():
    """检查数据库中的密码格式"""
    logger.info("检查数据库中的密码格式...")
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()
            
            for user in users:
                hash_value = user['password_hash']
                logger.info(f"用户 {user['username']}:")
                logger.info(f"  哈希: {hash_value}")
                logger.info(f"  长度: {len(hash_value)}")
                
                if hash_value.startswith('$2b$'):
                    logger.info("  格式: bcrypt ✅")
                elif len(hash_value) == 64 and all(c in '0123456789abcdef' for c in hash_value):
                    logger.info("  格式: SHA-256 (需要转换)")
                elif len(hash_value) == 32 and all(c in '0123456789abcdef' for c in hash_value):
                    logger.info("  格式: MD5 (需要转换)")
                else:
                    logger.info("  格式: 未知")
                logger.info("")
    finally:
        connection.close()

def verify_old_password(password, hash_value):
    """验证旧格式的密码"""
    # 尝试SHA-256
    sha256_hash = hashlib.sha256(password.encode()).hexdigest()
    if sha256_hash == hash_value:
        return True
    
    # 尝试MD5
    md5_hash = hashlib.md5(password.encode()).hexdigest()
    if md5_hash == hash_value:
        return True
    
    return False

def convert_password_to_bcrypt():
    """将密码转换为bcrypt格式"""
    logger.info("开始转换密码格式...")
    
    # 已知的用户密码映射
    known_passwords = {
        'admin': 'admin123',
        'xiaobang': 'xiaobang123',  # 假设的密码
        'testuser': 'testuser123'   # 假设的密码
    }
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, password_hash FROM users")
            users = cursor.fetchall()
            
            for user in users:
                username = user['username']
                current_hash = user['password_hash']
                
                # 检查是否已经是bcrypt格式
                if current_hash.startswith('$2b$'):
                    logger.info(f"用户 {username} 已经是bcrypt格式，跳过")
                    continue
                
                # 获取已知密码
                if username in known_passwords:
                    plain_password = known_passwords[username]
                    
                    # 验证旧密码
                    if verify_old_password(plain_password, current_hash):
                        logger.info(f"✅ 用户 {username} 旧密码验证成功")
                        
                        # 生成新的bcrypt哈希
                        new_hash = pwd_context.hash(plain_password)
                        
                        # 更新数据库
                        cursor.execute(
                            "UPDATE users SET password_hash = %s WHERE id = %s",
                            (new_hash, user['id'])
                        )
                        
                        logger.info(f"✅ 用户 {username} 密码已转换为bcrypt格式")
                    else:
                        logger.error(f"❌ 用户 {username} 旧密码验证失败")
                else:
                    logger.warning(f"⚠️  用户 {username} 没有已知密码，跳过转换")
            
            connection.commit()
            logger.info("密码格式转换完成")
            
    except Exception as e:
        logger.error(f"转换过程中发生错误: {e}")
        connection.rollback()
    finally:
        connection.close()

def test_converted_passwords():
    """测试转换后的密码"""
    logger.info("测试转换后的密码...")
    
    test_passwords = {
        'admin': 'admin123',
        'xiaobang': 'xiaobang123',
        'testuser': 'testuser123'
    }
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for username, password in test_passwords.items():
                cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                result = cursor.fetchone()
                
                if result:
                    hash_value = result['password_hash']
                    if pwd_context.verify(password, hash_value):
                        logger.info(f"✅ 用户 {username} 密码验证成功")
                    else:
                        logger.error(f"❌ 用户 {username} 密码验证失败")
                else:
                    logger.warning(f"⚠️  用户 {username} 不存在")
    finally:
        connection.close()

def main():
    """主函数"""
    logger.info("=== 修复密码哈希格式 ===")
    
    print("选择操作：")
    print("1. 检查当前密码格式")
    print("2. 转换密码为bcrypt格式")
    print("3. 测试转换后的密码")
    print("4. 完整修复流程")
    
    choice = input("请输入选择 (1/2/3/4): ").strip()
    
    if choice == "1":
        check_password_format()
    elif choice == "2":
        convert_password_to_bcrypt()
    elif choice == "3":
        test_converted_passwords()
    elif choice == "4":
        check_password_format()
        convert_password_to_bcrypt()
        test_converted_passwords()
    else:
        print("无效选择")

if __name__ == "__main__":
    main()