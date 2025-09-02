"""
数据库健康检查和监控模块
提供数据库连接状态检查、性能监控和故障诊断功能
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from dataclasses import dataclass

from app.core.database import engine, SessionLocal, check_database_connection

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ConnectionPoolStats:
    """连接池统计信息"""
    pool_size: int
    checked_in: int
    checked_out: int
    overflow: int
    invalid: int
    total_connections: int
    utilization_percent: float


class DatabaseHealthChecker:
    """数据库健康检查器"""
    
    def __init__(self):
        self.last_check_time: Optional[datetime] = None
        self.last_result: Optional[HealthCheckResult] = None
        self.check_history: List[HealthCheckResult] = []
        self.max_history_size = 100
    
    def perform_health_check(self) -> HealthCheckResult:
        """
        执行完整的数据库健康检查
        
        Returns:
            HealthCheckResult: 健康检查结果
        """
        start_time = time.time()
        timestamp = datetime.utcnow()
        
        try:
            # 基本连接检查
            connection_ok = self._check_basic_connection()
            if not connection_ok:
                return HealthCheckResult(
                    status="unhealthy",
                    timestamp=timestamp,
                    response_time_ms=(time.time() - start_time) * 1000,
                    details={},
                    error="Database connection failed"
                )
            
            # 获取连接池统计
            pool_stats = self._get_connection_pool_stats()
            
            # 执行性能测试
            performance_metrics = self._check_performance()
            
            # 检查表状态
            table_status = self._check_table_status()
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # 判断整体健康状态
            status = self._determine_health_status(
                pool_stats, performance_metrics, response_time_ms
            )
            
            result = HealthCheckResult(
                status=status,
                timestamp=timestamp,
                response_time_ms=response_time_ms,
                details={
                    "connection_pool": pool_stats.__dict__,
                    "performance": performance_metrics,
                    "tables": table_status,
                    "database_info": self._get_database_info()
                }
            )
            
            # 更新检查历史
            self._update_history(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            result = HealthCheckResult(
                status="unhealthy",
                timestamp=timestamp,
                response_time_ms=(time.time() - start_time) * 1000,
                details={},
                error=str(e)
            )
            self._update_history(result)
            return result
    
    def _check_basic_connection(self) -> bool:
        """检查基本数据库连接"""
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
                return True
        except Exception as e:
            logger.error(f"Basic connection check failed: {e}")
            return False
    
    def _get_connection_pool_stats(self) -> ConnectionPoolStats:
        """获取连接池统计信息"""
        try:
            pool = engine.pool
            pool_size = pool.size()
            checked_in = pool.checkedin()
            checked_out = pool.checkedout()
            overflow = pool.overflow()
            invalid = pool.invalid()
            total_connections = checked_in + checked_out
            
            utilization_percent = (
                (checked_out / (pool_size + overflow)) * 100 
                if (pool_size + overflow) > 0 else 0
            )
            
            return ConnectionPoolStats(
                pool_size=pool_size,
                checked_in=checked_in,
                checked_out=checked_out,
                overflow=overflow,
                invalid=invalid,
                total_connections=total_connections,
                utilization_percent=round(utilization_percent, 2)
            )
        except Exception as e:
            logger.error(f"Failed to get connection pool stats: {e}")
            return ConnectionPoolStats(0, 0, 0, 0, 0, 0, 0.0)
    
    def _check_performance(self) -> Dict[str, Any]:
        """检查数据库性能指标"""
        metrics = {}
        
        try:
            with engine.connect() as connection:
                # 测试简单查询响应时间
                start_time = time.time()
                connection.execute(text("SELECT 1"))
                simple_query_time = (time.time() - start_time) * 1000
                metrics["simple_query_ms"] = round(simple_query_time, 2)
                
                # 测试表计数查询（如果表存在）
                try:
                    start_time = time.time()
                    result = connection.execute(text("SELECT COUNT(*) FROM users"))
                    result.fetchone()
                    count_query_time = (time.time() - start_time) * 1000
                    metrics["count_query_ms"] = round(count_query_time, 2)
                except:
                    metrics["count_query_ms"] = None
                
                # 获取数据库状态变量
                try:
                    result = connection.execute(text("SHOW STATUS LIKE 'Threads_connected'"))
                    row = result.fetchone()
                    if row:
                        metrics["threads_connected"] = int(row[1])
                except:
                    pass
                
                try:
                    result = connection.execute(text("SHOW STATUS LIKE 'Uptime'"))
                    row = result.fetchone()
                    if row:
                        metrics["uptime_seconds"] = int(row[1])
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Performance check failed: {e}")
            metrics["error"] = str(e)
        
        return metrics
    
    def _check_table_status(self) -> Dict[str, Any]:
        """检查数据库表状态"""
        table_info = {}
        
        try:
            with engine.connect() as connection:
                # 检查关键表是否存在
                critical_tables = ["users", "subnets", "ip_addresses"]
                
                for table in critical_tables:
                    try:
                        result = connection.execute(
                            text(f"SELECT COUNT(*) FROM information_schema.tables "
                                f"WHERE table_schema = DATABASE() AND table_name = '{table}'")
                        )
                        exists = result.fetchone()[0] > 0
                        table_info[table] = {"exists": exists}
                        
                        if exists:
                            # 获取表记录数
                            result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                            count = result.fetchone()[0]
                            table_info[table]["record_count"] = count
                            
                    except Exception as e:
                        table_info[table] = {"exists": False, "error": str(e)}
                
        except Exception as e:
            logger.error(f"Table status check failed: {e}")
            table_info["error"] = str(e)
        
        return table_info
    
    def _get_database_info(self) -> Dict[str, Any]:
        """获取数据库基本信息"""
        info = {}
        
        try:
            with engine.connect() as connection:
                # 数据库版本
                result = connection.execute(text("SELECT VERSION()"))
                info["version"] = result.fetchone()[0]
                
                # 当前数据库名
                result = connection.execute(text("SELECT DATABASE()"))
                info["database_name"] = result.fetchone()[0]
                
                # 字符集
                result = connection.execute(text("SELECT @@character_set_database"))
                info["charset"] = result.fetchone()[0]
                
                # 时区
                result = connection.execute(text("SELECT @@time_zone"))
                info["timezone"] = result.fetchone()[0]
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            info["error"] = str(e)
        
        return info
    
    def _determine_health_status(
        self, 
        pool_stats: ConnectionPoolStats, 
        performance_metrics: Dict[str, Any],
        response_time_ms: float
    ) -> str:
        """
        根据各项指标判断健康状态
        
        Returns:
            str: "healthy", "degraded", "unhealthy"
        """
        # 检查响应时间
        if response_time_ms > 5000:  # 5秒
            return "unhealthy"
        elif response_time_ms > 1000:  # 1秒
            status = "degraded"
        else:
            status = "healthy"
        
        # 检查连接池使用率
        if pool_stats.utilization_percent > 90:
            return "unhealthy"
        elif pool_stats.utilization_percent > 70:
            status = "degraded"
        
        # 检查简单查询性能
        simple_query_time = performance_metrics.get("simple_query_ms", 0)
        if simple_query_time > 1000:  # 1秒
            return "unhealthy"
        elif simple_query_time > 100:  # 100毫秒
            status = "degraded"
        
        return status
    
    def _update_history(self, result: HealthCheckResult) -> None:
        """更新检查历史"""
        self.last_check_time = result.timestamp
        self.last_result = result
        
        self.check_history.append(result)
        
        # 保持历史记录大小限制
        if len(self.check_history) > self.max_history_size:
            self.check_history = self.check_history[-self.max_history_size:]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康状态摘要"""
        if not self.last_result:
            return {"status": "unknown", "message": "No health check performed yet"}
        
        # 计算最近的健康趋势
        recent_checks = self.check_history[-10:] if len(self.check_history) >= 10 else self.check_history
        healthy_count = sum(1 for check in recent_checks if check.status == "healthy")
        degraded_count = sum(1 for check in recent_checks if check.status == "degraded")
        unhealthy_count = sum(1 for check in recent_checks if check.status == "unhealthy")
        
        avg_response_time = (
            sum(check.response_time_ms for check in recent_checks) / len(recent_checks)
            if recent_checks else 0
        )
        
        return {
            "current_status": self.last_result.status,
            "last_check": self.last_result.timestamp.isoformat(),
            "response_time_ms": self.last_result.response_time_ms,
            "recent_trend": {
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "total_checks": len(recent_checks)
            },
            "avg_response_time_ms": round(avg_response_time, 2),
            "connection_pool": self.last_result.details.get("connection_pool", {}),
            "error": self.last_result.error
        }


