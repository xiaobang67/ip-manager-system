"""
Redis客户端配置和缓存服务
提供数据缓存、会话存储和分布式锁功能
"""
import redis
import json
import pickle
from typing import Any, Optional, Union, Dict, List
from datetime import datetime, timedelta
from app.core.timezone_config import now_beijing
import logging
from functools import wraps
import asyncio
from contextlib import asynccontextmanager

from .config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis客户端封装类"""
    
    def __init__(self):
        self._client = None
        self._connection_pool = None
        self.connect()
    
    def connect(self):
        """建立Redis连接"""
        try:
            # 创建连接池
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=30
            )
            
            # 创建Redis客户端
            self._client = redis.Redis(
                connection_pool=self._connection_pool,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            self._client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None
            self._connection_pool = None
    
    def is_connected(self) -> bool:
        """检查Redis连接状态"""
        try:
            if self._client:
                self._client.ping()
                return True
        except Exception as e:
            logger.warning(f"Redis connection check failed: {e}")
        return False
    
    def reconnect(self):
        """重新连接Redis"""
        logger.info("Attempting to reconnect to Redis...")
        self.connect()
    
    def get_client(self) -> Optional[redis.Redis]:
        """获取Redis客户端实例"""
        if not self.is_connected():
            self.reconnect()
        return self._client
    
    def close(self):
        """关闭Redis连接"""
        if self._connection_pool:
            self._connection_pool.disconnect()
            logger.info("Redis connection closed")


# 全局Redis客户端实例
redis_client = RedisClient()


class CacheService:
    """缓存服务类"""
    
    def __init__(self):
        self.client = redis_client.get_client()
    
    def _ensure_connection(self):
        """确保Redis连接可用"""
        if not redis_client.is_connected():
            redis_client.reconnect()
            self.client = redis_client.get_client()
    
    def set(self, key: str, value: Any, ttl: int = 300, serialize: str = 'json') -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
            serialize: 序列化方式 ('json' 或 'pickle')
        """
        try:
            self._ensure_connection()
            if not self.client:
                return False
            
            # 序列化数据
            if serialize == 'json':
                serialized_value = json.dumps(value, default=str)
            elif serialize == 'pickle':
                serialized_value = pickle.dumps(value)
            else:
                serialized_value = str(value)
            
            # 设置缓存
            result = self.client.setex(key, ttl, serialized_value)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return result
            
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    def get(self, key: str, serialize: str = 'json') -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            serialize: 序列化方式 ('json' 或 'pickle')
        """
        try:
            self._ensure_connection()
            if not self.client:
                return None
            
            value = self.client.get(key)
            if value is None:
                return None
            
            # 反序列化数据
            if serialize == 'json':
                return json.loads(value)
            elif serialize == 'pickle':
                return pickle.loads(value)
            else:
                return value
                
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            self._ensure_connection()
            if not self.client:
                return False
            
            result = self.client.delete(key)
            logger.debug(f"Cache deleted: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        try:
            self._ensure_connection()
            if not self.client:
                return False
            
            return bool(self.client.exists(key))
            
        except Exception as e:
            logger.error(f"Failed to check cache existence {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """设置缓存过期时间"""
        try:
            self._ensure_connection()
            if not self.client:
                return False
            
            return bool(self.client.expire(key, ttl))
            
        except Exception as e:
            logger.error(f"Failed to set expiration for {key}: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """获取缓存剩余过期时间"""
        try:
            self._ensure_connection()
            if not self.client:
                return -1
            
            return self.client.ttl(key)
            
        except Exception as e:
            logger.error(f"Failed to get TTL for {key}: {e}")
            return -1
    
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        try:
            self._ensure_connection()
            if not self.client:
                return []
            
            return self.client.keys(pattern)
            
        except Exception as e:
            logger.error(f"Failed to get keys with pattern {pattern}: {e}")
            return []
    
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有缓存"""
        try:
            keys = self.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear pattern {pattern}: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """递增计数器"""
        try:
            self._ensure_connection()
            if not self.client:
                return None
            
            return self.client.incrby(key, amount)
            
        except Exception as e:
            logger.error(f"Failed to increment {key}: {e}")
            return None
    
    def hash_set(self, name: str, mapping: Dict[str, Any]) -> bool:
        """设置哈希表"""
        try:
            self._ensure_connection()
            if not self.client:
                return False
            
            # 序列化哈希表值
            serialized_mapping = {}
            for k, v in mapping.items():
                serialized_mapping[k] = json.dumps(v, default=str)
            
            return bool(self.client.hset(name, mapping=serialized_mapping))
            
        except Exception as e:
            logger.error(f"Failed to set hash {name}: {e}")
            return False
    
    def hash_get(self, name: str, key: str) -> Optional[Any]:
        """获取哈希表值"""
        try:
            self._ensure_connection()
            if not self.client:
                return None
            
            value = self.client.hget(name, key)
            if value:
                return json.loads(value)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get hash {name}[{key}]: {e}")
            return None
    
    def hash_get_all(self, name: str) -> Dict[str, Any]:
        """获取整个哈希表"""
        try:
            self._ensure_connection()
            if not self.client:
                return {}
            
            hash_data = self.client.hgetall(name)
            result = {}
            for k, v in hash_data.items():
                try:
                    result[k] = json.loads(v)
                except:
                    result[k] = v
            return result
            
        except Exception as e:
            logger.error(f"Failed to get all hash {name}: {e}")
            return {}


