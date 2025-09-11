"""
数据库查询优化器
提供查询性能监控、索引管理和查询优化功能
"""
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
from contextlib import contextmanager
from sqlalchemy import text, inspect, Index
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine
from sqlalchemy.sql import Select
from datetime import datetime, timedelta
from app.core.timezone_config import now_beijing

from .database import engine, SessionLocal
from .redis_client import cache_service

logger = logging.getLogger(__name__)


class QueryPerformanceMonitor:
    """查询性能监控器"""
    
    def __init__(self):
        self.slow_query_threshold = 1.0  # 慢查询阈值（秒）
        self.cache_key_prefix = "query_perf"
    
    def log_query_performance(self, query: str, duration: float, params: Dict = None):
        """记录查询性能"""
        try:
            query_hash = hash(query)
            timestamp = now_beijing()
            
            perf_data = {
                "query": query[:500],  # 截断长查询
                "duration": duration,
                "timestamp": timestamp.isoformat(),
                "params": params or {},
                "is_slow": duration > self.slow_query_threshold
            }
            
            # 记录到Redis
            cache_key = f"{self.cache_key_prefix}:{query_hash}:{int(timestamp.timestamp())}"
            cache_service.set(cache_key, perf_data, ttl=86400)  # 保存24小时
            
            # 如果是慢查询，记录警告日志
            if duration > self.slow_query_threshold:
                logger.warning(f"Slow query detected: {duration:.3f}s - {query[:200]}...")
            else:
                logger.debug(f"Query executed: {duration:.3f}s")
                
        except Exception as e:
            logger.error(f"Failed to log query performance: {e}")
    
    def get_slow_queries(self, hours: int = 24) -> List[Dict]:
        """获取慢查询列表"""
        try:
            pattern = f"{self.cache_key_prefix}:*"
            keys = cache_service.keys(pattern)
            
            slow_queries = []
            cutoff_time = now_beijing() - timedelta(hours=hours)
            
            for key in keys:
                try:
                    data = cache_service.get(key)
                    if data and data.get('is_slow'):
                        query_time = datetime.fromisoformat(data['timestamp'])
                        if query_time > cutoff_time:
                            slow_queries.append(data)
                except Exception:
                    continue
            
            # 按执行时间排序
            slow_queries.sort(key=lambda x: x['duration'], reverse=True)
            return slow_queries
            
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []
    
    def get_query_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取查询统计信息"""
        try:
            pattern = f"{self.cache_key_prefix}:*"
            keys = cache_service.keys(pattern)
            
            total_queries = 0
            slow_queries = 0
            total_duration = 0.0
            cutoff_time = now_beijing() - timedelta(hours=hours)
            
            for key in keys:
                try:
                    data = cache_service.get(key)
                    if data:
                        query_time = datetime.fromisoformat(data['timestamp'])
                        if query_time > cutoff_time:
                            total_queries += 1
                            total_duration += data['duration']
                            if data.get('is_slow'):
                                slow_queries += 1
                except Exception:
                    continue
            
            avg_duration = total_duration / total_queries if total_queries > 0 else 0
            slow_query_ratio = slow_queries / total_queries if total_queries > 0 else 0
            
            return {
                "total_queries": total_queries,
                "slow_queries": slow_queries,
                "slow_query_ratio": slow_query_ratio,
                "avg_duration": avg_duration,
                "total_duration": total_duration,
                "period_hours": hours
            }
            
        except Exception as e:
            logger.error(f"Failed to get query stats: {e}")
            return {}


# 全局性能监控器实例
query_monitor = QueryPerformanceMonitor()


def monitor_query_performance(func):
    """查询性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 记录性能数据
            query_monitor.log_query_performance(
                query=func.__name__,
                duration=duration,
                params={"args_count": len(args), "kwargs_keys": list(kwargs.keys())}
            )
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            query_monitor.log_query_performance(
                query=f"{func.__name__}_ERROR",
                duration=duration,
                params={"error": str(e)}
            )
            raise
    
    return wrapper


