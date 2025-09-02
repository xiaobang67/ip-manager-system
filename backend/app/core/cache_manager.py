"""
缓存管理器
提供统一的缓存操作接口和缓存失效管理
"""
import logging
from typing import Any, Optional, List, Dict, Callable
from datetime import datetime, timedelta
import asyncio
from functools import wraps

from .redis_client import cache_service, DistributedLock
from .cache_config import (
    get_cache_config, get_cache_key, get_invalidation_patterns,
    CacheStrategy, CACHE_WARMUP_TASKS
)

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.cache = cache_service
        self._warmup_tasks = {}
        self._refresh_tasks = {}
    
    def get(self, cache_type: str, identifier: str = "", **kwargs) -> Optional[Any]:
        """
        获取缓存数据
        
        Args:
            cache_type: 缓存类型
            identifier: 标识符
            **kwargs: 额外参数用于生成缓存键
        """
        try:
            config = get_cache_config(cache_type)
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            
            result = self.cache.get(cache_key, config.serialize)
            
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                
                # 检查是否需要提前刷新
                if config.auto_refresh:
                    self._check_refresh_needed(cache_key, config)
                
                return result
            
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache {cache_type}:{identifier}: {e}")
            return None
    
    def set(self, cache_type: str, data: Any, identifier: str = "", **kwargs) -> bool:
        """
        设置缓存数据
        
        Args:
            cache_type: 缓存类型
            data: 缓存数据
            identifier: 标识符
            **kwargs: 额外参数用于生成缓存键
        """
        try:
            config = get_cache_config(cache_type)
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            
            success = self.cache.set(cache_key, data, config.ttl, config.serialize)
            
            if success:
                logger.debug(f"Cache set: {cache_key} (TTL: {config.ttl}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to set cache {cache_type}:{identifier}: {e}")
            return False
    
    def delete(self, cache_type: str, identifier: str = "", **kwargs) -> bool:
        """删除缓存数据"""
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            success = self.cache.delete(cache_key)
            
            if success:
                logger.debug(f"Cache deleted: {cache_key}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete cache {cache_type}:{identifier}: {e}")
            return False
    
    def invalidate(self, event_type: str, **context) -> int:
        """
        根据事件类型失效相关缓存
        
        Args:
            event_type: 事件类型
            **context: 上下文信息，用于生成具体的缓存键
        """
        try:
            patterns = get_invalidation_patterns(event_type)
            total_deleted = 0
            
            for pattern in patterns:
                # 替换模式中的占位符
                actual_pattern = self._resolve_pattern(pattern, **context)
                deleted_count = self.cache.clear_pattern(actual_pattern)
                total_deleted += deleted_count
                
                logger.info(f"Invalidated {deleted_count} cache entries for pattern: {actual_pattern}")
            
            logger.info(f"Total invalidated cache entries: {total_deleted}")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache for event {event_type}: {e}")
            return 0
    
    def get_or_set(self, cache_type: str, data_func: Callable, identifier: str = "", **kwargs) -> Any:
        """
        获取缓存数据，如果不存在则执行函数并缓存结果
        
        Args:
            cache_type: 缓存类型
            data_func: 数据获取函数
            identifier: 标识符
            **kwargs: 额外参数
        """
        # 先尝试从缓存获取
        cached_data = self.get(cache_type, identifier, **kwargs)
        if cached_data is not None:
            return cached_data
        
        # 使用分布式锁防止缓存击穿
        lock_key = f"lock:{cache_type}:{identifier}"
        with DistributedLock(lock_key, timeout=30):
            # 再次检查缓存（双重检查）
            cached_data = self.get(cache_type, identifier, **kwargs)
            if cached_data is not None:
                return cached_data
            
            # 执行数据获取函数
            try:
                data = data_func(**kwargs)
                if data is not None:
                    self.set(cache_type, data, identifier, **kwargs)
                return data
            except Exception as e:
                logger.error(f"Failed to execute data function for {cache_type}: {e}")
                raise
    
    async def get_or_set_async(self, cache_type: str, data_func: Callable, identifier: str = "", **kwargs) -> Any:
        """异步版本的get_or_set"""
        # 先尝试从缓存获取
        cached_data = self.get(cache_type, identifier, **kwargs)
        if cached_data is not None:
            return cached_data
        
        # 使用分布式锁防止缓存击穿
        lock_key = f"lock:{cache_type}:{identifier}"
        with DistributedLock(lock_key, timeout=30):
            # 再次检查缓存
            cached_data = self.get(cache_type, identifier, **kwargs)
            if cached_data is not None:
                return cached_data
            
            # 执行异步数据获取函数
            try:
                data = await data_func(**kwargs)
                if data is not None:
                    self.set(cache_type, data, identifier, **kwargs)
                return data
            except Exception as e:
                logger.error(f"Failed to execute async data function for {cache_type}: {e}")
                raise
    
    def batch_get(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量获取缓存数据
        
        Args:
            requests: 请求列表，每个请求包含cache_type和identifier
        """
        results = {}
        
        for req in requests:
            cache_type = req.get('cache_type')
            identifier = req.get('identifier', '')
            key = f"{cache_type}:{identifier}"
            
            try:
                data = self.get(cache_type, identifier)
                results[key] = data
            except Exception as e:
                logger.error(f"Failed to get cache in batch for {key}: {e}")
                results[key] = None
        
        return results
    
    def batch_set(self, data_list: List[Dict[str, Any]]) -> Dict[str, bool]:
        """
        批量设置缓存数据
        
        Args:
            data_list: 数据列表，每个包含cache_type、data和identifier
        """
        results = {}
        
        for item in data_list:
            cache_type = item.get('cache_type')
            data = item.get('data')
            identifier = item.get('identifier', '')
            key = f"{cache_type}:{identifier}"
            
            try:
                success = self.set(cache_type, data, identifier)
                results[key] = success
            except Exception as e:
                logger.error(f"Failed to set cache in batch for {key}: {e}")
                results[key] = False
        
        return results
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            # 获取所有缓存键
            all_keys = self.cache.keys("*")
            
            # 按前缀分组统计
            stats = {}
            for key in all_keys:
                prefix = key.split(':')[0] if ':' in key else 'unknown'
                if prefix not in stats:
                    stats[prefix] = {
                        'count': 0,
                        'total_ttl': 0,
                        'keys': []
                    }
                
                stats[prefix]['count'] += 1
                stats[prefix]['keys'].append(key)
                
                # 获取TTL
                ttl = self.cache.ttl(key)
                if ttl > 0:
                    stats[prefix]['total_ttl'] += ttl
            
            # 计算平均TTL
            for prefix_stats in stats.values():
                if prefix_stats['count'] > 0:
                    prefix_stats['avg_ttl'] = prefix_stats['total_ttl'] / prefix_stats['count']
                else:
                    prefix_stats['avg_ttl'] = 0
                
                # 移除keys列表以减少响应大小
                del prefix_stats['keys']
            
            return {
                'total_keys': len(all_keys),
                'by_prefix': stats,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'error': str(e)}
    
    def clear_all(self, confirm: bool = False) -> int:
        """清除所有缓存（危险操作）"""
        if not confirm:
            raise ValueError("Must confirm to clear all cache")
        
        try:
            keys = self.cache.keys("*")
            if keys:
                deleted = self.cache.client.delete(*keys)
                logger.warning(f"Cleared all cache: {deleted} keys deleted")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear all cache: {e}")
            return 0
    
    def _generate_cache_key(self, cache_type: str, identifier: str = "", **kwargs) -> str:
        """生成缓存键"""
        base_key = get_cache_key(cache_type, identifier)
        
        # 如果有额外参数，添加到键中
        if kwargs:
            params = sorted(kwargs.items())
            param_str = "_".join([f"{k}={v}" for k, v in params])
            return f"{base_key}:{hash(param_str)}"
        
        return base_key
    
    def _resolve_pattern(self, pattern: str, **context) -> str:
        """解析缓存模式中的占位符"""
        resolved_pattern = pattern
        
        # 替换常见的占位符
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in resolved_pattern:
                resolved_pattern = resolved_pattern.replace(placeholder, str(value))
        
        return resolved_pattern
    
    def _check_refresh_needed(self, cache_key: str, config):
        """检查是否需要提前刷新缓存"""
        try:
            ttl = self.cache.ttl(cache_key)
            if ttl > 0:
                remaining_ratio = ttl / config.ttl
                if remaining_ratio <= config.refresh_threshold:
                    # 需要刷新，添加到刷新任务队列
                    self._schedule_refresh(cache_key, config)
        except Exception as e:
            logger.error(f"Failed to check refresh for {cache_key}: {e}")
    
    def _schedule_refresh(self, cache_key: str, config):
        """调度缓存刷新任务"""
        # 这里可以实现异步刷新逻辑
        # 例如添加到任务队列或使用后台任务
        logger.info(f"Scheduled refresh for cache key: {cache_key}")
        # TODO: 实现实际的刷新逻辑


# 全局缓存管理器实例
cache_manager = CacheManager()


def cached(cache_type: str, identifier_func: Optional[Callable] = None, ttl: Optional[int] = None):
    """
    缓存装饰器
    
    Args:
        cache_type: 缓存类型
        identifier_func: 标识符生成函数
        ttl: 自定义TTL（覆盖配置中的TTL）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成标识符
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = hash(str(args) + str(sorted(kwargs.items())))
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_type, str(identifier))
            if cached_result is not None:
                return cached_result
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                if ttl:
                    # 使用自定义TTL
                    config = get_cache_config(cache_type)
                    original_ttl = config.ttl
                    config.ttl = ttl
                    cache_manager.set(cache_type, result, str(identifier))
                    config.ttl = original_ttl  # 恢复原始TTL
                else:
                    cache_manager.set(cache_type, result, str(identifier))
            
            return result
        return wrapper
    return decorator


