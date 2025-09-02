"""
监控服务 - 提供IP地址使用率统计和监控数据计算
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.ip_address import IPAddress, IPStatus
from app.models.subnet import Subnet
from app.models.alert import AlertRule, AlertHistory, RuleType, AlertSeverity
from app.models.user import User
import ipaddress
import json


class MonitoringService:
    def __init__(self, db: Session):
        self.db = db

    def calculate_ip_utilization_stats(self) -> Dict[str, Any]:
        """
        计算IP地址使用率统计
        """
        # 总体统计
        total_ips = self.db.query(IPAddress).count()
        allocated_ips = self.db.query(IPAddress).filter(
            IPAddress.status == IPStatus.ALLOCATED
        ).count()
        reserved_ips = self.db.query(IPAddress).filter(
            IPAddress.status == IPStatus.RESERVED
        ).count()
        available_ips = self.db.query(IPAddress).filter(
            IPAddress.status == IPStatus.AVAILABLE
        ).count()
        conflict_ips = self.db.query(IPAddress).filter(
            IPAddress.status == IPStatus.CONFLICT
        ).count()

        # 计算使用率
        utilization_rate = (allocated_ips + reserved_ips) / total_ips * 100 if total_ips > 0 else 0

        return {
            "total_ips": total_ips,
            "allocated_ips": allocated_ips,
            "reserved_ips": reserved_ips,
            "available_ips": available_ips,
            "conflict_ips": conflict_ips,
            "utilization_rate": round(utilization_rate, 2),
            "allocation_rate": round(allocated_ips / total_ips * 100, 2) if total_ips > 0 else 0,
            "reservation_rate": round(reserved_ips / total_ips * 100, 2) if total_ips > 0 else 0
        }

    def calculate_subnet_utilization_stats(self) -> List[Dict[str, Any]]:
        """
        计算每个网段的使用率统计
        """
        subnets = self.db.query(Subnet).all()
        subnet_stats = []

        for subnet in subnets:
            # 计算网段总IP数量
            network = ipaddress.ip_network(subnet.network, strict=False)
            total_ips_in_subnet = network.num_addresses - 2  # 排除网络地址和广播地址

            # 查询该网段的IP统计
            ip_stats = self.db.query(
                IPAddress.status,
                func.count(IPAddress.id).label('count')
            ).filter(
                IPAddress.subnet_id == subnet.id
            ).group_by(IPAddress.status).all()

            # 转换为字典
            status_counts = {status.value: 0 for status in IPStatus}
            for status, count in ip_stats:
                status_counts[status.value] = count

            # 计算使用率
            used_ips = status_counts['allocated'] + status_counts['reserved']
            utilization_rate = used_ips / total_ips_in_subnet * 100 if total_ips_in_subnet > 0 else 0

            subnet_stats.append({
                "subnet_id": subnet.id,
                "network": subnet.network,
                "description": subnet.description,
                "vlan_id": subnet.vlan_id,
                "location": subnet.location,
                "total_ips": total_ips_in_subnet,
                "allocated_ips": status_counts['allocated'],
                "reserved_ips": status_counts['reserved'],
                "available_ips": status_counts['available'],
                "conflict_ips": status_counts['conflict'],
                "utilization_rate": round(utilization_rate, 2),
                "created_at": subnet.created_at
            })

        return subnet_stats

    def get_ip_allocation_trends(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        获取IP分配趋势数据
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 按天统计IP分配数量
        daily_allocations = self.db.query(
            func.date(IPAddress.allocated_at).label('date'),
            func.count(IPAddress.id).label('count')
        ).filter(
            and_(
                IPAddress.allocated_at >= start_date,
                IPAddress.allocated_at <= end_date,
                IPAddress.status == IPStatus.ALLOCATED
            )
        ).group_by(func.date(IPAddress.allocated_at)).all()

        # 填充缺失的日期
        trends = []
        current_date = start_date.date()
        allocation_dict = {date: count for date, count in daily_allocations}

        while current_date <= end_date.date():
            trends.append({
                "date": current_date.isoformat(),
                "allocations": allocation_dict.get(current_date, 0)
            })
            current_date += timedelta(days=1)

        return trends

    def get_top_utilized_subnets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取使用率最高的网段
        """
        subnet_stats = self.calculate_subnet_utilization_stats()
        # 按使用率排序
        sorted_subnets = sorted(subnet_stats, key=lambda x: x['utilization_rate'], reverse=True)
        return sorted_subnets[:limit]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """
        获取警报统计信息
        """
        # 活跃警报规则数量
        active_rules = self.db.query(AlertRule).filter(AlertRule.is_active == True).count()
        
        # 最近30天的警报数量
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_alerts = self.db.query(AlertHistory).filter(
            AlertHistory.created_at >= thirty_days_ago
        ).count()

        # 未解决的警报数量
        unresolved_alerts = self.db.query(AlertHistory).filter(
            AlertHistory.is_resolved == False
        ).count()

        # 按严重程度统计警报
        severity_stats = self.db.query(
            AlertHistory.severity,
            func.count(AlertHistory.id).label('count')
        ).filter(
            AlertHistory.created_at >= thirty_days_ago
        ).group_by(AlertHistory.severity).all()

        severity_counts = {severity.value: 0 for severity in AlertSeverity}
        for severity, count in severity_stats:
            severity_counts[severity.value] = count

        return {
            "active_rules": active_rules,
            "recent_alerts": recent_alerts,
            "unresolved_alerts": unresolved_alerts,
            "severity_breakdown": severity_counts
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        获取仪表盘汇总数据
        """
        ip_stats = self.calculate_ip_utilization_stats()
        alert_stats = self.get_alert_statistics()
        
        # 网段统计
        total_subnets = self.db.query(Subnet).count()
        
        # 用户统计
        total_users = self.db.query(User).count()
        
        # 最近活动
        recent_allocations = self.db.query(IPAddress).filter(
            and_(
                IPAddress.allocated_at >= datetime.utcnow() - timedelta(hours=24),
                IPAddress.status == IPStatus.ALLOCATED
            )
        ).count()

        return {
            "ip_statistics": ip_stats,
            "alert_statistics": alert_stats,
            "total_subnets": total_subnets,
            "total_users": total_users,
            "recent_allocations_24h": recent_allocations,
            "timestamp": datetime.utcnow().isoformat()
        }

    def check_utilization_alerts(self) -> List[Dict[str, Any]]:
        """
        检查使用率警报
        """
        alerts = []
        
        # 获取所有活跃的使用率警报规则
        utilization_rules = self.db.query(AlertRule).filter(
            and_(
                AlertRule.rule_type == RuleType.UTILIZATION,
                AlertRule.is_active == True
            )
        ).all()

        for rule in utilization_rules:
            if rule.subnet_id:
                # 特定网段的使用率检查
                subnet_stats = self.calculate_subnet_utilization_stats()
                subnet_stat = next((s for s in subnet_stats if s['subnet_id'] == rule.subnet_id), None)
                
                if subnet_stat and subnet_stat['utilization_rate'] >= float(rule.threshold_value):
                    alerts.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "subnet_id": rule.subnet_id,
                        "network": subnet_stat['network'],
                        "current_utilization": subnet_stat['utilization_rate'],
                        "threshold": float(rule.threshold_value),
                        "severity": AlertSeverity.HIGH if subnet_stat['utilization_rate'] >= 90 else AlertSeverity.MEDIUM,
                        "message": f"网段 {subnet_stat['network']} 使用率达到 {subnet_stat['utilization_rate']}%，超过阈值 {rule.threshold_value}%"
                    })
            else:
                # 全局使用率检查
                ip_stats = self.calculate_ip_utilization_stats()
                
                if ip_stats['utilization_rate'] >= float(rule.threshold_value):
                    alerts.append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "subnet_id": None,
                        "network": "全局",
                        "current_utilization": ip_stats['utilization_rate'],
                        "threshold": float(rule.threshold_value),
                        "severity": AlertSeverity.CRITICAL if ip_stats['utilization_rate'] >= 95 else AlertSeverity.HIGH,
                        "message": f"全局IP使用率达到 {ip_stats['utilization_rate']}%，超过阈值 {rule.threshold_value}%"
                    })

        return alerts

    def create_alert_history(self, alert_data: Dict[str, Any]) -> AlertHistory:
        """
        创建警报历史记录
        """
        alert_history = AlertHistory(
            rule_id=alert_data['rule_id'],
            alert_message=alert_data['message'],
            severity=alert_data['severity']
        )
        
        self.db.add(alert_history)
        self.db.commit()
        self.db.refresh(alert_history)
        
        return alert_history