"""
警报服务 - 处理警报规则和警报历史
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.alert import AlertRule, AlertHistory, RuleType, AlertSeverity
from app.models.subnet import Subnet
from app.schemas.monitoring import AlertRuleCreate, AlertRuleUpdate
from app.services.monitoring_service import MonitoringService
from fastapi import HTTPException
import json


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def get_alert_rules(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        is_active: Optional[bool] = None
    ) -> List[AlertRule]:
        """
        获取警报规则列表
        """
        query = self.db.query(AlertRule)
        
        if is_active is not None:
            query = query.filter(AlertRule.is_active == is_active)
        
        return query.offset(skip).limit(limit).all()

    def create_alert_rule(self, rule_data: AlertRuleCreate, user_id: int) -> AlertRule:
        """
        创建警报规则
        """
        # 验证规则类型
        if rule_data.rule_type not in [rt.value for rt in RuleType]:
            raise HTTPException(status_code=400, detail="无效的规则类型")
        
        # 验证网段是否存在（如果指定了网段）
        if rule_data.subnet_id:
            subnet = self.db.query(Subnet).filter(Subnet.id == rule_data.subnet_id).first()
            if not subnet:
                raise HTTPException(status_code=404, detail="指定的网段不存在")

        # 验证邮箱格式（如果提供了邮箱）
        if rule_data.notification_emails:
            try:
                emails = json.loads(rule_data.notification_emails)
                if not isinstance(emails, list):
                    raise ValueError("邮箱列表格式错误")
            except (json.JSONDecodeError, ValueError):
                raise HTTPException(status_code=400, detail="邮箱列表格式错误，应为JSON数组")

        alert_rule = AlertRule(
            name=rule_data.name,
            rule_type=RuleType(rule_data.rule_type),
            threshold_value=rule_data.threshold_value,
            subnet_id=rule_data.subnet_id,
            notification_emails=rule_data.notification_emails,
            created_by=user_id
        )

        self.db.add(alert_rule)
        self.db.commit()
        self.db.refresh(alert_rule)

        return alert_rule

    def update_alert_rule(self, rule_id: int, rule_data: AlertRuleUpdate) -> AlertRule:
        """
        更新警报规则
        """
        alert_rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not alert_rule:
            raise HTTPException(status_code=404, detail="警报规则不存在")

        # 更新字段
        if rule_data.name is not None:
            alert_rule.name = rule_data.name
        if rule_data.threshold_value is not None:
            alert_rule.threshold_value = rule_data.threshold_value
        if rule_data.subnet_id is not None:
            # 验证网段是否存在
            if rule_data.subnet_id:
                subnet = self.db.query(Subnet).filter(Subnet.id == rule_data.subnet_id).first()
                if not subnet:
                    raise HTTPException(status_code=404, detail="指定的网段不存在")
            alert_rule.subnet_id = rule_data.subnet_id
        if rule_data.notification_emails is not None:
            # 验证邮箱格式
            if rule_data.notification_emails:
                try:
                    emails = json.loads(rule_data.notification_emails)
                    if not isinstance(emails, list):
                        raise ValueError("邮箱列表格式错误")
                except (json.JSONDecodeError, ValueError):
                    raise HTTPException(status_code=400, detail="邮箱列表格式错误，应为JSON数组")
            alert_rule.notification_emails = rule_data.notification_emails
        if rule_data.is_active is not None:
            alert_rule.is_active = rule_data.is_active

        self.db.commit()
        self.db.refresh(alert_rule)

        return alert_rule

    def delete_alert_rule(self, rule_id: int) -> bool:
        """
        删除警报规则
        """
        alert_rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not alert_rule:
            raise HTTPException(status_code=404, detail="警报规则不存在")

        self.db.delete(alert_rule)
        self.db.commit()

        return True

    def get_alert_history(
        self,
        skip: int = 0,
        limit: int = 100,
        is_resolved: Optional[bool] = None,
        severity: Optional[str] = None
    ) -> List[AlertHistory]:
        """
        获取警报历史记录
        """
        query = self.db.query(AlertHistory)

        if is_resolved is not None:
            query = query.filter(AlertHistory.is_resolved == is_resolved)
        
        if severity:
            if severity not in [s.value for s in AlertSeverity]:
                raise HTTPException(status_code=400, detail="无效的严重程度")
            query = query.filter(AlertHistory.severity == AlertSeverity(severity))

        return query.order_by(AlertHistory.created_at.desc()).offset(skip).limit(limit).all()

    def resolve_alert(self, alert_id: int, user_id: int) -> AlertHistory:
        """
        解决警报
        """
        alert = self.db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="警报记录不存在")

        if alert.is_resolved:
            raise HTTPException(status_code=400, detail="警报已经被解决")

        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = user_id

        self.db.commit()
        self.db.refresh(alert)

        return alert

    def check_and_create_alerts(self) -> List[AlertHistory]:
        """
        检查并创建警报
        """
        monitoring_service = MonitoringService(self.db)
        alerts_to_create = monitoring_service.check_utilization_alerts()
        
        created_alerts = []
        
        for alert_data in alerts_to_create:
            # 检查是否已经存在相同的未解决警报
            existing_alert = self.db.query(AlertHistory).filter(
                and_(
                    AlertHistory.rule_id == alert_data['rule_id'],
                    AlertHistory.is_resolved == False,
                    AlertHistory.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                )
            ).first()

            if not existing_alert:
                # 创建新的警报记录
                alert_history = monitoring_service.create_alert_history(alert_data)
                created_alerts.append(alert_history)

        return created_alerts

    def get_active_alerts(self) -> List[AlertHistory]:
        """
        获取活跃的警报（未解决的警报）
        """
        return self.db.query(AlertHistory).filter(
            AlertHistory.is_resolved == False
        ).order_by(AlertHistory.created_at.desc()).all()

    def get_alert_summary_by_severity(self) -> Dict[str, int]:
        """
        按严重程度获取警报汇总
        """
        from sqlalchemy import func
        
        severity_counts = self.db.query(
            AlertHistory.severity,
            func.count(AlertHistory.id).label('count')
        ).filter(
            AlertHistory.is_resolved == False
        ).group_by(AlertHistory.severity).all()

        summary = {severity.value: 0 for severity in AlertSeverity}
        for severity, count in severity_counts:
            summary[severity.value] = count

        return summary