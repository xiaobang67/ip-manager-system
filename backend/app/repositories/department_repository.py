"""
部门数据访问层
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.department import Department
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class DepartmentRepository:
    """部门数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, department_id: int) -> Optional[Department]:
        """根据ID获取部门"""
        return self.db.query(Department).filter(Department.id == department_id).first()
    
    def get_by_name(self, name: str) -> Optional[Department]:
        """根据名称获取部门"""
        return self.db.query(Department).filter(Department.name == name).first()
    
    def get_by_code(self, code: str) -> Optional[Department]:
        """根据编码获取部门"""
        if not code:
            return None
        return self.db.query(Department).filter(Department.code == code).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取部门列表"""
        query = self.db.query(Department)
        
        # 活跃状态过滤
        if active_only:
            query = query.filter(Department.is_active == True)
        
        # 搜索过滤
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Department.name.ilike(search_pattern),
                    Department.code.ilike(search_pattern),
                    Department.manager.ilike(search_pattern)
                )
            )
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        departments = query.order_by(Department.name).offset(skip).limit(limit).all()
        
        return {
            "departments": departments,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    def create(self, department_data: Dict[str, Any]) -> Department:
        """创建部门"""
        # 检查名称是否已存在
        if self.get_by_name(department_data["name"]):
            raise ValidationError(f"部门名称 '{department_data['name']}' 已存在")
        
        # 检查编码是否已存在（如果提供了编码）
        if department_data.get("code") and self.get_by_code(department_data["code"]):
            raise ValidationError(f"部门编码 '{department_data['code']}' 已存在")
        
        department = Department(**department_data)
        self.db.add(department)
        self.db.commit()
        self.db.refresh(department)
        
        logger.info(f"Created department: {department.name} (ID: {department.id})")
        return department
    
    def update(self, department_id: int, update_data: Dict[str, Any]) -> Department:
        """更新部门"""
        department = self.get_by_id(department_id)
        if not department:
            raise NotFoundError(f"部门 ID {department_id} 不存在")
        
        # 检查名称冲突（如果要更新名称）
        if "name" in update_data and update_data["name"] != department.name:
            existing = self.get_by_name(update_data["name"])
            if existing and existing.id != department_id:
                raise ValidationError(f"部门名称 '{update_data['name']}' 已存在")
        
        # 检查编码冲突（如果要更新编码）
        if "code" in update_data and update_data["code"] != department.code:
            if update_data["code"]:  # 只有当编码不为空时才检查
                existing = self.get_by_code(update_data["code"])
                if existing and existing.id != department_id:
                    raise ValidationError(f"部门编码 '{update_data['code']}' 已存在")
        
        # 更新字段
        for field, value in update_data.items():
            if hasattr(department, field):
                setattr(department, field, value)
        
        self.db.commit()
        self.db.refresh(department)
        
        logger.info(f"Updated department: {department.name} (ID: {department.id})")
        return department
    
    def delete(self, department_id: int) -> bool:
        """删除部门"""
        department = self.get_by_id(department_id)
        if not department:
            raise NotFoundError(f"部门 ID {department_id} 不存在")
        
        # 这里可以添加检查是否有关联的IP地址等
        # 暂时直接删除
        
        self.db.delete(department)
        self.db.commit()
        
        logger.info(f"Deleted department: {department.name} (ID: {department.id})")
        return True
    
    def get_active_departments_for_options(self) -> List[Department]:
        """获取活跃部门列表（用于下拉选项）"""
        return self.db.query(Department).filter(
            Department.is_active == True
        ).order_by(Department.name).all()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取部门统计信息"""
        total = self.db.query(Department).count()
        active = self.db.query(Department).filter(Department.is_active == True).count()
        inactive = total - active
        
        return {
            "total_departments": total,
            "active_departments": active,
            "inactive_departments": inactive
        }