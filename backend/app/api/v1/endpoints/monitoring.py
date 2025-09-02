"""
监控和报告相关的API端点
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.monitoring_service import MonitoringService
from app.services.report_service import ReportService
from app.services.alert_service import AlertService
from app.schemas.monitoring import (
    IPUtilizationStats,
    SubnetUtilizationStats,
    AllocationTrend,
    AlertStatistics,
    DashboardSummary,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRuleResponse,
    AlertHistoryResponse,
    ReportRequest,
    ReportResponse
)

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取仪表盘汇总数据
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_dashboard_summary()


@router.get("/ip-utilization", response_model=IPUtilizationStats)
async def get_ip_utilization_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取IP地址使用率统计
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.calculate_ip_utilization_stats()


@router.get("/subnet-utilization", response_model=List[SubnetUtilizationStats])
async def get_subnet_utilization_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取网段使用率统计
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.calculate_subnet_utilization_stats()


@router.get("/allocation-trends", response_model=List[AllocationTrend])
async def get_allocation_trends(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取IP分配趋势数据
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_ip_allocation_trends(days)


@router.get("/top-utilized-subnets", response_model=List[SubnetUtilizationStats])
async def get_top_utilized_subnets(
    limit: int = Query(10, ge=1, le=50, description="返回数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取使用率最高的网段
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_top_utilized_subnets(limit)


@router.get("/alerts/statistics", response_model=AlertStatistics)
async def get_alert_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取警报统计信息
    """
    monitoring_service = MonitoringService(db)
    return monitoring_service.get_alert_statistics()


@router.get("/alerts/rules", response_model=List[AlertRuleResponse])
async def get_alert_rules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取警报规则列表
    """
    alert_service = AlertService(db)
    return alert_service.get_alert_rules(skip=skip, limit=limit, is_active=is_active)


@router.post("/alerts/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建警报规则
    """
    alert_service = AlertService(db)
    return alert_service.create_alert_rule(rule_data, current_user.id)


@router.put("/alerts/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新警报规则
    """
    alert_service = AlertService(db)
    return alert_service.update_alert_rule(rule_id, rule_data)


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除警报规则
    """
    alert_service = AlertService(db)
    alert_service.delete_alert_rule(rule_id)
    return {"message": "警报规则已删除"}


@router.get("/alerts/history", response_model=List[AlertHistoryResponse])
async def get_alert_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_resolved: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取警报历史记录
    """
    alert_service = AlertService(db)
    return alert_service.get_alert_history(
        skip=skip, 
        limit=limit, 
        is_resolved=is_resolved, 
        severity=severity
    )


@router.put("/alerts/history/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    解决警报
    """
    alert_service = AlertService(db)
    alert_service.resolve_alert(alert_id, current_user.id)
    return {"message": "警报已解决"}


@router.post("/alerts/check")
async def check_alerts(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    手动触发警报检查
    """
    alert_service = AlertService(db)
    background_tasks.add_task(alert_service.check_and_create_alerts)
    return {"message": "警报检查已启动"}


@router.post("/reports/generate", response_model=ReportResponse)
async def generate_report(
    report_request: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成报告
    """
    report_service = ReportService(db)
    return report_service.generate_report(report_request, current_user.id, background_tasks)


@router.get("/reports/{report_id}")
async def get_report_status(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取报告生成状态
    """
    report_service = ReportService(db)
    return report_service.get_report_status(report_id)


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    下载报告文件
    """
    report_service = ReportService(db)
    return report_service.download_report(report_id)