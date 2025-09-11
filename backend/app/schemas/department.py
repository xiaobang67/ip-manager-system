"""
部门管理相关的Pydantic模型（简化版）
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class DepartmentBase(BaseModel):
    """部门基础模型"""
    name: str = Field(..., min_length=1, max_length=100, description="部门名称")
    code: Optional[str] = Field(None, max_length=50, description="部门编码")


class DepartmentCreate(DepartmentBase):
    """创建部门请求模型"""
    pass


class DepartmentUpdate(BaseModel):
    """更新部门请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="部门名称")
    code: Optional[str] = Field(None, max_length=50, description="部门编码")


class DepartmentResponse(DepartmentBase):
    """部门响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DepartmentListResponse(BaseModel):
    """部门列表响应模型"""
    departments: List[DepartmentResponse]
    total: int
    skip: int
    limit: int


class DepartmentOption(BaseModel):
    """部门选项模型（用于下拉菜单）"""
    id: int
    name: str
    code: Optional[str]