# 全局健康检查器实例
health_checker = DatabaseHealthChecker()


def get_database_health() -> Dict[str, Any]:
    """
    获取数据库健康状态
    这是一个快速检查，适用于API健康检查端点
    
    Returns:
        Dict[str, Any]: 健康状态信息
    """
    try:
        # 如果最近5分钟内有检查结果，直接返回
        if (health_checker.last_check_time and 
            datetime.utcnow() - health_checker.last_check_time < timedelta(minutes=5)):
            return health_checker.get_health_summary()
        
        # 执行新的健康检查
        result = health_checker.perform_health_check()
        return health_checker.get_health_summary()
        
    except Exception as e:
        logger.error(f"Failed to get database health: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def perform_detailed_health_check() -> HealthCheckResult:
    """
    执行详细的数据库健康检查
    
    Returns:
        HealthCheckResult: 详细的健康检查结果
    """
    return health_checker.perform_health_check()


def get_connection_pool_info() -> Dict[str, Any]:
    """
    获取连接池详细信息
    
    Returns:
        Dict[str, Any]: 连接池信息
    """
    try:
        stats = health_checker._get_connection_pool_stats()
        return {
            "pool_configuration": {
                "pool_size": engine.pool.size(),
                "max_overflow": engine.pool._max_overflow,
                "pool_timeout": engine.pool._timeout,
                "pool_recycle": engine.pool._recycle
            },
            "current_stats": stats.__dict__,
            "recommendations": _get_pool_recommendations(stats)
        }
    except Exception as e:
        logger.error(f"Failed to get connection pool info: {e}")
        return {"error": str(e)}


def _get_pool_recommendations(stats: ConnectionPoolStats) -> List[str]:
    """根据连接池统计提供优化建议"""
    recommendations = []
    
    if stats.utilization_percent > 80:
        recommendations.append("连接池使用率过高，建议增加pool_size或max_overflow")
    
    if stats.invalid > 0:
        recommendations.append(f"发现{stats.invalid}个无效连接，可能存在连接泄漏")
    
    if stats.overflow > stats.pool_size * 0.5:
        recommendations.append("溢出连接较多，建议增加基础pool_size")
    
    if not recommendations:
        recommendations.append("连接池状态良好")
    
    return recommendations