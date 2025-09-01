"""
部门管理API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.connection import get_db
from services.department_service import DepartmentService
from app.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, 
    MessageResponse, PaginatedResponse
)

router = APIRouter()


@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=1000, description="每页记录数"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    db: Session = Depends(get_db)
):
    """获取部门列表"""
    service = DepartmentService(db)
    departments = service.get_departments(skip=skip, limit=limit, is_active=is_active)
    
    # 手动构建响应以避免循环引用
    result = []
    for dept in departments:
        dept_data = {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "parent_id": dept.parent_id,
            "description": dept.description,
            "is_active": dept.is_active,
            "created_at": dept.created_at,
            "updated_at": dept.updated_at,
            "parent": {
                "id": dept.parent.id,
                "name": dept.parent.name,
                "code": dept.parent.code
            } if dept.parent else None,
            "children": None  # 列表中不返回子部门
        }
        result.append(dept_data)
    
    return result


@router.get("/tree", response_model=List[DepartmentResponse])
async def get_department_tree(db: Session = Depends(get_db)):
    """获取部门树形结构"""
    service = DepartmentService(db)
    tree = service.get_department_tree()
    
    def build_tree_response(departments):
        """递归构建树形响应"""
        result = []
        for dept in departments:
            # 获取子部门
            children_depts = service.get_children_departments(dept.id)
            children_simple = [{
                "id": child.id,
                "name": child.name,
                "code": child.code
            } for child in children_depts]
            
            dept_data = {
                "id": dept.id,
                "name": dept.name,
                "code": dept.code,
                "parent_id": dept.parent_id,
                "description": dept.description,
                "is_active": dept.is_active,
                "created_at": dept.created_at,
                "updated_at": dept.updated_at,
                "parent": {
                    "id": dept.parent.id,
                    "name": dept.parent.name,
                    "code": dept.parent.code
                } if dept.parent else None,
                "children": children_simple
            }
            result.append(dept_data)
        
        return result
    
    return build_tree_response(tree)


@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(department_id: int, db: Session = Depends(get_db)):
    """根据ID获取部门详情"""
    service = DepartmentService(db)
    department = service.get_department_by_id(department_id)
    if not department:
        raise HTTPException(status_code=404, detail="部门不存在")
    return department


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department(
    department_data: DepartmentCreate,
    db: Session = Depends(get_db)
):
    """创建部门"""
    service = DepartmentService(db)
    new_department = service.create_department(department_data)
    
    # 手动构建响应以避免循环引用
    response_data = {
        "id": new_department.id,
        "name": new_department.name,
        "code": new_department.code,
        "parent_id": new_department.parent_id,
        "description": new_department.description,
        "is_active": new_department.is_active,
        "created_at": new_department.created_at,
        "updated_at": new_department.updated_at,
        "parent": {
            "id": new_department.parent.id,
            "name": new_department.parent.name,
            "code": new_department.parent.code
        } if new_department.parent else None,
        "children": None  # 新创建的部门不会有子部门
    }
    
    return response_data


@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db)
):
    """更新部门"""
    service = DepartmentService(db)
    return service.update_department(department_id, department_data)


@router.delete("/{department_id}", response_model=MessageResponse)
async def delete_department(department_id: int, db: Session = Depends(get_db)):
    """删除部门"""
    service = DepartmentService(db)
    service.delete_department(department_id)
    return MessageResponse(message="部门删除成功")


@router.get("/{department_id}/children", response_model=List[DepartmentResponse])
async def get_children_departments(department_id: int, db: Session = Depends(get_db)):
    """获取子部门列表"""
    service = DepartmentService(db)
    children = service.get_children_departments(department_id)
    return children


@router.get("/{department_id}/statistics")
async def get_department_statistics(department_id: int, db: Session = Depends(get_db)):
    """获取部门统计信息"""
    service = DepartmentService(db)
    return service.get_department_statistics(department_id)