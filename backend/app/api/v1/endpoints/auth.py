from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.services.auth_service import AuthService
from app.core.dependencies import get_auth_service, get_current_active_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()


# Request/Response Models
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求模型"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """刷新令牌响应模型"""
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    """修改密码请求模型"""
    old_password: str
    new_password: str


class UpdateProfileRequest(BaseModel):
    """更新个人信息请求模型"""
    email: Optional[EmailStr] = None
    theme: Optional[str] = None


class UserProfileResponse(BaseModel):
    """用户个人信息响应模型"""
    id: int
    username: str
    email: Optional[str]
    role: str
    theme: str
    is_active: bool


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登录
    
    Args:
        request: 登录请求数据
        auth_service: 认证服务
    
    Returns:
        LoginResponse: 登录响应，包含访问令牌、刷新令牌和用户信息
    
    Raises:
        HTTPException: 认证失败时抛出401错误
    """
    try:
        access_token, refresh_token, user_info = auth_service.login(
            request.username, 
            request.password
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=user_info
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录过程中发生错误"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    用户登出
    
    Args:
        credentials: HTTP认证凭据
        auth_service: 认证服务
    
    Returns:
        dict: 登出成功消息
    """
    try:
        token = credentials.credentials
        auth_service.logout(token)
        
        return {"message": "登出成功"}
    
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        # 即使出错也返回成功，因为登出是客户端操作
        return {"message": "登出成功"}


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    刷新访问令牌
    
    Args:
        request: 刷新令牌请求数据
        auth_service: 认证服务
    
    Returns:
        RefreshTokenResponse: 新的访问令牌
    
    Raises:
        HTTPException: 刷新令牌无效时抛出401错误
    """
    try:
        new_access_token = auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(access_token=new_access_token)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新过程中发生错误"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户个人信息
    
    Args:
        current_user: 当前认证用户
    
    Returns:
        UserProfileResponse: 用户个人信息
    """
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.value,
        theme=current_user.theme.value,
        is_active=current_user.is_active
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    更新用户个人信息
    
    Args:
        request: 更新请求数据
        current_user: 当前认证用户
        auth_service: 认证服务
    
    Returns:
        UserProfileResponse: 更新后的用户信息
    
    Raises:
        HTTPException: 更新失败时抛出错误
    """
    try:
        user_info = auth_service.update_profile(
            current_user.id,
            email=request.email,
            theme=request.theme
        )
        
        return UserProfileResponse(**user_info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新个人信息过程中发生错误"
        )


@router.put("/password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    修改用户密码
    
    Args:
        request: 修改密码请求数据
        current_user: 当前认证用户
        auth_service: 认证服务
    
    Returns:
        dict: 修改成功消息
    
    Raises:
        HTTPException: 修改失败时抛出错误
    """
    try:
        auth_service.change_password(
            current_user.id,
            request.old_password,
            request.new_password
        )
        
        return {"message": "密码修改成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password change: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码过程中发生错误"
        )


@router.get("/verify")
async def verify_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    验证访问令牌
    
    Args:
        current_user: 当前认证用户
    
    Returns:
        dict: 验证结果和用户基本信息
    """
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role.value
        }
    }