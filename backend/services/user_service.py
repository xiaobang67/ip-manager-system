"""
用户管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models import User, Department
from app.schemas import UserCreate, UserUpdate
from fastapi import HTTPException


class UserService:
    """用户管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_users(self, skip: int = 0, limit: int = 100, 
                  department_id: Optional[int] = None, 
                  is_active: Optional[bool] = None,
                  search: Optional[str] = None) -> List[User]:
        """获取用户列表"""
        try:
            query = self.db.query(User)
            
            # 按部门筛选
            if department_id is not None:
                query = query.filter(User.department_id == department_id)
            
            # 按激活状态筛选
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            # 搜索功能
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    or_(
                        User.username.like(search_pattern),
                        User.real_name.like(search_pattern),
                        User.email.like(search_pattern),
                        User.employee_id.like(search_pattern)
                    )
                )
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            print(f"Error in get_users: {e}")
            return []
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_employee_id(self, employee_id: str) -> Optional[User]:
        """根据员工编号获取用户"""
        return self.db.query(User).filter(User.employee_id == employee_id).first()
    
    def create_user(self, user_data: UserCreate) -> User:
        """创建用户"""
        # 检查用户名是否已存在
        existing_user = self.get_user_by_username(user_data.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = self.get_user_by_email(user_data.email)
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被使用")
        
        # 检查员工编号是否已存在
        if user_data.employee_id:
            existing_employee = self.get_user_by_employee_id(user_data.employee_id)
            if existing_employee:
                raise HTTPException(status_code=400, detail="员工编号已存在")
        
        # 检查部门是否存在
        if user_data.department_id:
            department = self.db.query(Department).filter(Department.id == user_data.department_id).first()
            if not department:
                raise HTTPException(status_code=400, detail="指定的部门不存在")
        
        # 创建用户
        db_user = User(**user_data.model_dump())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """更新用户"""
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查用户名是否重复（排除自己）
        if user_data.username:
            existing_user = self.db.query(User).filter(
                and_(User.username == user_data.username, User.id != user_id)
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 检查邮箱是否重复（排除自己）
        if user_data.email:
            existing_email = self.db.query(User).filter(
                and_(User.email == user_data.email, User.id != user_id)
            ).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="邮箱已被使用")
        
        # 检查员工编号是否重复（排除自己）
        if user_data.employee_id:
            existing_employee = self.db.query(User).filter(
                and_(User.employee_id == user_data.employee_id, User.id != user_id)
            ).first()
            if existing_employee:
                raise HTTPException(status_code=400, detail="员工编号已存在")
        
        # 检查部门是否存在
        if user_data.department_id:
            department = self.db.query(Department).filter(Department.id == user_data.department_id).first()
            if not department:
                raise HTTPException(status_code=400, detail="指定的部门不存在")
        
        # 更新字段
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户（软删除）"""
        db_user = self.get_user_by_id(user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 检查是否有关联的IP分配
        if hasattr(db_user, 'assigned_ips') and db_user.assigned_ips:
            active_ips = [ip for ip in db_user.assigned_ips if ip.status == 'allocated']
            if active_ips:
                raise HTTPException(status_code=400, detail="用户还有分配的IP地址，无法删除")
        
        # 检查是否有活跃的地址保留
        if hasattr(db_user, 'reserved_addresses') and db_user.reserved_addresses:
            active_reservations = [res for res in db_user.reserved_addresses if res.is_active]
            if active_reservations:
                raise HTTPException(status_code=400, detail="用户还有活跃的地址保留，无法删除")
        
        # 软删除
        db_user.is_active = False
        self.db.commit()
        
        return True
    
    def get_users_by_department(self, department_id: int, include_subdepartments: bool = False) -> List[User]:
        """获取指定部门的用户"""
        if include_subdepartments:
            # 获取部门及其所有子部门的用户
            department_ids = self._get_department_and_children_ids(department_id)
            return self.db.query(User).filter(
                and_(User.department_id.in_(department_ids), User.is_active == True)
            ).all()
        else:
            # 只获取当前部门的用户
            return self.db.query(User).filter(
                and_(User.department_id == department_id, User.is_active == True)
            ).all()
    
    def transfer_users_to_department(self, user_ids: List[int], new_department_id: int) -> List[User]:
        """批量转移用户到新部门"""
        # 检查新部门是否存在
        department = self.db.query(Department).filter(Department.id == new_department_id).first()
        if not department:
            raise HTTPException(status_code=400, detail="目标部门不存在")
        
        # 获取要转移的用户
        users = self.db.query(User).filter(User.id.in_(user_ids)).all()
        if len(users) != len(user_ids):
            raise HTTPException(status_code=400, detail="部分用户不存在")
        
        # 执行转移
        for user in users:
            user.department_id = new_department_id
        
        self.db.commit()
        
        return users
    
    def get_user_statistics(self, user_id: int) -> dict:
        """获取用户统计信息"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 统计分配的IP数量
        allocated_ips = len([ip for ip in user.assigned_ips if ip.status == 'allocated']) if user.assigned_ips else 0
        
        # 统计负责的网段数量
        responsible_segments = len(user.responsible_segments) if user.responsible_segments else 0
        
        # 统计地址保留数量
        active_reservations = len([res for res in user.reserved_addresses if res.is_active]) if user.reserved_addresses else 0
        
        return {
            "allocated_ips": allocated_ips,
            "responsible_segments": responsible_segments,
            "active_reservations": active_reservations
        }
    
    def _get_department_and_children_ids(self, department_id: int) -> List[int]:
        """递归获取部门及其所有子部门的ID"""
        department_ids = [department_id]
        
        children = self.db.query(Department).filter(Department.parent_id == department_id).all()
        for child in children:
            department_ids.extend(self._get_department_and_children_ids(child.id))
        
        return department_ids
    
    def search_users(self, query: str, limit: int = 10) -> List[User]:
        """搜索用户"""
        search_pattern = f"%{query}%"
        return self.db.query(User).filter(
            and_(
                User.is_active == True,
                or_(
                    User.username.like(search_pattern),
                    User.real_name.like(search_pattern),
                    User.email.like(search_pattern),
                    User.employee_id.like(search_pattern)
                )
            )
        ).limit(limit).all()