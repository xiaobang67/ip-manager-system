#!/usr/bin/env python3
"""
统一认证系统测试脚本
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

async def test_unified_auth():
    """测试统一认证系统"""
    logger.info("开始测试统一认证系统...")
    
    try:
        # 导入必要的模块
        from app.database import get_db
        from app.services.auth_service import AuthService
        from app.services.user_service import UserService
        from app.core.unified_deps import ensure_auth_consistency
        
        # 确保认证一致性
        ensure_auth_consistency()
        
        # 获取数据库会话
        db = next(get_db())
        
        # 创建服务实例
        auth_service = AuthService(db)
        user_service = UserService(db)
        
        # 测试用户认证
        logger.info("测试用户认证...")
        user = auth_service.authenticate_user("admin", "admin")
        if user:
            logger.info(f"✅ 用户认证成功: {user.username}")
        else:
            logger.warning("❌ 用户认证失败")
        
        # 测试密码重置
        if user:
            logger.info("测试密码重置...")
            try:
                success = user_service.reset_user_password(user.id, "newpassword123")
                if success:
                    logger.info("✅ 密码重置成功")
                    
                    # 验证新密码
                    new_user = auth_service.authenticate_user("admin", "newpassword123")
                    if new_user:
                        logger.info("✅ 新密码验证成功")
                        
                        # 恢复原密码
                        user_service.reset_user_password(user.id, "admin")
                        logger.info("✅ 密码已恢复")
                    else:
                        logger.error("❌ 新密码验证失败")
                else:
                    logger.error("❌ 密码重置失败")
            except Exception as e:
                logger.error(f"密码重置测试失败: {e}")
        
        logger.info("统一认证系统测试完成")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_unified_auth())
