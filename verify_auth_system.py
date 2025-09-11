#!/usr/bin/env python3
"""
认证系统验证脚本
验证密码重置功能是否正常工作
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent / "backend"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_auth_system():
    """验证认证系统"""
    logger.info("开始验证认证系统...")
    
    try:
        # 导入必要的模块
        from app.database import get_db
        from app.services.auth_service import AuthService
        from app.services.user_service import UserService
        from app.repositories.user_repository import UserRepository
        
        # 获取数据库会话
        db = next(get_db())
        
        # 创建服务实例
        auth_service = AuthService(db)
        user_service = UserService(db)
        user_repo = UserRepository(db)
        
        logger.info("=== 认证系统验证 ===")
        
        # 1. 测试用户认证
        logger.info("1. 测试用户认证...")
        user = auth_service.authenticate_user("admin", "admin")
        if user:
            logger.info(f"✅ 用户认证成功: {user.username}")
            user_id = user.id
        else:
            logger.error("❌ 用户认证失败")
            return
        
        # 2. 测试密码重置（核心功能）
        logger.info("2. 测试密码重置...")
        test_password = "TestPassword123!"
        
        try:
            # 使用用户服务重置密码
            success = user_service.reset_user_password(user_id, test_password)
            if success:
                logger.info("✅ 用户服务密码重置成功")
                
                # 验证新密码是否生效
                new_auth = auth_service.authenticate_user("admin", test_password)
                if new_auth:
                    logger.info("✅ 新密码验证成功 - 密码重置功能正常！")
                    
                    # 恢复原密码
                    user_service.reset_user_password(user_id, "admin")
                    logger.info("✅ 原密码已恢复")
                else:
                    logger.error("❌ 新密码验证失败 - 密码重置功能异常！")
            else:
                logger.error("❌ 用户服务密码重置失败")
                
        except Exception as e:
            logger.error(f"密码重置测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 3. 测试直接数据库密码更新
        logger.info("3. 测试数据库密码更新...")
        try:
            success = user_repo.update_password(user_id, "DirectTest123!")
            if success:
                logger.info("✅ 数据库密码更新成功")
                
                # 验证
                direct_auth = auth_service.authenticate_user("admin", "DirectTest123!")
                if direct_auth:
                    logger.info("✅ 直接数据库更新验证成功")
                    
                    # 恢复原密码
                    user_repo.update_password(user_id, "admin")
                    logger.info("✅ 原密码已恢复")
                else:
                    logger.error("❌ 直接数据库更新验证失败")
            else:
                logger.error("❌ 数据库密码更新失败")
                
        except Exception as e:
            logger.error(f"数据库密码更新测试失败: {e}")
        
        logger.info("=== 验证完成 ===")
        
        # 关闭数据库连接
        db.close()
        
    except Exception as e:
        logger.error(f"验证过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_password_reset_api():
    """测试密码重置API"""
    logger.info("测试密码重置API...")
    
    import requests
    import json
    
    # API基础URL
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # 1. 登录获取token
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            logger.info("✅ 登录成功，获取到token")
            
            # 2. 测试密码重置API
            headers = {"Authorization": f"Bearer {access_token}"}
            reset_data = {"new_password": "ApiTest123!"}
            
            # 假设要重置用户ID为1的密码
            response = requests.put(f"{base_url}/users/1/password", 
                                  json=reset_data, headers=headers)
            
            if response.status_code == 200:
                logger.info("✅ 密码重置API调用成功")
                
                # 3. 验证新密码
                new_login_data = {
                    "username": "admin",
                    "password": "ApiTest123!"
                }
                
                response = requests.post(f"{base_url}/auth/login", json=new_login_data)
                if response.status_code == 200:
                    logger.info("✅ 新密码登录成功 - API功能正常！")
                    
                    # 恢复原密码
                    token_data = response.json()
                    new_token = token_data["access_token"]
                    headers = {"Authorization": f"Bearer {new_token}"}
                    restore_data = {"new_password": "admin"}
                    
                    requests.put(f"{base_url}/users/1/password", 
                               json=restore_data, headers=headers)
                    logger.info("✅ 原密码已恢复")
                else:
                    logger.error("❌ 新密码登录失败 - API功能异常！")
            else:
                logger.error(f"❌ 密码重置API调用失败: {response.status_code}")
        else:
            logger.error("❌ 登录失败，无法测试API")
            
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️  无法连接到API服务器，请确保服务正在运行")
    except Exception as e:
        logger.error(f"API测试失败: {e}")

if __name__ == "__main__":
    print("选择验证方式：")
    print("1. 直接数据库验证")
    print("2. API接口验证")
    print("3. 完整验证")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    if choice == "1":
        asyncio.run(verify_auth_system())
    elif choice == "2":
        test_password_reset_api()
    elif choice == "3":
        asyncio.run(verify_auth_system())
        test_password_reset_api()
    else:
        print("无效选择")
