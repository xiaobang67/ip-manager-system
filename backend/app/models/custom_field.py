from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class EntityType(str, enum.Enum):
    IP = "ip"
    SUBNET = "subnet"


class FieldType(str, enum.Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"


class CustomField(Base):
    __tablename__ = "custom_fields"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    field_name = Column(String(50), nullable=False, index=True)
    field_type = Column(Enum(FieldType), nullable=False)
    field_options = Column(JSON)  # 用于select类型的选项
    is_required = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    values = relationship("CustomFieldValue", back_populates="field", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CustomField(id={self.id}, name='{self.field_name}', type='{self.field_type}')>"


class CustomFieldValue(Base):
    __tablename__ = "custom_field_values"

    id = Column(Integer, primary_key=True, index=True)
    field_id = Column(Integer, ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)
    entity_type = Column(Enum(EntityType), nullable=False, index=True)
    field_value = Column(Text)

    # Relationships
    field = relationship("CustomField", back_populates="values")

    def __repr__(self):
        return f"<CustomFieldValue(id={self.id}, field_id={self.field_id}, value='{self.field_value}')>"