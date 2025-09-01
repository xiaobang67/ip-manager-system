"""
部门管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from models import Department
from app.schemas import DepartmentCreate, DepartmentUpdate
from fastapi import HTTPException


class DepartmentService:
    """部门管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_departments(self, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[Department]:
        """获取部门列表"""
        query = self.db.query(Department)
        
        if is_active is not None:
            query = query.filter(Department.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()
    
    def get_department_by_id(self, department_id: int) -> Optional[Department]:
        """根据ID获取部门"""
        return self.db.query(Department).filter(Department.id == department_id).first()
    
    def get_department_by_code(self, code: str) -> Optional[Department]:
        """根据编码获取部门"""
        return self.db.query(Department).filter(Department.code == code).first()
    
    def create_department(self, department_data: DepartmentCreate) -> Department:
        """创建部门"""
        # 检查编码是否已存在
        existing_dept = self.get_department_by_code(department_data.code)
        if existing_dept:
            raise HTTPException(status_code=400, detail="部门编码已存在")
        
        # 如果指定了上级部门，检查是否存在
        if department_data.parent_id:
            parent_dept = self.get_department_by_id(department_data.parent_id)
            if not parent_dept:
                raise HTTPException(status_code=400, detail="上级部门不存在")
        
        # 创建部门
        db_department = Department(**department_data.model_dump())
        self.db.add(db_department)
        self.db.commit()
        self.db.refresh(db_department)
        
        return db_department
    
    def update_department(self, department_id: int, department_data: DepartmentUpdate) -> Department:
        """更新部门"""
        db_department = self.get_department_by_id(department_id)
        if not db_department:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 检查编码是否重复（排除自己）
        if department_data.code:
            existing_dept = self.db.query(Department).filter(
                and_(Department.code == department_data.code, Department.id != department_id)
            ).first()
            if existing_dept:
                raise HTTPException(status_code=400, detail="部门编码已存在")
        
        # 检查上级部门
        if department_data.parent_id:
            # 不能设置自己为上级部门
            if department_data.parent_id == department_id:
                raise HTTPException(status_code=400, detail="不能设置自己为上级部门")
            
            # 检查上级部门是否存在
            parent_dept = self.get_department_by_id(department_data.parent_id)
            if not parent_dept:
                raise HTTPException(status_code=400, detail="上级部门不存在")
            
            # 检查是否会形成循环引用
            if self._would_create_cycle(department_id, department_data.parent_id):
                raise HTTPException(status_code=400, detail="不能设置下级部门为上级部门")
        
        # 更新字段
        update_data = department_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_department, field, value)
        
        self.db.commit()
        self.db.refresh(db_department)
        
        return db_department
    
    def delete_department(self, department_id: int) -> bool:
        """删除部门（软删除）"""
        db_department = self.get_department_by_id(department_id)
        if not db_department:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 检查是否有子部门
        children = self.db.query(Department).filter(Department.parent_id == department_id).count()
        if children > 0:
            raise HTTPException(status_code=400, detail="存在子部门，无法删除")
        
        # 检查是否有关联的用户
        if hasattr(db_department, 'users') and db_department.users:
            raise HTTPException(status_code=400, detail="部门下存在用户，无法删除")
        
        # 软删除
        db_department.is_active = False
        self.db.commit()
        
        return True
    
    def get_department_tree(self) -> List[Department]:
        """获取部门树形结构"""
        # 获取所有活跃部门
        all_departments = self.db.query(Department).filter(Department.is_active == True).all()
        
        # 构建树形结构
        dept_dict = {dept.id: dept for dept in all_departments}
        root_departments = []
        
        for dept in all_departments:
            if dept.parent_id is None:
                root_departments.append(dept)
            else:
                parent = dept_dict.get(dept.parent_id)
                if parent:
                    if not hasattr(parent, '_children'):
                        parent._children = []
                    parent._children.append(dept)
        
        return root_departments
    
    def get_children_departments(self, department_id: int) -> List[Department]:
        """获取指定部门的所有子部门"""
        return self.db.query(Department).filter(
            and_(Department.parent_id == department_id, Department.is_active == True)
        ).all()
    
    def _would_create_cycle(self, department_id: int, new_parent_id: int) -> bool:
        """检查设置新的上级部门是否会造成循环引用"""
        current_id = new_parent_id
        visited = set()
        
        while current_id and current_id not in visited:
            if current_id == department_id:
                return True
            
            visited.add(current_id)
            parent_dept = self.get_department_by_id(current_id)
            current_id = parent_dept.parent_id if parent_dept else None
        
        return False
    
    def get_department_statistics(self, department_id: int) -> dict:
        """获取部门统计信息"""
        department = self.get_department_by_id(department_id)
        if not department:
            raise HTTPException(status_code=404, detail="部门不存在")
        
        # 统计用户数量
        user_count = len(department.users) if department.users else 0
        
        # 统计子部门数量
        children_count = len(department.children) if department.children else 0
        
        # 统计负责的网段数量
        segment_count = len(department.network_segments) if department.network_segments else 0
        
        # 统计分配的IP数量
        ip_count = len(department.ip_addresses) if department.ip_addresses else 0
        
        return {
            "user_count": user_count,
            "children_count": children_count,
            "segment_count": segment_count,
            "ip_count": ip_count
        }