from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging
import time
from typing import Generator
from .config import settings

logger = logging.getLogger(__name__)

# Database engine configuration with optimized connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,           # 验证连接是否有效
    pool_recycle=3600,            # 1小时后回收连接
    pool_size=30,                 # 增加连接池大小以支持更高并发
    max_overflow=50,              # 增加最大溢出连接数
    pool_timeout=30,              # 获取连接超时时间
    echo=settings.DEBUG,          # 是否打印SQL语句
    echo_pool=settings.DEBUG,     # 是否打印连接池信息
    # 优化的连接参数
    connect_args={
        "charset": "utf8mb4",
        "autocommit": False,
        "connect_timeout": 60,
        "read_timeout": 30,
        "write_timeout": 30,
        # MySQL性能优化参数
        "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        "use_unicode": True,
        "cursorclass": "pymysql.cursors.DictCursor" if "pymysql" in settings.DATABASE_URL else None
    },
    # 连接池事件监听器
    pool_reset_on_return='commit',  # 连接返回池时提交事务
    pool_logging_name='ipam_pool'   # 连接池日志名称
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  # 防止会话提交后对象过期
)

# Create base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    数据库会话依赖注入
    用于FastAPI的依赖注入系统
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    数据库会话上下文管理器
    用于非FastAPI环境下的数据库操作
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def check_database_connection() -> bool:
    """
    检查数据库连接是否正常
    返回True表示连接正常，False表示连接异常
    """
    try:
        with engine.connect() as connection:
            # 执行简单查询测试连接
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database connection check successful")
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """
    获取数据库连接信息
    返回数据库状态和连接池信息
    """
    try:
        pool = engine.pool
        return {
            "status": "connected" if check_database_connection() else "disconnected",
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
            "url": str(engine.url).replace(f":{engine.url.password}@", ":***@") if engine.url.password else str(engine.url)
        }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def wait_for_database(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """
    等待数据库连接可用
    用于应用启动时等待数据库服务就绪
    
    Args:
        max_retries: 最大重试次数
        retry_interval: 重试间隔（秒）
    
    Returns:
        bool: 连接成功返回True，超时返回False
    """
    for attempt in range(max_retries):
        try:
            if check_database_connection():
                logger.info(f"Database connection established after {attempt + 1} attempts")
                return True
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
        
        if attempt < max_retries - 1:
            logger.info(f"Retrying database connection in {retry_interval} seconds...")
            time.sleep(retry_interval)
    
    logger.error(f"Failed to connect to database after {max_retries} attempts")
    return False


def create_tables():
    """
    创建所有数据库表
    仅在开发环境使用，生产环境应使用Alembic迁移
    """
    try:
        # 导入所有模型以确保它们被注册
        from app.models import (
            User, Subnet, IPAddress, CustomField, CustomFieldValue,
            Tag, AuditLog, SystemConfig, AlertRule, AlertHistory
        )
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def drop_tables():
    """
    删除所有数据库表
    仅在开发环境使用，生产环境禁止使用
    """
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("Cannot drop tables in production environment")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise