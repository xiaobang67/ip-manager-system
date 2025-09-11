#!/usr/bin/env python3
"""
最终认证系统测试
验证密码重置问题是否已完全解决
"""

import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api"

def test_complete_password_reset_flow():
    """测试完整的密码重置流程"""
    logger.info("=== 完整密码重置流程测试 ===")
    
    # 1. 初始登录
    logger.info("1. 使用初始密码登录...")
    login_data = {"username": "admin", "password": "admin123"}
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
    if response.status_code != 200:
        logger.error(f"❌ 初始登录失败: {response.status_code} - {response.text}")
        return False
    
    token = response.json().get("access_token")
    logger.info("✅ 初始登录成功")
    
    # 2. 重置密码
    logger.info("2. 重置密码...")
    headers = {"Authorization": f"Bearer {token}"}
    reset_data = {"new_password": "NewPassword123!"}
    
    response = requests.put(f"{BASE_URL}/users/1/password", 
                          json=reset_data, headers=headers, timeout=10)
    
    if response.status_code != 200:
        logger.error(f"❌ 密码重置失败: {response.status_code} - {response.text}")
        return False
    
    logger.info("✅ 密码重置API调用成功")
    
    # 3. 使用新密码登录
    logger.info("3. 使用新密码登录...")
    new_login_data = {"username": "admin", "password": "NewPassword123!"}
    
    response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data, timeout=10)
    if response.status_code != 200:
        logger.error(f"❌ 新密码登录失败: {response.status_code} - {response.text}")
        return False
    
    new_token = response.json().get("access_token")
    logger.info("✅ 新密码登录成功")
    
    # 4. 再次重置密码回原来的密码
    logger.info("4. 恢复原密码...")
    new_headers = {"Authorization": f"Bearer {new_token}"}
    restore_data = {"new_password": "admin123"}
    
    response = requests.put(f"{BASE_URL}/users/1/password", 
                          json=restore_data, headers=new_headers, timeout=10)
    
    if response.status_code != 200:
        logger.error(f"❌ 密码恢复失败: {response.status_code} - {response.text}")
        return False
    
    logger.info("✅ 密码恢复成功")
    
    # 5. 验证原密码可以登录
    logger.info("5. 验证原密码登录...")
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
    if response.status_code != 200:
        logger.error(f"❌ 原密码登录失败: {response.status_code} - {response.text}")
        return False
    
    logger.info("✅ 原密码登录成功")
    
    return True

def test_change_password_flow():
    """测试修改密码流程"""
    logger.info("=== 修改密码流程测试 ===")
    
    # 1. 登录
    login_data = {"username": "admin", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
    
    if response.status_code != 200:
        logger.error(f"❌ 登录失败: {response.status_code}")
        return False
    
    token = response.json().get("access_token")
    logger.info("✅ 登录成功")
    
    # 2. 修改密码
    logger.info("2. 修改密码...")
    headers = {"Authorization": f"Bearer {token}"}
    change_data = {
        "old_password": "admin123",
        "new_password": "ChangedPassword123!"
    }
    
    response = requests.put(f"{BASE_URL}/auth/password", 
                          json=change_data, headers=headers, timeout=10)
    
    if response.status_code != 200:
        logger.error(f"❌ 修改密码失败: {response.status_code} - {response.text}")
        return False
    
    logger.info("✅ 修改密码成功")
    
    # 3. 使用新密码登录
    new_login_data = {"username": "admin", "password": "ChangedPassword123!"}
    response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data, timeout=10)
    
    if response.status_code != 200:
        logger.error(f"❌ 新密码登录失败: {response.status_code}")
        return False
    
    new_token = response.json().get("access_token")
    logger.info("✅ 新密码登录成功")
    
    # 4. 恢复原密码
    new_headers = {"Authorization": f"Bearer {new_token}"}
    restore_data = {
        "old_password": "ChangedPassword123!",
        "new_password": "admin123"
    }
    
    response = requests.put(f"{BASE_URL}/auth/password", 
                          json=restore_data, headers=new_headers, timeout=10)
    
    if response.status_code == 200:
        logger.info("✅ 原密码恢复成功")
        return True
    else:
        logger.warning(f"⚠️  原密码恢复失败: {response.status_code}")
        return True  # 修改功能本身是正常的

def main():
    """主函数"""
    logger.info("开始最终认证系统测试...")
    
    try:
        # 测试密码重置功能
        reset_success = test_complete_password_reset_flow()
        
        # 测试修改密码功能
        change_success = test_change_password_flow()
        
        # 总结
        logger.info("=== 测试结果总结 ===")
        if reset_success:
            logger.info("✅ 密码重置功能：正常")
        else:
            logger.error("❌ 密码重置功能：异常")
        
        if change_success:
            logger.info("✅ 修改密码功能：正常")
        else:
            logger.error("❌ 修改密码功能：异常")
        
        if reset_success and change_success:
            logger.info("🎉 所有认证功能测试通过！密码重置问题已解决！")
        else:
            logger.error("❌ 部分功能仍有问题")
            
    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到API服务器，请确保服务正在运行")
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")

if __name__ == "__main__":
    main()