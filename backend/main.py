from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import wait_for_database, get_database_info
from app.core.health_check import get_database_health, perform_detailed_health_check
from app.core.seed_data import seed_database
from app.core.audit_middleware import AuditMiddleware
from app.core.response_cache_middleware import setup_response_cache_middleware
from app.core.query_optimizer import initialize_database_optimizations
from app.core.redis_client import get_redis_health
from app.core.security_middleware import SecurityMiddleware
from app.core.exceptions import (
    IPAMException, 
    ipam_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler
)
from app.api.v1.api import api_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up IPAM backend...")
    
    # 等待数据库连接
    logger.info("Waiting for database connection...")
    if not wait_for_database(max_retries=30, retry_interval=2):
        logger.error("Failed to connect to database during startup")
        raise RuntimeError("Database connection failed")
    
    # 初始化数据库优化
    logger.info("Initializing database optimizations...")
    if initialize_database_optimizations():
        logger.info("Database optimizations initialized successfully")
    else:
        logger.warning("Database optimizations initialization failed")
    
    # 执行数据库种子数据初始化
    logger.info("Initializing database seed data...")
    if seed_database():
        logger.info("Database seed data initialized successfully")
    else:
        logger.warning("Database seed data initialization failed or skipped")
    
    # 执行健康检查
    health_result = perform_detailed_health_check()
    logger.info(f"Database health check: {health_result.status}")
    
    # 检查Redis连接
    redis_health = get_redis_health()
    logger.info(f"Redis health check: {redis_health.get('status', 'unknown')}")
    
    logger.info("IPAM backend startup completed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IPAM backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="IP Address Management System API",
    lifespan=lifespan
)

# 创建日志目录
os.makedirs("logs", exist_ok=True)

# 注册异常处理器
app.add_exception_handler(IPAMException, ipam_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware (should be first)
app.add_middleware(SecurityMiddleware)

# Add audit middleware
app.add_middleware(AuditMiddleware)

# Setup response cache middleware
setup_response_cache_middleware(app, enabled=True)

# Include API router
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """根端点，返回API基本信息"""
    return {
        "message": "IPAM Backend API", 
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": get_database_info()
    }


@app.get("/health")
async def health_check():
    """快速健康检查端点"""
    db_health = get_database_health()
    
    return {
        "status": "healthy" if db_health.get("status") == "healthy" else "degraded",
        "service": "ipam-backend",
        "version": settings.VERSION,
        "timestamp": db_health.get("timestamp"),
        "database": {
            "status": db_health.get("status"),
            "response_time_ms": db_health.get("response_time_ms"),
            "connection_pool": db_health.get("connection_pool", {})
        }
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查端点"""
    health_result = perform_detailed_health_check()
    redis_health = get_redis_health()
    
    return {
        "status": health_result.status,
        "timestamp": health_result.timestamp.isoformat(),
        "response_time_ms": health_result.response_time_ms,
        "details": health_result.details,
        "error": health_result.error,
        "redis": redis_health
    }


@app.get("/performance")
async def performance_info():
    """性能信息端点"""
    from app.core.query_optimizer import get_database_performance_info
    from app.core.cache_manager import cache_manager
    
    try:
        db_performance = get_database_performance_info()
        cache_stats = cache_manager.get_cache_stats()
        redis_health = get_redis_health()
        
        return {
            "database": db_performance,
            "cache": cache_stats,
            "redis": redis_health,
            "timestamp": db_performance.get("timestamp")
        }
    except Exception as e:
        logger.error(f"Failed to get performance info: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )