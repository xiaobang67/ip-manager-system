"""
监控和报告相关的API端点
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.ip_address import IPAddress
from app.models.subnet import Subnet
from app.schemas.monitoring import (
    DashboardSummary,
    IPUtilizationStats,
    SubnetUtilizationStats,
    AllocationTrend,
    TopSubnet
)

router = APIRouter()

@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取仪表盘汇总数据"""
    
    # IP地址统计
    total_ips = db.query(IPAddress).count()
    allocated_ips = db.query(IPAddress).filter(IPAddress.status == "allocated").count()
    reserved_ips = db.query(IPAddress).filter(IPAddress.status == "reserved").count()
    available_ips = db.query(IPAddress).filter(IPAddress.status == "available").count()
    conflict_ips = db.query(IPAddress).filter(IPAddress.status == "conflict").count()
    
    utilization_rate = round((allocated_ips / total_ips * 100) if total_ips > 0 else 0, 2)
    
    # 网段统计
    total_subnets = db.query(Subnet).count()
    
    # 警报统计（模拟数据，因为警报功能已删除）
    unresolved_alerts = 0
    
    return DashboardSummary(
        ip_statistics={
            "total_ips": total_ips,
            "allocated_ips": allocated_ips,
            "reserved_ips": reserved_ips,
            "available_ips": available_ips,
            "conflict_ips": conflict_ips,
            "utilization_rate": utilization_rate
        },
        total_subnets=total_subnets,
        alert_statistics={
            "unresolved_alerts": unresolved_alerts
        }
    )

@router.get("/ip-utilization", response_model=IPUtilizationStats)
async def get_ip_utilization_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP使用率统计"""
    
    stats = db.query(
        IPAddress.status,
        func.count(IPAddress.id).label('count')
    ).group_by(IPAddress.status).all()
    
    result = {
        "allocated": 0,
        "reserved": 0,
        "available": 0,
        "conflict": 0
    }
    
    for stat in stats:
        if stat.status in result:
            result[stat.status] = stat.count
    
    return IPUtilizationStats(**result)

@router.get("/subnet-utilization", response_model=List[SubnetUtilizationStats])
async def get_subnet_utilization_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取网段使用率统计"""
    
    subnets = db.query(Subnet).all()
    result = []
    
    for subnet in subnets:
        total_ips = db.query(IPAddress).filter(IPAddress.subnet_id == subnet.id).count()
        allocated_ips = db.query(IPAddress).filter(
            IPAddress.subnet_id == subnet.id,
            IPAddress.status == "allocated"
        ).count()
        
        utilization_rate = round((allocated_ips / total_ips * 100) if total_ips > 0 else 0, 2)
        
        result.append(SubnetUtilizationStats(
            subnet_id=subnet.id,
            network=subnet.network,
            description=subnet.description,
            total_ips=total_ips,
            allocated_ips=allocated_ips,
            utilization_rate=utilization_rate
        ))
    
    return result

@router.get("/allocation-trends", response_model=List[AllocationTrend])
async def get_allocation_trends(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取IP分配趋势"""
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # 查询指定时间范围内的分配记录
    trends = db.query(
        func.date(IPAddress.allocated_at).label('date'),
        func.count(IPAddress.id).label('allocations')
    ).filter(
        IPAddress.allocated_at >= start_date,
        IPAddress.allocated_at <= end_date,
        IPAddress.status == "allocated"
    ).group_by(
        func.date(IPAddress.allocated_at)
    ).order_by(
        func.date(IPAddress.allocated_at)
    ).all()
    
    # 填充缺失的日期
    result = []
    current_date = start_date
    trend_dict = {trend.date: trend.allocations for trend in trends}
    
    while current_date <= end_date:
        result.append(AllocationTrend(
            date=current_date.isoformat(),
            allocations=trend_dict.get(current_date, 0)
        ))
        current_date += timedelta(days=1)
    
    return result

@router.get("/top-utilized-subnets", response_model=List[TopSubnet])
async def get_top_utilized_subnets(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取使用率最高的网段"""
    
    subnets = db.query(Subnet).all()
    subnet_stats = []
    
    for subnet in subnets:
        total_ips = db.query(IPAddress).filter(IPAddress.subnet_id == subnet.id).count()
        allocated_ips = db.query(IPAddress).filter(
            IPAddress.subnet_id == subnet.id,
            IPAddress.status == "allocated"
        ).count()
        
        utilization_rate = round((allocated_ips / total_ips * 100) if total_ips > 0 else 0, 2)
        
        subnet_stats.append(TopSubnet(
            network=subnet.network,
            description=subnet.description,
            vlan_id=subnet.vlan_id,
            location=subnet.location,
            total_ips=total_ips,
            allocated_ips=allocated_ips,
            utilization_rate=utilization_rate
        ))
    
    # 按使用率排序并返回前N个
    subnet_stats.sort(key=lambda x: x.utilization_rate, reverse=True)
    return subnet_stats[:limit]