def cached_async(cache_type: str, identifier_func: Optional[Callable] = None, ttl: Optional[int] = None):
    """异步缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成标识符
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = hash(str(args) + str(sorted(kwargs.items())))
            
            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_type, str(identifier))
            if cached_result is not None:
                return cached_result
            
            # 执行异步函数
            result = await func(*args, **kwargs)
            
            # 缓存结果
            if result is not None:
                if ttl:
                    # 使用自定义TTL
                    config = get_cache_config(cache_type)
                    original_ttl = config.ttl
                    config.ttl = ttl
                    cache_manager.set(cache_type, result, str(identifier))
                    config.ttl = original_ttl
                else:
                    cache_manager.set(cache_type, result, str(identifier))
            
            return result
        return wrapper
    return decorator


def invalidate_cache(event_type: str, **context):
    """缓存失效装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # 执行成功后失效相关缓存
            try:
                cache_manager.invalidate(event_type, **context)
            except Exception as e:
                logger.error(f"Failed to invalidate cache after {func.__name__}: {e}")
            
            return result
        return wrapper
    return decorator


def invalidate_cache_async(event_type: str, **context):
    """异步缓存失效装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # 执行成功后失效相关缓存
            try:
                cache_manager.invalidate(event_type, **context)
            except Exception as e:
                logger.error(f"Failed to invalidate cache after {func.__name__}: {e}")
            
            return result
        return wrapper
    return decorator