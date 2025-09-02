"""
安全监控和日志记录模块
提供实时安全监控、威胁检测和安全事件记录功能
"""
import time
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import threading

logger = logging.getLogger(__name__)


class SecurityEventType(Enum):
    """安全事件类型"""
    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    CSRF_VIOLATION = "csrf_violation"
    INVALID_TOKEN = "invalid_token"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALICIOUS_FILE_UPLOAD = "malicious_file_upload"
    BRUTE_FORCE_ATTACK = "brute_force_attack"
    ACCOUNT_LOCKED = "account_locked"
    PASSWORD_CHANGED = "password_changed"
    ADMIN_ACTION = "admin_action"


class SecurityLevel(Enum):
    """安全级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """安全事件数据类"""
    event_type: SecurityEventType
    level: SecurityLevel
    timestamp: float
    client_ip: str
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        data['level'] = self.level.value
        return data
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class SecurityMonitor:
    """安全监控器"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self.events = deque(maxlen=max_events)
        self.event_counts = defaultdict(int)
        self.ip_activity = defaultdict(list)
        self.user_activity = defaultdict(list)
        self.threat_patterns = defaultdict(int)
        self.alerts = []
        self.lock = threading.Lock()
        
        # 配置安全日志记录器
        self.security_logger = self._setup_security_logger()
        
        # 启动监控任务
        self._start_monitoring_tasks()
    
    def _setup_security_logger(self) -> logging.Logger:
        """设置安全日志记录器"""
        security_logger = logging.getLogger("security_monitor")
        security_logger.setLevel(logging.INFO)
        
        # 创建文件处理器
        handler = logging.FileHandler("logs/security_events.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        security_logger.addHandler(handler)
        
        return security_logger
    
    def _start_monitoring_tasks(self):
        """启动监控任务"""
        # 启动清理任务
        cleanup_thread = threading.Thread(target=self._cleanup_old_data, daemon=True)
        cleanup_thread.start()
        
        # 启动威胁分析任务
        analysis_thread = threading.Thread(target=self._analyze_threats, daemon=True)
        analysis_thread.start()
    
    def record_event(self, event: SecurityEvent):
        """记录安全事件"""
        with self.lock:
            # 添加事件到队列
            self.events.append(event)
            
            # 更新统计信息
            self.event_counts[event.event_type] += 1
            
            # 记录IP活动
            self.ip_activity[event.client_ip].append(event.timestamp)
            
            # 记录用户活动
            if event.user_id:
                self.user_activity[event.user_id].append(event.timestamp)
            
            # 记录威胁模式
            if event.level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                self.threat_patterns[event.event_type] += 1
        
        # 记录到日志文件
        self.security_logger.info(event.to_json())
        
        # 实时威胁检测
        self._detect_real_time_threats(event)
        
        # 触发警报检查
        self._check_alert_conditions(event)
    
    def _detect_real_time_threats(self, event: SecurityEvent):
        """实时威胁检测"""
        current_time = time.time()
        
        # 检测暴力破解攻击
        if event.event_type == SecurityEventType.LOGIN_FAILED:
            recent_failures = [
                t for t in self.ip_activity[event.client_ip]
                if current_time - t < 300  # 5分钟内
            ]
            
            if len(recent_failures) >= 5:
                self._trigger_alert(
                    "暴力破解攻击检测",
                    f"IP {event.client_ip} 在5分钟内尝试登录失败{len(recent_failures)}次",
                    SecurityLevel.HIGH,
                    {"ip": event.client_ip, "attempts": len(recent_failures)}
                )
        
        # 检测异常活动模式
        if event.user_id:
            user_events = [
                t for t in self.user_activity[event.user_id]
                if current_time - t < 3600  # 1小时内
            ]
            
            if len(user_events) >= 100:  # 1小时内超过100次活动
                self._trigger_alert(
                    "异常用户活动",
                    f"用户 {event.username or event.user_id} 在1小时内活动{len(user_events)}次",
                    SecurityLevel.MEDIUM,
                    {"user_id": event.user_id, "activity_count": len(user_events)}
                )
    
    def _check_alert_conditions(self, event: SecurityEvent):
        """检查警报条件"""
        # 高危事件立即警报
        if event.level == SecurityLevel.CRITICAL:
            self._trigger_alert(
                "严重安全事件",
                f"检测到严重安全事件: {event.event_type.value}",
                SecurityLevel.CRITICAL,
                event.details or {}
            )
        
        # 检查特定事件类型的阈值
        alert_thresholds = {
            SecurityEventType.SQL_INJECTION_ATTEMPT: 3,
            SecurityEventType.XSS_ATTEMPT: 5,
            SecurityEventType.PERMISSION_DENIED: 10,
            SecurityEventType.RATE_LIMIT_EXCEEDED: 20
        }
        
        if event.event_type in alert_thresholds:
            threshold = alert_thresholds[event.event_type]
            recent_count = self._count_recent_events(event.event_type, 3600)  # 1小时内
            
            if recent_count >= threshold:
                self._trigger_alert(
                    f"{event.event_type.value}事件频发",
                    f"1小时内检测到{recent_count}次{event.event_type.value}事件",
                    SecurityLevel.HIGH,
                    {"event_type": event.event_type.value, "count": recent_count}
                )
    
    def _count_recent_events(self, event_type: SecurityEventType, time_window: int) -> int:
        """统计最近时间窗口内的事件数量"""
        current_time = time.time()
        count = 0
        
        for event in self.events:
            if (event.event_type == event_type and 
                current_time - event.timestamp < time_window):
                count += 1
        
        return count
    
    def _trigger_alert(self, title: str, message: str, level: SecurityLevel, details: Dict[str, Any]):
        """触发安全警报"""
        alert = {
            "id": hashlib.md5(f"{title}{message}{time.time()}".encode()).hexdigest()[:8],
            "title": title,
            "message": message,
            "level": level.value,
            "timestamp": time.time(),
            "details": details,
            "acknowledged": False
        }
        
        self.alerts.append(alert)
        
        # 记录警报日志
        self.security_logger.warning(f"ALERT: {title} - {message}")
        
        # 发送通知（这里可以集成邮件、短信等通知方式）
        self._send_alert_notification(alert)
    
    def _send_alert_notification(self, alert: Dict[str, Any]):
        """发送警报通知"""
        # 这里可以实现具体的通知逻辑
        # 例如：发送邮件、短信、Slack消息等
        logger.warning(f"Security Alert: {alert['title']} - {alert['message']}")
    
    def _cleanup_old_data(self):
        """清理旧数据"""
        while True:
            try:
                current_time = time.time()
                cutoff_time = current_time - 86400  # 24小时前
                
                with self.lock:
                    # 清理IP活动记录
                    for ip in list(self.ip_activity.keys()):
                        self.ip_activity[ip] = [
                            t for t in self.ip_activity[ip] if t > cutoff_time
                        ]
                        if not self.ip_activity[ip]:
                            del self.ip_activity[ip]
                    
                    # 清理用户活动记录
                    for user_id in list(self.user_activity.keys()):
                        self.user_activity[user_id] = [
                            t for t in self.user_activity[user_id] if t > cutoff_time
                        ]
                        if not self.user_activity[user_id]:
                            del self.user_activity[user_id]
                    
                    # 清理旧警报
                    self.alerts = [
                        alert for alert in self.alerts
                        if current_time - alert['timestamp'] < 604800  # 7天
                    ]
                
                time.sleep(3600)  # 每小时清理一次
                
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                time.sleep(60)
    
    def _analyze_threats(self):
        """威胁分析任务"""
        while True:
            try:
                # 分析威胁模式
                self._analyze_threat_patterns()
                
                # 生成安全报告
                self._generate_security_report()
                
                time.sleep(1800)  # 每30分钟分析一次
                
            except Exception as e:
                logger.error(f"Error in threat analysis task: {e}")
                time.sleep(300)
    
    def _analyze_threat_patterns(self):
        """分析威胁模式"""
        current_time = time.time()
        
        # 分析最近1小时的事件
        recent_events = [
            event for event in self.events
            if current_time - event.timestamp < 3600
        ]
        
        if not recent_events:
            return
        
        # 按IP分组分析
        ip_events = defaultdict(list)
        for event in recent_events:
            ip_events[event.client_ip].append(event)
        
        # 检测可疑IP
        for ip, events in ip_events.items():
            if len(events) >= 50:  # 1小时内超过50次活动
                event_types = [event.event_type for event in events]
                unique_types = set(event_types)
                
                if len(unique_types) >= 5:  # 涉及多种事件类型
                    self._trigger_alert(
                        "可疑IP活动",
                        f"IP {ip} 在1小时内产生{len(events)}次活动，涉及{len(unique_types)}种事件类型",
                        SecurityLevel.HIGH,
                        {"ip": ip, "event_count": len(events), "event_types": list(unique_types)}
                    )
    
    def _generate_security_report(self):
        """生成安全报告"""
        current_time = time.time()
        
        # 统计最近24小时的事件
        recent_events = [
            event for event in self.events
            if current_time - event.timestamp < 86400
        ]
        
        if not recent_events:
            return
        
        # 生成统计信息
        event_stats = defaultdict(int)
        level_stats = defaultdict(int)
        ip_stats = defaultdict(int)
        
        for event in recent_events:
            event_stats[event.event_type.value] += 1
            level_stats[event.level.value] += 1
            ip_stats[event.client_ip] += 1
        
        # 记录报告
        report = {
            "timestamp": current_time,
            "period": "24_hours",
            "total_events": len(recent_events),
            "event_types": dict(event_stats),
            "security_levels": dict(level_stats),
            "top_ips": dict(sorted(ip_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
            "active_alerts": len([a for a in self.alerts if not a.get('acknowledged', False)])
        }
        
        self.security_logger.info(f"SECURITY_REPORT: {json.dumps(report, ensure_ascii=False)}")
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """获取安全仪表盘数据"""
        current_time = time.time()
        
        # 最近24小时的事件
        recent_events = [
            event for event in self.events
            if current_time - event.timestamp < 86400
        ]
        
        # 统计数据
        event_stats = defaultdict(int)
        level_stats = defaultdict(int)
        hourly_stats = defaultdict(int)
        
        for event in recent_events:
            event_stats[event.event_type.value] += 1
            level_stats[event.level.value] += 1
            
            # 按小时统计
            hour = int((current_time - event.timestamp) // 3600)
            hourly_stats[hour] += 1
        
        # 活跃警报
        active_alerts = [
            alert for alert in self.alerts
            if not alert.get('acknowledged', False)
        ]
        
        # 威胁趋势
        threat_trend = []
        for i in range(24):  # 最近24小时
            hour_start = current_time - (i + 1) * 3600
            hour_end = current_time - i * 3600
            
            hour_events = [
                event for event in self.events
                if hour_start <= event.timestamp < hour_end and
                event.level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            ]
            
            threat_trend.append({
                "hour": i,
                "threats": len(hour_events)
            })
        
        return {
            "total_events_24h": len(recent_events),
            "active_alerts": len(active_alerts),
            "threat_level": self._calculate_threat_level(),
            "event_statistics": dict(event_stats),
            "security_levels": dict(level_stats),
            "hourly_distribution": dict(hourly_stats),
            "threat_trend": threat_trend,
            "recent_alerts": active_alerts[-10:],  # 最近10个警报
            "top_threat_ips": self._get_top_threat_ips(),
            "security_score": self._calculate_security_score()
        }
    
    def _calculate_threat_level(self) -> str:
        """计算当前威胁级别"""
        current_time = time.time()
        
        # 最近1小时的高危事件
        recent_high_threats = [
            event for event in self.events
            if (current_time - event.timestamp < 3600 and
                event.level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL])
        ]
        
        if len(recent_high_threats) >= 10:
            return "CRITICAL"
        elif len(recent_high_threats) >= 5:
            return "HIGH"
        elif len(recent_high_threats) >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_top_threat_ips(self) -> List[Dict[str, Any]]:
        """获取威胁IP排行"""
        current_time = time.time()
        
        # 最近24小时的威胁事件
        threat_events = [
            event for event in self.events
            if (current_time - event.timestamp < 86400 and
                event.level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL])
        ]
        
        ip_threats = defaultdict(int)
        for event in threat_events:
            ip_threats[event.client_ip] += 1
        
        # 排序并返回前10个
        top_ips = sorted(ip_threats.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [
            {"ip": ip, "threat_count": count}
            for ip, count in top_ips
        ]
    
    def _calculate_security_score(self) -> int:
        """计算安全评分（0-100）"""
        current_time = time.time()
        
        # 基础分数
        score = 100
        
        # 最近24小时的事件
        recent_events = [
            event for event in self.events
            if current_time - event.timestamp < 86400
        ]
        
        # 根据事件级别扣分
        for event in recent_events:
            if event.level == SecurityLevel.CRITICAL:
                score -= 10
            elif event.level == SecurityLevel.HIGH:
                score -= 5
            elif event.level == SecurityLevel.MEDIUM:
                score -= 2
            elif event.level == SecurityLevel.LOW:
                score -= 1
        
        # 活跃警报扣分
        active_alerts = [
            alert for alert in self.alerts
            if not alert.get('acknowledged', False)
        ]
        score -= len(active_alerts) * 3
        
        return max(0, min(100, score))
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认警报"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = time.time()
                return True
        return False
    
    def get_security_events(self, 
                          limit: int = 100, 
                          event_type: Optional[SecurityEventType] = None,
                          level: Optional[SecurityLevel] = None,
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """获取安全事件列表"""
        events = list(self.events)
        
        # 过滤条件
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if level:
            events = [e for e in events if e.level == level]
        
        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        
        # 按时间倒序排列
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 限制数量
        events = events[:limit]
        
        return [event.to_dict() for event in events]


# 全局安全监控器实例
security_monitor = SecurityMonitor()


def log_security_event(event_type: SecurityEventType,
                      level: SecurityLevel,
                      client_ip: str,
                      user_id: Optional[int] = None,
                      username: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      endpoint: Optional[str] = None,
                      method: Optional[str] = None,
                      details: Optional[Dict[str, Any]] = None,
                      session_id: Optional[str] = None,
                      request_id: Optional[str] = None):
    """记录安全事件的便捷函数"""
    event = SecurityEvent(
        event_type=event_type,
        level=level,
        timestamp=time.time(),
        client_ip=client_ip,
        user_id=user_id,
        username=username,
        user_agent=user_agent,
        endpoint=endpoint,
        method=method,
        details=details,
        session_id=session_id,
        request_id=request_id
    )
    
    security_monitor.record_event(event)