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
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取部门列表"""
        try:
            result = self.repository.get_all(
                skip=skip,
                limit=limit,
                search=search
            )
            
            # 转换为字典格式
            departments_data = []
            for dept in result["departments"]:
                departments_data.append({
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code,
                    "created_at": dept.created_at.isoformat() if dept.created_at else None
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
            "created_at": department.created_at.isoformat() if department.created_at else None
        }
    
    def create_department(
        self,
        name: str,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """创建部门"""
        try:
            department_data = {
                "name": name.strip(),
                "code": code.strip() if code else None
            }
            
            department = self.repository.create(department_data)
            
            return {
                "id": department.id,
                "name": department.name,
                "code": department.code,
                "created_at": department.created_at.isoformat() if department.created_at else None
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
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新部门"""
        try:
            update_data = {}
            
            if name is not None:
                update_data["name"] = name.strip()
            if code is not None:
                update_data["code"] = code.strip() if code else None
            
            department = self.repository.update(department_id, update_data)
            
            return {
                "id": department.id,
                "name": department.name,
                "code": department.code,
                "created_at": department.created_at.isoformat() if department.created_at else None
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
            departments = self.repository.get_all_for_options()
            
            return [
                {
                    "id": dept.id,
                    "name": dept.name,
                    "code": dept.code
                }
                for dept in departments
            ]
            
        except Exception as e:
            logger.error(f"Error getting department options: {e}")
            return []