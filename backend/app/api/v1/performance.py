"""
性能测试和监控API端点
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.performance_testing import (
    PerformanceTester, DatabasePerformanceTester, CachePerformanceTester,
    run_comprehensive_performance_test
)
from app.core.query_optimizer import get_database_performance_info, query_monitor
from app.core.cache_manager import cache_manager
from app.core.redis_client import get_redis_health
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/database")
async def get_database_performance(
    current_user: User = Depends(get_current_user)
):
    """获取数据库性能信息"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        performance_info = get_database_performance_info()
        return performance_info
        
    except Exception as e:
        logger.error(f"Failed to get database performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache")
async def get_cache_performance(
    current_user: User = Depends(get_current_user)
):
    """获取缓存性能信息"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        cache_stats = cache_manager.get_cache_stats()
        redis_health = get_redis_health()
        
        return {
            "cache_stats": cache_stats,
            "redis_health": redis_health
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/slow-queries")
async def get_slow_queries(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """获取慢查询列表"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        slow_queries = query_monitor.get_slow_queries(hours=hours)
        return {
            "slow_queries": slow_queries,
            "period_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Failed to get slow queries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query-stats")
async def get_query_statistics(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """获取查询统计信息"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        query_stats = query_monitor.get_query_stats(hours=hours)
        return query_stats
        
    except Exception as e:
        logger.error(f"Failed to get query statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/load")
async def run_load_test(
    background_tasks: BackgroundTasks,
    endpoint: str,
    method: str = "GET",
    concurrent_users: int = 10,
    requests_per_user: int = 10,
    current_user: User = Depends(get_current_user)
):
    """运行负载测试"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if concurrent_users > 50 or requests_per_user > 50:
            raise HTTPException(status_code=400, detail="测试参数过大，请降低并发数或请求数")
        
        # 在后台运行测试
        def run_test():
            try:
                tester = PerformanceTester()
                result = tester.run_load_test(
                    endpoint=endpoint,
                    method=method,
                    concurrent_users=concurrent_users,
                    requests_per_user=requests_per_user
                )
                logger.info(f"Load test completed: {result.requests_per_second:.2f} RPS")
            except Exception as e:
                logger.error(f"Load test failed: {e}")
        
        background_tasks.add_task(run_test)
        
        return {
            "message": "负载测试已启动",
            "endpoint": endpoint,
            "method": method,
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user
        }
        
    except Exception as e:
        logger.error(f"Failed to start load test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/cache")
async def run_cache_test(
    iterations: int = 1000,
    current_user: User = Depends(get_current_user)
):
    """运行缓存性能测试"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if iterations > 5000:
            raise HTTPException(status_code=400, detail="测试迭代次数过大")
        
        tester = CachePerformanceTester()
        result = tester.test_cache_performance(iterations=iterations)
        
        return {
            "message": "缓存性能测试完成",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to run cache test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/database")
async def run_database_test(
    iterations: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """运行数据库性能测试"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if iterations > 1000:
            raise HTTPException(status_code=400, detail="测试迭代次数过大")
        
        tester = DatabasePerformanceTester()
        
        # 简单查询测试
        def simple_query(db_session):
            return db_session.execute("SELECT 1").fetchone()
        
        result = tester.test_query_performance(simple_query, iterations=iterations)
        
        return {
            "message": "数据库性能测试完成",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to run database test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/comprehensive")
async def run_comprehensive_test(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """运行综合性能测试"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 在后台运行综合测试
        def run_test():
            try:
                result = run_comprehensive_performance_test()
                logger.info("Comprehensive performance test completed")
                # 这里可以将结果保存到数据库或发送通知
            except Exception as e:
                logger.error(f"Comprehensive performance test failed: {e}")
        
        background_tasks.add_task(run_test)
        
        return {
            "message": "综合性能测试已启动，请稍后查看日志获取结果"
        }
        
    except Exception as e:
        logger.error(f"Failed to start comprehensive test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/clear")
async def clear_cache(
    pattern: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """清除缓存"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        if pattern:
            cleared_count = cache_manager.cache.clear_pattern(pattern)
            message = f"已清除 {cleared_count} 个匹配模式 '{pattern}' 的缓存项"
        else:
            # 清除所有缓存需要确认
            cleared_count = cache_manager.clear_all(confirm=True)
            message = f"已清除所有缓存，共 {cleared_count} 个项目"
        
        return {
            "message": message,
            "cleared_count": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/invalidate")
async def invalidate_cache(
    event_type: str,
    context: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user)
):
    """手动失效缓存"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        context = context or {}
        invalidated_count = cache_manager.invalidate(event_type, **context)
        
        return {
            "message": f"已失效 {invalidated_count} 个缓存项",
            "event_type": event_type,
            "context": context,
            "invalidated_count": invalidated_count
        }
        
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_user)
):
    """获取性能摘要信息"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="需要管理员权限")
        
        # 获取各种性能指标
        db_performance = get_database_performance_info()
        cache_stats = cache_manager.get_cache_stats()
        redis_health = get_redis_health()
        query_stats = query_monitor.get_query_stats(hours=24)
        
        return {
            "database": {
                "query_stats": db_performance.get("query_stats", {}),
                "slow_queries_count": len(db_performance.get("slow_queries", [])),
                "database_summary": db_performance.get("database_summary", {})
            },
            "cache": {
                "total_keys": cache_stats.get("total_keys", 0),
                "redis_status": redis_health.get("status", "unknown"),
                "memory_usage": redis_health.get("used_memory", "unknown")
            },
            "queries": {
                "total_queries_24h": query_stats.get("total_queries", 0),
                "slow_queries_24h": query_stats.get("slow_queries", 0),
                "avg_response_time": query_stats.get("avg_duration", 0),
                "slow_query_ratio": query_stats.get("slow_query_ratio", 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))