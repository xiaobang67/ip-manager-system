from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class RuleType(str, enum.Enum):
    UTILIZATION = "utilization"
    CONFLICT = "conflict"
    EXPIRY = "expiry"


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rule_type = Column(Enum(RuleType), nullable=False, index=True)
    threshold_value = Column(DECIMAL(5, 2))  # 阈值，如使用率80%
    subnet_id = Column(Integer, ForeignKey("subnets.id", ondelete="CASCADE"))  # 可选，针对特定网段的规则
    is_active = Column(Boolean, default=True, index=True)
    notification_emails = Column(Text)  # JSON格式的邮箱列表
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subnet = relationship("Subnet", back_populates="alert_rules")
    creator = relationship("User", back_populates="created_alert_rules")
    alert_history = relationship("AlertHistory", back_populates="rule", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<AlertRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False)
    alert_message = Column(Text, nullable=False)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.MEDIUM, index=True)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    rule = relationship("AlertRule", back_populates="alert_history")
    resolver = relationship("User", back_populates="resolved_alerts")

    def __repr__(self):
        return f"<AlertHistory(id={self.id}, rule_id={self.rule_id}, severity='{self.severity}')>"