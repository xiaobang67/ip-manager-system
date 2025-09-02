from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# 关联表定义
ip_tags = Table(
    'ip_tags',
    Base.metadata,
    Column('ip_id', Integer, ForeignKey('ip_addresses.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)

subnet_tags = Table(
    'subnet_tags',
    Base.metadata,
    Column('subnet_id', Integer, ForeignKey('subnets.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    color = Column(String(7), default='#007bff')  # 十六进制颜色
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ip_addresses = relationship("IPAddress", secondary=ip_tags, back_populates="tags")
    subnets = relationship("Subnet", secondary=subnet_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}', color='{self.color}')>"


# 为了向后兼容，保留这些类的引用
IPTag = ip_tags
SubnetTag = subnet_tags