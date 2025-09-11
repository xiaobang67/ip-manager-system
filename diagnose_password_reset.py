#!/usr/bin/env python3
"""
诊断密码重置问题
分析为什么密码重置API返回成功但实际没有生效
"""

import pymysql
import os
import requests
import json
import logging
from passlib.context import CryptContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API基础URL
BASE_URL = "http://localhost:8000/api"

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

def get_user_password_hash(username):
    """获取用户的密码哈希"""
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
            result = cursor.fetchone()
            if result:
                hash_value = result['password_hash']
                logger.info(f"用户 {username} 的密码哈希: {hash_value}")
                logger.info(f"哈希长度: {len(hash_value)}")
                logger.info(f"哈希前缀: {hash_value[:10]}")
                return hash_value
            return None
    finally:
        connection.close()

def verify_password_direct(password, hash_value):
    """直接验证密码"""
    try:
        return pwd_context.verify(password, hash_value)
    except Exception as e:
        logger.error(f"密码验证失败: {e}")
        return False

def login_and_get_token():
    """登录并获取token"""
    login_data = {"username": "admin", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            logger.error(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"登录请求失败: {e}")
        return None

def diagnose_password_reset():
    """诊断密码重置问题"""
    logger.info("开始诊断密码重置问题...")
    
    # 1. 获取初始状态
    logger.info("1. 检查初始状态...")
    initial_hash = get_user_password_hash("admin")
    logger.info(f"初始密码哈希: {initial_hash[:50]}...")
    
    # 验证初始密码
    if verify_password_direct("admin123", initial_hash):
        logger.info("✅ 初始密码验证成功")
    else:
        logger.error("❌ 初始密码验证失败")
        return
    
    # 2. 获取token
    logger.info("2. 获取认证token...")
    token = login_and_get_token()
    if not token:
        logger.error("无法获取token，停止诊断")
        return
    
    logger.info("✅ token获取成功")
    
    # 3. 调用密码重置API
    logger.info("3. 调用密码重置API...")
    headers = {"Authorization": f"Bearer {token}"}
    reset_data = {"new_password": "DiagnoseTest123!"}
    
    try:
        response = requests.put(f"{BASE_URL}/users/1/password", 
                              json=reset_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ 密码重置API调用成功")
        else:
            logger.error(f"❌ 密码重置API调用失败: {response.status_code} - {response.text}")
            return
    except Exception as e:
        logger.error(f"密码重置API请求失败: {e}")
        return
    
    # 4. 检查数据库中的密码哈希是否改变
    logger.info("4. 检查数据库中的密码哈希...")
    new_hash = get_user_password_hash("admin")
    logger.info(f"新密码哈希: {new_hash[:50]}...")
    
    if initial_hash == new_hash:
        logger.error("❌ 密码哈希未改变 - 这就是问题所在！")
        logger.error("密码重置API返回成功，但数据库中的密码哈希没有更新")
    else:
        logger.info("✅ 密码哈希已改变")
        
        # 验证新密码
        if verify_password_direct("DiagnoseTest123!", new_hash):
            logger.info("✅ 新密码验证成功")
        else:
            logger.error("❌ 新密码验证失败")
    
    # 5. 尝试用新密码登录
    logger.info("5. 尝试用新密码登录...")
    new_login_data = {"username": "admin", "password": "DiagnoseTest123!"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data, timeout=10)
        if response.status_code == 200:
            logger.info("✅ 新密码登录成功")
            
            # 恢复原密码
            new_token = response.json().get("access_token")
            if new_token:
                restore_headers = {"Authorization": f"Bearer {new_token}"}
                restore_data = {"new_password": "admin123"}
                
                requests.put(f"{BASE_URL}/users/1/password", 
                           json=restore_data, headers=restore_headers, timeout=10)
                logger.info("✅ 原密码已恢复")
        else:
            logger.error("❌ 新密码登录失败")
            logger.error(f"响应: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"新密码登录请求失败: {e}")

def analyze_auth_services():
    """分析认证服务的差异"""
    logger.info("分析认证服务差异...")
    
    # 检查两个认证服务文件
    auth_files = [
        "backend/auth_service.py",
        "backend/app/services/auth_service.py",
        "backend/app/services/user_service.py",
        "backend/app/repositories/user_repository.py"
    ]
    
    for file_path in auth_files:
        if os.path.exists(file_path):
            logger.info(f"✅ 找到文件: {file_path}")
        else:
            logger.warning(f"❌ 文件不存在: {file_path}")

def main():
    """主函数"""
    logger.info("=== 密码重置问题诊断 ===")
    
    # 1. 分析认证服务
    analyze_auth_services()
    
    # 2. 诊断密码重置
    diagnose_password_reset()
    
    logger.info("=== 诊断完成 ===")

if __name__ == "__main__":
    main()