@contextmanager
def query_performance_context(query_name: str):
    """查询性能监控上下文管理器"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        query_monitor.log_query_performance(query_name, duration)


class DatabaseIndexManager:
    """数据库索引管理器"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.inspector = inspect(engine)
    
    def get_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表的现有索引"""
        try:
            indexes = self.inspector.get_indexes(table_name)
            return indexes
        except Exception as e:
            logger.error(f"Failed to get indexes for table {table_name}: {e}")
            return []
    
    def create_performance_indexes(self):
        """创建性能优化索引"""
        indexes_to_create = [
            # IP地址表索引
            {
                "table": "ip_addresses",
                "name": "idx_ip_subnet_status",
                "columns": ["subnet_id", "status", "ip_address"],
                "unique": False
            },
            {
                "table": "ip_addresses", 
                "name": "idx_ip_status_allocated",
                "columns": ["status", "allocated_at"],
                "unique": False
            },
            {
                "table": "ip_addresses",
                "name": "idx_ip_hostname",
                "columns": ["hostname"],
                "unique": False
            },
            {
                "table": "ip_addresses",
                "name": "idx_ip_mac_address",
                "columns": ["mac_address"],
                "unique": False
            },
            
            # 网段表索引
            {
                "table": "subnets",
                "name": "idx_subnet_network",
                "columns": ["network"],
                "unique": True
            },
            {
                "table": "subnets",
                "name": "idx_subnet_vlan",
                "columns": ["vlan_id"],
                "unique": False
            },
            {
                "table": "subnets",
                "name": "idx_subnet_location",
                "columns": ["location"],
                "unique": False
            },
            
            # 用户表索引
            {
                "table": "users",
                "name": "idx_user_username",
                "columns": ["username"],
                "unique": True
            },
            {
                "table": "users",
                "name": "idx_user_email",
                "columns": ["email"],
                "unique": False
            },
            {
                "table": "users",
                "name": "idx_user_role_active",
                "columns": ["role", "is_active"],
                "unique": False
            },
            
            # 审计日志表索引
            {
                "table": "audit_logs",
                "name": "idx_audit_user_action",
                "columns": ["user_id", "action"],
                "unique": False
            },
            {
                "table": "audit_logs",
                "name": "idx_audit_entity",
                "columns": ["entity_type", "entity_id"],
                "unique": False
            },
            {
                "table": "audit_logs",
                "name": "idx_audit_created_at",
                "columns": ["created_at"],
                "unique": False
            },
            {
                "table": "audit_logs",
                "name": "idx_audit_user_created",
                "columns": ["user_id", "created_at"],
                "unique": False
            },
            
            # 标签关联表索引
            {
                "table": "ip_tags",
                "name": "idx_ip_tags_ip",
                "columns": ["ip_id"],
                "unique": False
            },
            {
                "table": "ip_tags",
                "name": "idx_ip_tags_tag",
                "columns": ["tag_id"],
                "unique": False
            },
            {
                "table": "subnet_tags",
                "name": "idx_subnet_tags_subnet",
                "columns": ["subnet_id"],
                "unique": False
            },
            {
                "table": "subnet_tags",
                "name": "idx_subnet_tags_tag",
                "columns": ["tag_id"],
                "unique": False
            },
            
            # 自定义字段值表索引
            {
                "table": "custom_field_values",
                "name": "idx_custom_field_entity",
                "columns": ["entity_type", "entity_id"],
                "unique": False
            },
            {
                "table": "custom_field_values",
                "name": "idx_custom_field_field_id",
                "columns": ["field_id"],
                "unique": False
            },
            
            # 警报相关索引
            {
                "table": "alert_history",
                "name": "idx_alert_rule_created",
                "columns": ["rule_id", "created_at"],
                "unique": False
            },
            {
                "table": "alert_history",
                "name": "idx_alert_severity_resolved",
                "columns": ["severity", "is_resolved"],
                "unique": False
            }
        ]
        
        created_count = 0
        for index_def in indexes_to_create:
            if self._create_index_if_not_exists(index_def):
                created_count += 1
        
        logger.info(f"Created {created_count} performance indexes")
        return created_count
    
    def _create_index_if_not_exists(self, index_def: Dict[str, Any]) -> bool:
        """如果索引不存在则创建"""
        try:
            table_name = index_def["table"]
            index_name = index_def["name"]
            columns = index_def["columns"]
            unique = index_def.get("unique", False)
            
            # 检查索引是否已存在
            existing_indexes = self.get_existing_indexes(table_name)
            for existing_index in existing_indexes:
                if existing_index["name"] == index_name:
                    logger.debug(f"Index {index_name} already exists on table {table_name}")
                    return False
            
            # 创建索引SQL
            unique_clause = "UNIQUE" if unique else ""
            columns_str = ", ".join(columns)
            sql = f"CREATE {unique_clause} INDEX {index_name} ON {table_name} ({columns_str})"
            
            with self.engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            
            logger.info(f"Created index {index_name} on table {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create index {index_def.get('name', 'unknown')}: {e}")
            return False
    
    def analyze_table_performance(self, table_name: str) -> Dict[str, Any]:
        """分析表性能"""
        try:
            with self.engine.connect() as conn:
                # 获取表统计信息
                stats_sql = f"""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    data_free
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = '{table_name}'
                """
                
                result = conn.execute(text(stats_sql)).fetchone()
                
                if result:
                    return {
                        "table_name": result[0],
                        "row_count": result[1],
                        "data_size_bytes": result[2],
                        "index_size_bytes": result[3],
                        "free_space_bytes": result[4],
                        "total_size_bytes": result[2] + result[3],
                        "index_ratio": result[3] / (result[2] + result[3]) if (result[2] + result[3]) > 0 else 0
                    }
                
                return {}
                
        except Exception as e:
            logger.error(f"Failed to analyze table performance for {table_name}: {e}")
            return {}
    
    def get_database_performance_summary(self) -> Dict[str, Any]:
        """获取数据库性能摘要"""
        try:
            tables = ["users", "subnets", "ip_addresses", "audit_logs", "tags", "custom_field_values"]
            summary = {
                "tables": {},
                "total_size_bytes": 0,
                "total_rows": 0,
                "timestamp": now_beijing().isoformat()
            }
            
            for table in tables:
                table_stats = self.analyze_table_performance(table)
                if table_stats:
                    summary["tables"][table] = table_stats
                    summary["total_size_bytes"] += table_stats.get("total_size_bytes", 0)
                    summary["total_rows"] += table_stats.get("row_count", 0)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get database performance summary: {e}")
            return {}


# 全局索引管理器实例
index_manager = DatabaseIndexManager(engine)


class QueryOptimizer:
    """查询优化器"""
    
    @staticmethod
    def optimize_ip_list_query(session: Session, filters: Dict[str, Any], page: int = 1, size: int = 50):
        """优化IP地址列表查询"""
        from app.models.ip_address import IPAddress
        from app.models.subnet import Subnet
        
        # 基础查询
        query = session.query(IPAddress)
        
        # 应用过滤器
        if filters.get("subnet_id"):
            query = query.filter(IPAddress.subnet_id == filters["subnet_id"])
        
        if filters.get("status"):
            if isinstance(filters["status"], list):
                query = query.filter(IPAddress.status.in_(filters["status"]))
            else:
                query = query.filter(IPAddress.status == filters["status"])
        
        if filters.get("search"):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                IPAddress.ip_address.like(search_term) |
                IPAddress.hostname.like(search_term) |
                IPAddress.mac_address.like(search_term) |
                IPAddress.description.like(search_term)
            )
        
        if filters.get("allocated_by"):
            query = query.filter(IPAddress.allocated_by == filters["allocated_by"])
        
        # 排序优化
        sort_field = filters.get("sort", "ip_address")
        sort_order = filters.get("order", "asc")
        
        if sort_field == "ip_address":
            # IP地址排序使用INET_ATON函数
            if sort_order == "desc":
                query = query.order_by(text("INET_ATON(ip_address) DESC"))
            else:
                query = query.order_by(text("INET_ATON(ip_address) ASC"))
        else:
            # 其他字段正常排序
            order_column = getattr(IPAddress, sort_field, IPAddress.ip_address)
            if sort_order == "desc":
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        return query
    
    @staticmethod
    def optimize_subnet_utilization_query(session: Session, subnet_id: Optional[int] = None):
        """优化网段利用率查询"""
        from app.models.ip_address import IPAddress
        from app.models.subnet import Subnet
        
        # 使用子查询优化
        subquery = session.query(
            IPAddress.subnet_id,
            IPAddress.status,
            text("COUNT(*) as count")
        ).group_by(IPAddress.subnet_id, IPAddress.status).subquery()
        
        query = session.query(
            Subnet.id,
            Subnet.network,
            Subnet.description,
            subquery.c.status,
            subquery.c.count
        ).outerjoin(subquery, Subnet.id == subquery.c.subnet_id)
        
        if subnet_id:
            query = query.filter(Subnet.id == subnet_id)
        
        return query
    
    @staticmethod
    def optimize_audit_log_query(session: Session, filters: Dict[str, Any], page: int = 1, size: int = 50):
        """优化审计日志查询"""
        from app.models.audit_log import AuditLog
        from app.models.user import User
        
        # 基础查询，使用JOIN优化
        query = session.query(AuditLog).join(User, AuditLog.user_id == User.id, isouter=True)
        
        # 应用过滤器
        if filters.get("user_id"):
            query = query.filter(AuditLog.user_id == filters["user_id"])
        
        if filters.get("action"):
            if isinstance(filters["action"], list):
                query = query.filter(AuditLog.action.in_(filters["action"]))
            else:
                query = query.filter(AuditLog.action == filters["action"])
        
        if filters.get("entity_type"):
            query = query.filter(AuditLog.entity_type == filters["entity_type"])
        
        if filters.get("start_date"):
            query = query.filter(AuditLog.created_at >= filters["start_date"])
        
        if filters.get("end_date"):
            query = query.filter(AuditLog.created_at <= filters["end_date"])
        
        # 按创建时间倒序排序（最新的在前）
        query = query.order_by(AuditLog.created_at.desc())
        
        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        return query
    
    @staticmethod
    def get_dashboard_stats_optimized(session: Session):
        """优化仪表盘统计查询"""
        from app.models.ip_address import IPAddress
        from app.models.subnet import Subnet
        from app.models.user import User
        
        # 使用单个查询获取IP统计
        ip_stats = session.query(
            IPAddress.status,
            text("COUNT(*) as count")
        ).group_by(IPAddress.status).all()
        
        # 获取网段总数
        subnet_count = session.query(Subnet).count()
        
        # 获取用户总数
        user_count = session.query(User).filter(User.is_active == True).count()
        
        # 获取最近24小时的活动
        from datetime import datetime, timedelta
        yesterday = now_beijing() - timedelta(days=1)
        
        recent_allocations = session.query(IPAddress).filter(
            IPAddress.allocated_at >= yesterday,
            IPAddress.status == 'allocated'
        ).count()
        
        return {
            "ip_stats": {stat.status: stat.count for stat in ip_stats},
            "subnet_count": subnet_count,
            "user_count": user_count,
            "recent_allocations": recent_allocations
        }


# 全局查询优化器实例
query_optimizer = QueryOptimizer()


def get_database_performance_info() -> Dict[str, Any]:
    """获取数据库性能信息"""
    try:
        # 获取查询统计
        query_stats = query_monitor.get_query_stats()
        
        # 获取数据库性能摘要
        db_summary = index_manager.get_database_performance_summary()
        
        # 获取慢查询
        slow_queries = query_monitor.get_slow_queries(hours=24)
        
        return {
            "query_stats": query_stats,
            "database_summary": db_summary,
            "slow_queries": slow_queries[:10],  # 只返回前10个慢查询
            "timestamp": now_beijing().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get database performance info: {e}")
        return {"error": str(e)}


def initialize_database_optimizations():
    """初始化数据库优化"""
    try:
        logger.info("Initializing database optimizations...")
        
        # 创建性能索引
        created_indexes = index_manager.create_performance_indexes()
        
        logger.info(f"Database optimization completed. Created {created_indexes} indexes.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database optimizations: {e}")
        return False