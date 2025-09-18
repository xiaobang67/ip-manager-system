"""
用户管理API端点
提供用户CRUD操作的REST接口
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from app.services.user_service import UserService
from app.core.dependencies import (
    get_current_active_user, 
    require_admin, 
    require_manager_or_admin,
    get_db
)
from app.models.user import User, UserRole, UserTheme
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response Models
class CreateUserRequest(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=8, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    role: str = Field(default="user", description="用户角色")


class UpdateUserRequest(BaseModel):
    """更新用户请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    role: Optional[str] = Field(None, description="用户角色")
    theme: Optional[str] = Field(None, description="主题设置")
    is_active: Optional[bool] = Field(None, description="是否激活")


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    new_password: str = Field(..., min_length=8, description="新密码")


class UserResponse(BaseModel):
    """用户响应模型"""
    id: int
    username: str
    email: Optional[str]
    role: str
    theme: str
    is_active: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    skip: int
    limit: int


class UserStatisticsResponse(BaseModel):
    """用户统计响应模型"""
    total_users: int
    active_users: int
    inactive_users: int
    role_distribution: dict


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """获取用户服务实例"""
    return UserService(db)


@router.get("/", response_model=UserListResponse)
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    active_only: bool = Query(True, description="是否只返回活跃用户"),
    role_filter: Optional[str] = Query(None, description="角色过滤器"),
    current_user: User = Depends(require_manager_or_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户列表
    
    需要管理员或经理权限
    """
    try:
        result = user_service.get_users(
            skip=skip,
            limit=limit,
            active_only=active_only,
            role_filter=role_filter
        )
        
        return UserListResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )


@router.get("/statistics", response_model=UserStatisticsResponse)
async def get_user_statistics(
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    获取用户统计信息
    
    需要管理员权限
    """
    try:
        stats = user_service.get_user_statistics()
        return UserStatisticsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户统计信息失败"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_manager_or_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    根据ID获取用户详情
    
    需要管理员或经理权限
    """
    try:
        user_data = user_service.get_user_by_id(user_id)
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户信息失败"
        )


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    创建新用户
    
    需要管理员权限
    """
    try:
        user_data = user_service.create_user(
            username=request.username,
            password=request.password,
            email=request.email,
            role=request.role
        )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建用户失败"
        )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    更新用户信息
    
    需要管理员权限
    """
    try:
        user_data = user_service.update_user(
            user_id=user_id,
            username=request.username,
            email=request.email,
            role=request.role,
            theme=request.theme,
            is_active=request.is_active
        )
        
        return UserResponse(**user_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户失败"
        )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    删除用户
    
    需要管理员权限
    """
    try:
        user_service.delete_user(user_id, current_user.id)
        
        return {"message": "用户删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )


@router.put("/{user_id}/password")
async def reset_user_password(
    user_id: int,
    request: ResetPasswordRequest,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    重置用户密码
    
    需要管理员权限
    """
    try:
        user_service.reset_user_password(user_id, request.new_password)
        
        return {"message": "密码重置成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in reset_user_password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败"
        )


@router.put("/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    user_service: UserService = Depends(get_user_service)
):
    """
    切换用户激活状态
    
    需要管理员权限
    """
    try:
        result = user_service.toggle_user_status(user_id, current_user.id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in toggle_user_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="切换用户状态失败"
        )


@router.get("/roles/available")
async def get_available_roles(
    current_user: User = Depends(require_manager_or_admin)
):
    """
    获取可用的用户角色列表
    
    需要管理员或经理权限
    """
    roles = []
    for role in UserRole:
        roles.append({
            "value": role.value,
            "label": {
                "admin": "管理员",
                "manager": "经理",
                "user": "普通用户",
                "readonly": "只读用户"
            }.get(role.value, role.value)
        })
    
    return {"roles": roles}


@router.get("/themes/available")
async def get_available_themes(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取可用的主题列表
    
    需要登录
    """
    themes = []
    for theme in UserTheme:
        themes.append({
            "value": theme.value,
            "label": {
                "light": "明亮主题",
                "dark": "暗黑主题"
            }.get(theme.value, theme.value)
        })
    
    return {"themes": themes}