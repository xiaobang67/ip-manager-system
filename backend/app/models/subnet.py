from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Subnet(Base):
    __tablename__ = "subnets"

    id = Column(Integer, primary_key=True, index=True)
    network = Column(String(18), nullable=False, unique=True, index=True)  # CIDR格式
    netmask = Column(String(15), nullable=False)
    gateway = Column(String(15))
    description = Column(Text)
    vlan_id = Column(Integer, index=True)
    location = Column(String(100))
    created_by = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_subnets")
    ip_addresses = relationship("IPAddress", back_populates="subnet", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="subnet_tags", back_populates="subnets")
    alert_rules = relationship("AlertRule", back_populates="subnet")

    def __repr__(self):
        return f"<Subnet(id={self.id}, network='{self.network}', vlan_id={self.vlan_id})>"