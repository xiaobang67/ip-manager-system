from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    READONLY = "readonly"


class UserTheme(str, enum.Enum):
    LIGHT = "light"
    DARK = "dark"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.USER, index=True)
    theme = Column(Enum(UserTheme), default=UserTheme.LIGHT)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    created_subnets = relationship("Subnet", back_populates="creator")
    allocated_ips = relationship("IPAddress", back_populates="allocator")
    audit_logs = relationship("AuditLog", back_populates="user")
    updated_configs = relationship("SystemConfig", back_populates="updater")
    created_alert_rules = relationship("AlertRule", back_populates="creator")
    resolved_alerts = relationship("AlertHistory", back_populates="resolver")
    search_history = relationship("SearchHistory", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"