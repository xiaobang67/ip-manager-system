"""
部门管理服务层
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.department_repository import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.core.exceptions import NotFoundError, ValidationError
import logging

logger = logging.getLogger(__name__)


class DepartmentService:
    """部门管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = DepartmentRepository(db)
    
    def get_departments(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取部门列表"""
        try:
            result = self.repository.get_all(
                skip=skip,
                limit=limit,
                active_only=active_only,
                search=search
            )
            
            # 转换为字典格式
            departments_data = []
            for dept in result["departments"]:
                departments_data.append({
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code,
                    "description": dept.description,
                    "manager": dept.manager,
                    "contact_email": dept.contact_email,
                    "contact_phone": dept.contact_phone,
                    "is_active": dept.is_active,
                    "created_at": dept.created_at.isoformat() if dept.created_at else None,
                    "updated_at": dept.updated_at.isoformat() if dept.updated_at else None
                })
            
            return {
                "departments": departments_data,
                "total": result["total"],
                "skip": result["skip"],
                "limit": result["limit"]
            }
            
        except Exception as e:
            logger.error(f"Error getting departments: {e}")
            raise
    
    def get_department_by_id(self, department_id: int) -> Dict[str, Any]:
        """根据ID获取部门详情"""
        department = self.repository.get_by_id(department_id)
        if not department:
            raise NotFoundError(f"部门 ID {department_id} 不存在")
        
        return {
            "id": department.id,
            "name": department.name,
            "code": department.code,
            "description": department.description,
            "manager": department.manager,
            "contact_email": department.contact_email,
            "contact_phone": department.contact_phone,
            "is_active": department.is_active,
            "created_at": department.created_at.isoformat() if department.created_at else None,
            "updated_at": department.updated_at.isoformat() if department.updated_at else None
        }
    
    def create_department(
        self,
        name: str,
        code: Optional[str] = None,
        description: Optional[str] = None,
        manager: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建部门"""
        try:
            department_data = {
                "name": name.strip(),
                "code": code.strip() if code else None,
                "description": description.strip() if description else None,
                "manager": manager.strip() if manager else None,
                "contact_email": contact_email.strip() if contact_email else None,
                "contact_phone": contact_phone.strip() if contact_phone else None
            }
            
            department = self.repository.create(department_data)
            
            return {
                "id": department.id,
                "name": department.name,
                "code": department.code,
                "description": department.description,
                "manager": department.manager,
                "contact_email": department.contact_email,
                "contact_phone": department.contact_phone,
                "is_active": department.is_active,
                "created_at": department.created_at.isoformat() if department.created_at else None,
                "updated_at": department.updated_at.isoformat() if department.updated_at else None
            }
            
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error creating department: {e}")
            raise ValidationError("创建部门失败")
    
    def update_department(
        self,
        department_id: int,
        name: Optional[str] = None,
        code: Optional[str] = None,
        description: Optional[str] = None,
        manager: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """更新部门"""
        try:
            update_data = {}
            
            if name is not None:
                update_data["name"] = name.strip()
            if code is not None:
                update_data["code"] = code.strip() if code else None
            if description is not None:
                update_data["description"] = description.strip() if description else None
            if manager is not None:
                update_data["manager"] = manager.strip() if manager else None
            if contact_email is not None:
                update_data["contact_email"] = contact_email.strip() if contact_email else None
            if contact_phone is not None:
                update_data["contact_phone"] = contact_phone.strip() if contact_phone else None
            if is_active is not None:
                update_data["is_active"] = is_active
            
            department = self.repository.update(department_id, update_data)
            
            return {
                "id": department.id,
                "name": department.name,
                "code": department.code,
                "description": department.description,
                "manager": department.manager,
                "contact_email": department.contact_email,
                "contact_phone": department.contact_phone,
                "is_active": department.is_active,
                "created_at": department.created_at.isoformat() if department.created_at else None,
                "updated_at": department.updated_at.isoformat() if department.updated_at else None
            }
            
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error updating department: {e}")
            raise ValidationError("更新部门失败")
    
    def delete_department(self, department_id: int) -> bool:
        """删除部门"""
        try:
            return self.repository.delete(department_id)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            logger.error(f"Error deleting department: {e}")
            raise ValidationError("删除部门失败")
    
    def get_department_options(self) -> List[Dict[str, Any]]:
        """获取部门选项列表（用于下拉菜单）"""
        try:
            departments = self.repository.get_active_departments_for_options()
            
            return [
                {
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code,
                    "is_active": dept.is_active
                }
                for dept in departments
            ]
            
        except Exception as e:
            logger.error(f"Error getting department options: {e}")
            return []
    
    def get_department_statistics(self) -> Dict[str, Any]:
        """获取部门统计信息"""
        try:
            return self.repository.get_statistics()
        except Exception as e:
            logger.error(f"Error getting department statistics: {e}")
            return {
                "total_departments": 0,
                "active_departments": 0,
                "inactive_departments": 0
            }