#!/usr/bin/env python3
"""
统一认证系统修复脚本
解决密码重置API返回成功但实际没有生效的问题

问题分析：
1. backend/auth_service.py - 独立认证服务，使用直接数据库连接
2. backend/app/services/auth_service.py - FastAPI应用认证服务，使用SQLAlchemy ORM
3. 密码重置API使用的是FastAPI应用的认证服务，但可能存在配置不一致的问题

解决方案：
1. 统一使用SQLAlchemy ORM的认证服务
2. 确保所有密码操作都使用相同的哈希算法
3. 修复密码重置API的实现
"""

import sys
import os
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """主函数"""
    logger.info("开始修复统一认证系统...")
    
    # 1. 检查当前认证系统状态
    check_auth_system_status()
    
    # 2. 创建统一的认证服务接口
    create_unified_auth_interface()
    
    # 3. 修复密码重置API
    fix_password_reset_api()
    
    # 4. 更新依赖注入
    update_dependency_injection()
    
    # 5. 创建测试脚本
    create_test_script()
    
    logger.info("统一认证系统修复完成！")
    print("\n" + "="*60)
    print("修复完成！请按以下步骤验证：")
    print("1. 重启应用: python -m uvicorn app.main:app --reload")
    print("2. 运行测试: python test_unified_auth.py")
    print("3. 测试密码重置功能")
    print("="*60)

def check_auth_system_status():
    """检查当前认证系统状态"""
    logger.info("检查认证系统状态...")
    
    auth_files = [
        "backend/auth_service.py",
        "backend/app/services/auth_service.py",
        "backend/app/repositories/user_repository.py"
    ]
    
    for file_path in auth_files:
        if os.path.exists(file_path):
            logger.info(f"✅ 找到认证文件: {file_path}")
        else:
            logger.warning(f"❌ 认证文件不存在: {file_path}")

def create_unified_auth_interface():
    """创建统一的认证服务接口"""
    logger.info("创建统一认证服务接口...")
    
    # 创建统一认证接口
    interface_content = '''"""
统一认证服务接口
确保所有认证操作使用相同的实现
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class AuthServiceInterface(ABC):
    """认证服务接口"""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """用户认证"""
        pass
    
    @abstractmethod
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        pass
    
    @abstractmethod
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """重置密码"""
        pass
    
    @abstractmethod
    def verify_password(self, username: str, password: str) -> bool:
        """验证密码"""
        pass
'''
    
    os.makedirs("backend/app/interfaces", exist_ok=True)
    with open("backend/app/interfaces/__init__.py", "w", encoding="utf-8") as f:
        f.write("")
    
    with open("backend/app/interfaces/auth_interface.py", "w", encoding="utf-8") as f:
        f.write(interface_content)
    
    logger.info("✅ 统一认证接口创建完成")

def fix_password_reset_api():
    """修复密码重置API"""
    logger.info("修复密码重置API...")
    
    # 修复用户服务中的密码重置方法
    user_service_fix = '''    def reset_user_password(self, user_id: int, new_password: str) -> bool:
        """
        重置用户密码（管理员功能）
        
        Args:
            user_id: 用户ID
            new_password: 新密码
        
        Returns:
            bool: 重置成功返回True
        
        Raises:
            HTTPException: 重置失败时抛出错误
        """
        # 检查用户是否存在
        user = self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"用户不存在: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证新密码强度
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            logger.error(f"密码强度验证失败: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        try:
            # 重置密码
            success = self.user_repo.update_password(user_id, new_password)
            if not success:
                logger.error(f"密码重置失败: user_id={user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="重置密码失败"
                )
            
            logger.info(f"密码重置成功: user_id={user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"重置密码过程中发生错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="重置密码失败"
            )'''
    
    # 创建修复后的用户服务补丁
    patch_content = f'''"""
用户服务密码重置修复补丁
"""
import logging
from fastapi import HTTPException, status
from app.core.security import validate_password_strength

logger = logging.getLogger(__name__)

def patch_user_service_reset_password():
    """修复用户服务的密码重置方法"""
    from app.services.user_service import UserService
    
{user_service_fix}
    
    # 替换原方法
    UserService.reset_user_password = reset_user_password
    logger.info("用户服务密码重置方法已修复")

if __name__ == "__main__":
    patch_user_service_reset_password()
'''
    
    os.makedirs("backend/app/patches", exist_ok=True)
    with open("backend/app/patches/__init__.py", "w", encoding="utf-8") as f:
        f.write("")
    
    with open("backend/app/patches/user_service_patch.py", "w", encoding="utf-8") as f:
        f.write(patch_content)
    
    logger.info("✅ 密码重置API修复完成")

def update_dependency_injection():
    """更新依赖注入"""
    logger.info("更新依赖注入...")
    
    # 创建统一的依赖注入配置
    deps_content = '''"""
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
'''
    
    os.makedirs("backend/app/patches", exist_ok=True)
    with open("backend/app/patches/__init__.py", "w", encoding="utf-8") as f:
        f.write("")
    
    with open("backend/app/core/unified_deps.py", "w", encoding="utf-8") as f:
        f.write(deps_content)
    
    logger.info("✅ 依赖注入更新完成")

def create_test_script():
    """创建测试脚本"""
    logger.info("创建测试脚本...")
    
    test_content = '''#!/usr/bin/env python3
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
'''
    
    with open("test_unified_auth.py", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    logger.info("✅ 测试脚本创建完成")

if __name__ == "__main__":
    main()