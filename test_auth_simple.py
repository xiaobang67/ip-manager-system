#!/usr/bin/env python3
"""
简单的认证系统测试脚本
直接使用独立的认证服务进行测试
"""

import sys
import os
import logging
from pathlib import Path

# 添加backend路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_standalone_auth():
    """测试独立认证服务"""
    logger.info("测试独立认证服务...")
    
    try:
        # 导入独立认证服务
        from auth_service import auth_service
        
        # 1. 测试用户认证
        logger.info("1. 测试用户认证...")
        user = auth_service.authenticate_user("admin", "admin")
        if user:
            logger.info(f"✅ 用户认证成功: {user['username']}")
            user_id = user['id']
        else:
            logger.error("❌ 用户认证失败")
            return
        
        # 2. 测试密码重置
        logger.info("2. 测试密码重置...")
        test_password = "TestPassword123!"
        
        try:
            success = auth_service.reset_password("admin", test_password)
            if success:
                logger.info("✅ 密码重置成功")
                
                # 验证新密码
                new_user = auth_service.authenticate_user("admin", test_password)
                if new_user:
                    logger.info("✅ 新密码验证成功 - 密码重置功能正常！")
                    
                    # 恢复原密码
                    auth_service.reset_password("admin", "admin")
                    logger.info("✅ 原密码已恢复")
                else:
                    logger.error("❌ 新密码验证失败")
            else:
                logger.error("❌ 密码重置失败")
                
        except Exception as e:
            logger.error(f"密码重置测试失败: {e}")
        
        # 3. 测试密码修改
        logger.info("3. 测试密码修改...")
        try:
            success = auth_service.change_password(user_id, "admin", "ChangeTest123!")
            if success:
                logger.info("✅ 密码修改成功")
                
                # 验证新密码
                change_user = auth_service.authenticate_user("admin", "ChangeTest123!")
                if change_user:
                    logger.info("✅ 修改后密码验证成功")
                    
                    # 恢复原密码
                    auth_service.change_password(user_id, "ChangeTest123!", "admin")
                    logger.info("✅ 原密码已恢复")
                else:
                    logger.error("❌ 修改后密码验证失败")
            else:
                logger.error("❌ 密码修改失败")
                
        except Exception as e:
            logger.error(f"密码修改测试失败: {e}")
        
        logger.info("=== 独立认证服务测试完成 ===")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def check_database_connection():
    """检查数据库连接"""
    logger.info("检查数据库连接...")
    
    try:
        from auth_service import auth_service
        
        # 尝试获取数据库连接
        connection = auth_service.get_db_connection()
        if connection:
            logger.info("✅ 数据库连接成功")
            
            # 测试查询
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as count FROM users")
                result = cursor.fetchone()
                logger.info(f"✅ 用户表查询成功，共有 {result['count']} 个用户")
            
            connection.close()
        else:
            logger.error("❌ 数据库连接失败")
            
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")

def main():
    """主函数"""
    logger.info("开始简单认证系统测试...")
    
    # 1. 检查数据库连接
    check_database_connection()
    
    # 2. 测试认证功能
    test_standalone_auth()
    
    logger.info("测试完成！")

if __name__ == "__main__":
    main()