"""
用户服务密码重置修复补丁
"""
import logging
from fastapi import HTTPException, status
from app.core.security import validate_password_strength

logger = logging.getLogger(__name__)

def patch_user_service_reset_password():
    """修复用户服务的密码重置方法"""
    from app.services.user_service import UserService
    
    def reset_user_password(self, user_id: int, new_password: str) -> bool:
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
            )
    
    # 替换原方法
    UserService.reset_user_password = reset_user_password
    logger.info("用户服务密码重置方法已修复")

if __name__ == "__main__":
    patch_user_service_reset_password()