# 全局缓存服务实例
cache_service = CacheService()


class SessionStore:
    """会话存储服务"""
    
    def __init__(self):
        self.cache = cache_service
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.default_ttl = 1800  # 30分钟
    
    def create_session(self, session_id: str, user_id: int, user_data: Dict[str, Any], ttl: int = None) -> bool:
        """创建用户会话"""
        try:
            ttl = ttl or self.default_ttl
            session_key = f"{self.session_prefix}{session_id}"
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            
            # 存储会话数据
            session_data = {
                "user_id": user_id,
                "created_at": now_beijing().isoformat(),
                "last_accessed": now_beijing().isoformat(),
                **user_data
            }
            
            # 设置会话
            success = self.cache.set(session_key, session_data, ttl)
            
            if success:
                # 将会话ID添加到用户会话列表
                self.cache.client.sadd(user_sessions_key, session_id)
                self.cache.expire(user_sessions_key, ttl)
                logger.info(f"Session created for user {user_id}: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create session {session_id}: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.cache.get(session_key)
            
            if session_data:
                # 更新最后访问时间
                session_data["last_accessed"] = now_beijing().isoformat()
                self.cache.set(session_key, session_data, self.default_ttl)
                
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """更新会话数据"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.cache.get(session_key)
            
            if session_data:
                session_data.update(data)
                session_data["last_accessed"] = now_beijing().isoformat()
                return self.cache.set(session_key, session_data, self.default_ttl)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.cache.get(session_key)
            
            if session_data:
                user_id = session_data.get("user_id")
                if user_id:
                    user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
                    self.cache.client.srem(user_sessions_key, session_id)
            
            return self.cache.delete(session_key)
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def delete_user_sessions(self, user_id: int) -> int:
        """删除用户的所有会话"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{user_id}"
            session_ids = self.cache.client.smembers(user_sessions_key)
            
            deleted_count = 0
            for session_id in session_ids:
                if self.delete_session(session_id):
                    deleted_count += 1
            
            # 清除用户会话列表
            self.cache.delete(user_sessions_key)
            
            logger.info(f"Deleted {deleted_count} sessions for user {user_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to delete user sessions for {user_id}: {e}")
            return 0
    
    def extend_session(self, session_id: str, ttl: int = None) -> bool:
        """延长会话有效期"""
        try:
            ttl = ttl or self.default_ttl
            session_key = f"{self.session_prefix}{session_id}"
            return self.cache.expire(session_key, ttl)
            
        except Exception as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False


# 全局会话存储实例
session_store = SessionStore()


def cache_result(key_prefix: str, ttl: int = 300, serialize: str = 'json'):
    """
    缓存装饰器
    
    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间（秒）
        serialize: 序列化方式
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, serialize)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                cache_service.set(cache_key, result, ttl, serialize)
                logger.debug(f"Cache set: {cache_key}")
            
            return result
        return wrapper
    return decorator


async def cache_result_async(key_prefix: str, ttl: int = 300, serialize: str = 'json'):
    """
    异步缓存装饰器
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            cached_result = cache_service.get(cache_key, serialize)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result
            
            # 执行异步函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                cache_service.set(cache_key, result, ttl, serialize)
                logger.debug(f"Cache set: {cache_key}")
            
            return result
        return wrapper
    return decorator


class DistributedLock:
    """分布式锁"""
    
    def __init__(self, key: str, timeout: int = 10, blocking_timeout: int = 10):
        self.key = f"lock:{key}"
        self.timeout = timeout
        self.blocking_timeout = blocking_timeout
        self.client = cache_service.client
    
    def __enter__(self):
        if self.acquire():
            return self
        raise RuntimeError(f"Could not acquire lock: {self.key}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
    
    def acquire(self) -> bool:
        """获取锁"""
        try:
            cache_service._ensure_connection()
            if not self.client:
                return False
            
            # 使用SET命令的NX和EX选项实现分布式锁
            return bool(self.client.set(
                self.key, 
                "locked", 
                nx=True, 
                ex=self.timeout
            ))
            
        except Exception as e:
            logger.error(f"Failed to acquire lock {self.key}: {e}")
            return False
    
    def release(self) -> bool:
        """释放锁"""
        try:
            return bool(self.client.delete(self.key))
        except Exception as e:
            logger.error(f"Failed to release lock {self.key}: {e}")
            return False


def get_redis_health() -> Dict[str, Any]:
    """获取Redis健康状态"""
    try:
        client = redis_client.get_client()
        if not client:
            return {
                "status": "disconnected",
                "error": "Redis client not available"
            }
        
        # 获取Redis信息
        info = client.info()
        
        return {
            "status": "healthy",
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory": info.get("used_memory_human"),
            "used_memory_peak": info.get("used_memory_peak_human"),
            "keyspace_hits": info.get("keyspace_hits"),
            "keyspace_misses": info.get("keyspace_misses"),
            "total_commands_processed": info.get("total_commands_processed"),
            "uptime_in_seconds": info.get("uptime_in_seconds")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }