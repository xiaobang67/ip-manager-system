#!/usr/bin/env python3
"""
测试VLAN API和认证系统
使用HTTP请求直接测试API端点
"""

import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API基础URL
BASE_URL = "http://localhost:8000/api"

def test_login():
    """测试登录功能"""
    logger.info("测试登录功能...")
    
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info("✅ 登录成功")
            return data.get("access_token")
        else:
            logger.error(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        logger.error("❌ 无法连接到API服务器，请确保服务正在运行")
        return None
    except Exception as e:
        logger.error(f"登录测试失败: {e}")
        return None

def test_password_reset(token):
    """测试密码重置功能"""
    logger.info("测试密码重置功能...")
    
    if not token:
        logger.error("没有有效的token，跳过密码重置测试")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试重置用户ID为1的密码
    reset_data = {"new_password": "TestPassword123!"}
    
    try:
        response = requests.put(f"{BASE_URL}/users/1/password", 
                              json=reset_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ 密码重置API调用成功")
            
            # 等待一下确保密码更新生效
            time.sleep(1)
            
            # 测试新密码登录
            new_login_data = {
                "username": "admin",
                "password": "TestPassword123!"
            }
            
            response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ 新密码登录成功 - 密码重置功能正常！")
                
                # 获取新token并恢复原密码
                new_token = response.json().get("access_token")
                if new_token:
                    restore_headers = {"Authorization": f"Bearer {new_token}"}
                    restore_data = {"new_password": "admin"}
                    
                    response = requests.put(f"{BASE_URL}/users/1/password", 
                                          json=restore_data, headers=restore_headers, timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ 原密码已恢复")
                        return True
                    else:
                        logger.warning("⚠️  原密码恢复失败")
                        return True  # 重置功能本身是正常的
                else:
                    logger.warning("⚠️  无法获取新token恢复密码")
                    return True
            else:
                logger.error("❌ 新密码登录失败 - 密码重置功能异常！")
                logger.error(f"响应: {response.status_code} - {response.text}")
                return False
        else:
            logger.error(f"❌ 密码重置API调用失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"密码重置测试失败: {e}")
        return False

def test_user_management(token):
    """测试用户管理功能"""
    logger.info("测试用户管理功能...")
    
    if not token:
        logger.error("没有有效的token，跳过用户管理测试")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # 获取用户列表
        response = requests.get(f"{BASE_URL}/users", headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            logger.info(f"✅ 获取用户列表成功，共 {len(users.get('users', []))} 个用户")
            return True
        else:
            logger.error(f"❌ 获取用户列表失败: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"用户管理测试失败: {e}")
        return False

def test_change_password(token):
    """测试修改密码功能"""
    logger.info("测试修改密码功能...")
    
    if not token:
        logger.error("没有有效的token，跳过修改密码测试")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 测试修改密码
    change_data = {
        "old_password": "admin123",
        "new_password": "ChangeTest123!"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/auth/password", 
                              json=change_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ 修改密码API调用成功")
            
            # 测试新密码登录
            new_login_data = {
                "username": "admin",
                "password": "ChangeTest123!"
            }
            
            response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ 新密码登录成功 - 修改密码功能正常！")
                
                # 恢复原密码
                new_token = response.json().get("access_token")
                if new_token:
                    restore_headers = {"Authorization": f"Bearer {new_token}"}
                    restore_data = {
                        "old_password": "ChangeTest123!",
                        "new_password": "admin"
                    }
                    
                    response = requests.put(f"{BASE_URL}/auth/password", 
                                          json=restore_data, headers=restore_headers, timeout=10)
                    if response.status_code == 200:
                        logger.info("✅ 原密码已恢复")
                        return True
                    else:
                        logger.warning("⚠️  原密码恢复失败")
                        return True
                else:
                    logger.warning("⚠️  无法获取新token恢复密码")
                    return True
            else:
                logger.error("❌ 新密码登录失败 - 修改密码功能异常！")
                return False
        else:
            logger.error(f"❌ 修改密码API调用失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"修改密码测试失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始API认证系统测试...")
    
    # 1. 测试登录
    token = test_login()
    if not token:
        logger.error("登录失败，无法继续测试")
        return
    
    # 2. 测试用户管理
    test_user_management(token)
    
    # 3. 测试修改密码
    test_change_password(token)
    
    # 4. 测试密码重置（管理员功能）
    test_password_reset(token)
    
    logger.info("=== API认证系统测试完成 ===")

if __name__ == "__main__":
    main()