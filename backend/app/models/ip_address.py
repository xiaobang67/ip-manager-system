from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class IPStatus(str, enum.Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    CONFLICT = "conflict"


class IPAddress(Base):
    __tablename__ = "ip_addresses"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(15), nullable=False, unique=True, index=True)
    subnet_id = Column(Integer, ForeignKey("subnets.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(IPStatus), default=IPStatus.AVAILABLE, index=True)
    mac_address = Column(String(17), index=True)
    user_name = Column(String(255), index=True)
    device_type = Column(String(50))
    location = Column(String(100))
    assigned_to = Column(String(100))
    description = Column(Text)
    allocated_at = Column(DateTime(timezone=True))
    allocated_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subnet = relationship("Subnet", back_populates="ip_addresses")
    allocator = relationship("User", back_populates="allocated_ips")
    tags = relationship("Tag", secondary="ip_tags", back_populates="ip_addresses")

    def __repr__(self):
        return f"<IPAddress(id={self.id}, ip='{self.ip_address}', status='{self.status}')>"