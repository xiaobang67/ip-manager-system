from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False, index=True)  # CREATE, UPDATE, DELETE, ALLOCATE, RELEASE
    entity_type = Column(String(20), nullable=False, index=True)  # ip, subnet, user
    entity_id = Column(Integer, index=True)
    old_values = Column(JSON)
    new_values = Column(JSON)
    ip_address = Column(String(45))  # 操作者IP
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity_type='{self.entity_type}')>"