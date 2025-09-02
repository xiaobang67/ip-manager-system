"""
安全监控API端点
提供安全事件查询、警报管理和安全仪表盘数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from datetime import datetime

from app.core.security_monitoring import (
    security_monitor, 
    SecurityEventType, 
    SecurityLevel,
    log_security_event
)
from app.core.dependencies import get_current_user, require_admin
from app.models.user import User

router = APIRouter()


class SecurityEventResponse(BaseModel):
    """安全事件响应模型"""
    event_type: str
    level: str
    timestamp: float
    client_ip: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    details: Optional[dict] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None


class SecurityDashboardResponse(BaseModel):
    """安全仪表盘响应模型"""
    total_events_24h: int
    active_alerts: int
    threat_level: str
    event_statistics: dict
    security_levels: dict
    hourly_distribution: dict
    threat_trend: List[dict]
    recent_alerts: List[dict]
    top_threat_ips: List[dict]
    security_score: int


class AlertResponse(BaseModel):
    """警报响应模型"""
    id: str
    title: str
    message: str
    level: str
    timestamp: float
    details: dict
    acknowledged: bool
    acknowledged_at: Optional[float] = None


@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    current_user: User = Depends(require_admin)
):
    """
    获取安全仪表盘数据
    需要管理员权限
    """
    try:
        dashboard_data = security_monitor.get_security_dashboard_data()
        return SecurityDashboardResponse(**dashboard_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全仪表盘数据失败: {str(e)}"
        )


@router.get("/events", response_model=List[SecurityEventResponse])
async def get_security_events(
    limit: int = Query(100, ge=1, le=1000, description="返回事件数量限制"),
    event_type: Optional[str] = Query(None, description="事件类型过滤"),
    level: Optional[str] = Query(None, description="安全级别过滤"),
    start_time: Optional[float] = Query(None, description="开始时间戳"),
    end_time: Optional[float] = Query(None, description="结束时间戳"),
    current_user: User = Depends(require_admin)
):
    """
    获取安全事件列表
    需要管理员权限
    """
    try:
        # 转换枚举类型
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = SecurityEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的事件类型: {event_type}"
                )
        
        level_enum = None
        if level:
            try:
                level_enum = SecurityLevel(level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的安全级别: {level}"
                )
        
        events = security_monitor.get_security_events(
            limit=limit,
            event_type=event_type_enum,
            level=level_enum,
            start_time=start_time,
            end_time=end_time
        )
        
        return [SecurityEventResponse(**event) for event in events]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全事件失败: {str(e)}"
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_security_alerts(
    acknowledged: Optional[bool] = Query(None, description="是否已确认"),
    limit: int = Query(100, ge=1, le=1000, description="返回警报数量限制"),
    current_user: User = Depends(require_admin)
):
    """
    获取安全警报列表
    需要管理员权限
    """
    try:
        alerts = security_monitor.alerts
        
        # 过滤已确认/未确认的警报
        if acknowledged is not None:
            alerts = [
                alert for alert in alerts
                if alert.get('acknowledged', False) == acknowledged
            ]
        
        # 按时间倒序排列
        alerts = sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
        
        # 限制数量
        alerts = alerts[:limit]
        
        return [AlertResponse(**alert) for alert in alerts]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全警报失败: {str(e)}"
        )


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(require_admin)
):
    """
    确认安全警报
    需要管理员权限
    """
    try:
        success = security_monitor.acknowledge_alert(alert_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"警报不存在: {alert_id}"
            )
        
        # 记录确认操作
        log_security_event(
            event_type=SecurityEventType.ADMIN_ACTION,
            level=SecurityLevel.LOW,
            client_ip="127.0.0.1",  # 这里应该从请求中获取真实IP
            user_id=current_user.id,
            username=current_user.username,
            details={
                "action": "acknowledge_alert",
                "alert_id": alert_id
            }
        )
        
        return {"message": "警报已确认", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"确认警报失败: {str(e)}"
        )


@router.get("/statistics")
async def get_security_statistics(
    period: str = Query("24h", description="统计周期: 1h, 24h, 7d, 30d"),
    current_user: User = Depends(require_admin)
):
    """
    获取安全统计信息
    需要管理员权限
    """
    try:
        import time
        
        # 计算时间范围
        current_time = time.time()
        period_seconds = {
            "1h": 3600,
            "24h": 86400,
            "7d": 604800,
            "30d": 2592000
        }
        
        if period not in period_seconds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的统计周期: {period}"
            )
        
        start_time = current_time - period_seconds[period]
        
        # 获取指定时间范围内的事件
        events = security_monitor.get_security_events(
            limit=10000,  # 获取足够多的事件用于统计
            start_time=start_time,
            end_time=current_time
        )
        
        # 统计分析
        from collections import defaultdict
        
        event_counts = defaultdict(int)
        level_counts = defaultdict(int)
        ip_counts = defaultdict(int)
        hourly_counts = defaultdict(int)
        
        for event in events:
            event_counts[event['event_type']] += 1
            level_counts[event['level']] += 1
            ip_counts[event['client_ip']] += 1
            
            # 按小时统计
            event_time = event['timestamp']
            hour_key = int((current_time - event_time) // 3600)
            hourly_counts[hour_key] += 1
        
        # 获取前10个最活跃的IP
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "period": period,
            "start_time": start_time,
            "end_time": current_time,
            "total_events": len(events),
            "event_types": dict(event_counts),
            "security_levels": dict(level_counts),
            "hourly_distribution": dict(hourly_counts),
            "top_active_ips": [{"ip": ip, "count": count} for ip, count in top_ips],
            "threat_score": security_monitor._calculate_security_score()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全统计失败: {str(e)}"
        )


@router.get("/threat-analysis")
async def get_threat_analysis(
    current_user: User = Depends(require_admin)
):
    """
    获取威胁分析报告
    需要管理员权限
    """
    try:
        import time
        from collections import defaultdict
        
        current_time = time.time()
        
        # 获取最近24小时的高危事件
        high_threat_events = security_monitor.get_security_events(
            limit=1000,
            level=SecurityLevel.HIGH,
            start_time=current_time - 86400
        )
        
        critical_threat_events = security_monitor.get_security_events(
            limit=1000,
            level=SecurityLevel.CRITICAL,
            start_time=current_time - 86400
        )
        
        # 威胁模式分析
        threat_patterns = defaultdict(int)
        threat_ips = defaultdict(int)
        threat_timeline = []
        
        all_threats = high_threat_events + critical_threat_events
        
        for event in all_threats:
            threat_patterns[event['event_type']] += 1
            threat_ips[event['client_ip']] += 1
            
            threat_timeline.append({
                "timestamp": event['timestamp'],
                "type": event['event_type'],
                "level": event['level'],
                "ip": event['client_ip']
            })
        
        # 按时间排序
        threat_timeline.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # 威胁趋势分析
        threat_trend = []
        for i in range(24):  # 最近24小时
            hour_start = current_time - (i + 1) * 3600
            hour_end = current_time - i * 3600
            
            hour_threats = [
                event for event in all_threats
                if hour_start <= event['timestamp'] < hour_end
            ]
            
            threat_trend.append({
                "hour": 23 - i,  # 0-23小时前
                "count": len(hour_threats),
                "high_count": len([e for e in hour_threats if e['level'] == 'high']),
                "critical_count": len([e for e in hour_threats if e['level'] == 'critical'])
            })
        
        # 威胁建议
        recommendations = []
        
        if threat_patterns.get('login_failed', 0) > 10:
            recommendations.append("检测到大量登录失败，建议启用账户锁定机制")
        
        if threat_patterns.get('sql_injection_attempt', 0) > 0:
            recommendations.append("检测到SQL注入尝试，建议加强输入验证")
        
        if threat_patterns.get('xss_attempt', 0) > 0:
            recommendations.append("检测到XSS攻击尝试，建议启用内容安全策略")
        
        if len(threat_ips) > 5:
            recommendations.append("检测到多个可疑IP，建议考虑IP黑名单机制")
        
        return {
            "analysis_time": current_time,
            "period": "24h",
            "total_threats": len(all_threats),
            "high_threats": len(high_threat_events),
            "critical_threats": len(critical_threat_events),
            "threat_patterns": dict(threat_patterns),
            "top_threat_ips": [
                {"ip": ip, "count": count}
                for ip, count in sorted(threat_ips.items(), key=lambda x: x[1], reverse=True)[:10]
            ],
            "threat_timeline": threat_timeline[:50],  # 最近50个威胁事件
            "threat_trend": threat_trend,
            "recommendations": recommendations,
            "current_threat_level": security_monitor._calculate_threat_level()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取威胁分析失败: {str(e)}"
        )


@router.post("/test-security")
async def test_security_event(
    event_type: str,
    level: str = "medium",
    details: Optional[dict] = None,
    current_user: User = Depends(require_admin)
):
    """
    测试安全事件记录（仅用于测试）
    需要管理员权限
    """
    try:
        # 验证事件类型和级别
        try:
            event_type_enum = SecurityEventType(event_type)
            level_enum = SecurityLevel(level)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无效的参数: {str(e)}"
            )
        
        # 记录测试事件
        log_security_event(
            event_type=event_type_enum,
            level=level_enum,
            client_ip="127.0.0.1",
            user_id=current_user.id,
            username=current_user.username,
            details=details or {"test": True}
        )
        
        return {
            "message": "测试安全事件已记录",
            "event_type": event_type,
            "level": level
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"记录测试事件失败: {str(e)}"
        )