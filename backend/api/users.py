"""
用户管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from services.user_service import UserService
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, 
    MessageResponse, PaginatedResponse
)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    department_id: Optional[int] = Query(None, description="部门ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    service = UserService(db)
    users = service.get_users(
        skip=skip, 
        limit=limit, 
        department_id=department_id,
        is_active=is_active,
        search=search
    )
    return users


@router.get("/search", response_model=List[UserResponse])
async def search_users(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量"),
    db: Session = Depends(get_db)
):
    """搜索用户"""
    service = UserService(db)
    users = service.search_users(q, limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """根据ID获取用户详情"""
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """创建用户"""
    service = UserService(db)
    return service.create_user(user_data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """更新用户"""
    service = UserService(db)
    return service.update_user(user_id, user_data)


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除用户"""
    service = UserService(db)
    service.delete_user(user_id)
    return MessageResponse(message="用户删除成功")


@router.get("/department/{department_id}", response_model=List[UserResponse])
async def get_users_by_department(
    department_id: int,
    include_subdepartments: bool = Query(False, description="是否包含子部门"),
    db: Session = Depends(get_db)
):
    """获取部门用户列表"""
    service = UserService(db)
    users = service.get_users_by_department(department_id, include_subdepartments)
    return users


@router.post("/transfer", response_model=List[UserResponse])
async def transfer_users_to_department(
    user_ids: List[int],
    new_department_id: int,
    db: Session = Depends(get_db)
):
    """批量转移用户到新部门"""
    service = UserService(db)
    users = service.transfer_users_to_department(user_ids, new_department_id)
    return users


@router.get("/{user_id}/statistics")
async def get_user_statistics(user_id: int, db: Session = Depends(get_db)):
    """获取用户统计信息"""
    service = UserService(db)
    return service.get_user_statistics(user_id)