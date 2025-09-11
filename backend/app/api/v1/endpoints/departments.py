"""
部门管理API端点
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from app.services.department_service import DepartmentService
from app.core.dependencies import (
    get_current_active_user, 
    require_admin, 
    require_manager_or_admin,
    get_db
)
from app.models.user import User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentListResponse,
    DepartmentOption
)
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_department_service(db: Session = Depends(get_db)) -> DepartmentService:
    """获取部门服务实例"""
    return DepartmentService(db)


@router.get("/", response_model=DepartmentListResponse)
async def get_departments(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=100, description="返回的记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user),
    department_service: DepartmentService = Depends(get_department_service)
):
    """
    获取部门列表
    
    需要登录用户权限
    """
    try:
        result = department_service.get_departments(
            skip=skip,
            limit=limit,
            search=search
        )
        
        return DepartmentListResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_departments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取部门列表失败"
        )


@router.get("/options")
async def get_department_options(
    current_user: User = Depends(get_current_active_user),
    department_service: DepartmentService = Depends(get_department_service)
):
    """
    获取部门选项列表（用于下拉菜单）
    
    需要登录用户权限
    """
    try:
        options = department_service.get_department_options()
        return {"departments": options}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_department_options: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取部门选项失败"
        )


# 移除统计功能


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    department_service: DepartmentService = Depends(get_department_service)
):
    """
    根据ID获取部门详情
    
    需要登录用户权限
    """
    try:
        department_data = department_service.get_department_by_id(department_id)
        return DepartmentResponse(**department_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_department: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取部门信息失败"
        )


@router.post("/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    request: DepartmentCreate,
    current_user: User = Depends(require_manager_or_admin),
    department_service: DepartmentService = Depends(get_department_service)
):
    """
    创建新部门
    
    需要管理员或经理权限
    """
    try:
        department_data = department_service.create_department(
            name=request.name,
            code=request.code
        )
        
        return DepartmentResponse(**department_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_department: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建部门失败"
        )


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    request: DepartmentUpdate,
    current_user: User = Depends(require_manager_or_admin),
    department_service: DepartmentService = Depends(get_department_service)
):
    """
    更新部门信息
    
    需要管理员或经理权限
    """
    try:
        department_data = department_service.update_department(
            department_id=department_id,
            name=request.name,
            code=request.code
        )
        
        return DepartmentResponse(**department_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_department: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新部门失败"
        )


@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    current_user: User = Depends(require_manager_or_admin),
    department_service: DepartmentService = Depends(get_department_service)
):
    """
    删除部门
    
    需要管理员或经理权限
    """
    try:
        department_service.delete_department(department_id)
        
        return {"message": "部门删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_department: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除部门失败"
        )