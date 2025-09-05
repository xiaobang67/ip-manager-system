"""
部门管理模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=True, index=True)  # 部门编码
    description = Column(Text, nullable=True)
    manager = Column(String(100), nullable=True)  # 部门负责人
    contact_email = Column(String(100), nullable=True)  # 联系邮箱
    contact_phone = Column(String(50), nullable=True)  # 联系电话
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', code='{self.code}')>"