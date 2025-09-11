"""
统一认证系统依赖注入
"""
from functools import lru_cache
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from fastapi import Depends
import logging

logger = logging.getLogger(__name__)

@lru_cache()
def get_unified_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """获取统一认证服务实例"""
    logger.debug("创建统一认证服务实例")
    return AuthService(db)

@lru_cache()
def get_unified_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取统一用户服务实例"""
    logger.debug("创建统一用户服务实例")
    return UserService(db)

# 确保所有认证操作都使用相同的服务实例
def ensure_auth_consistency():
    """确保认证一致性"""
    logger.info("确保认证系统一致性...")
    
    # 应用补丁
    try:
        from app.patches.user_service_patch import patch_user_service_reset_password
        patch_user_service_reset_password()
        logger.info("✅ 用户服务补丁应用成功")
    except ImportError as e:
        logger.warning(f"无法应用用户服务补丁: {e}")
    except Exception as e:
        logger.error(f"应用补丁时发生错误: {e}")
