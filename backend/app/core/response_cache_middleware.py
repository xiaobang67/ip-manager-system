"""
API响应缓存中间件
提供API响应的自动缓存和缓存控制功能
"""
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from fastapi import FastAPI

from .redis_client import cache_service
from .cache_config import get_cache_config

logger = logging.getLogger(__name__)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """API响应缓存中间件"""
    
    def __init__(self, app: FastAPI, cache_enabled: bool = True):
        super().__init__(app)
        self.cache_enabled = cache_enabled
        self.cache_key_prefix = "api_response"
        
        # 可缓存的HTTP方法
        self.cacheable_methods = {"GET"}
        
        # 可缓存的路径模式
        self.cacheable_paths = [
            "/api/v1/users",
            "/api/v1/subnets",
            "/api/v1/ips",
            "/api/v1/tags",
            "/api/v1/custom-fields",
            "/api/v1/monitoring/dashboard",
            "/api/v1/monitoring/statistics",
            "/api/v1/reports"
        ]
        
        # 不缓存的路径模式
        self.non_cacheable_paths = [
            "/api/v1/auth",
            "/api/v1/users/profile",
            "/health",
            "/docs",
            "/openapi.json"
        ]
        
        # 默认缓存TTL（秒）
        self.default_ttl = 60
    
    async def dispatch(self, request: Request, call_next):
        """处理请求和响应"""
        if not self.cache_enabled:
            return await call_next(request)
        
        # 检查是否应该缓存此请求
        if not self._should_cache_request(request):
            return await call_next(request)
        
        # 生成缓存键
        cache_key = self._generate_cache_key(request)
        
        # 尝试从缓存获取响应
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for {request.url.path}")
            return self._create_response_from_cache(cached_response)
        
        # 执行请求
        response = await call_next(request)
        
        # 缓存响应（如果适合）
        if self._should_cache_response(response):
            await self._cache_response(cache_key, response)
            logger.debug(f"Cached response for {request.url.path}")
        
        return response
    
    def _should_cache_request(self, request: Request) -> bool:
        """判断是否应该缓存请求"""
        # 检查HTTP方法
        if request.method not in self.cacheable_methods:
            return False
        
        # 检查路径是否在不缓存列表中
        path = request.url.path
        for non_cacheable_path in self.non_cacheable_paths:
            if path.startswith(non_cacheable_path):
                return False
        
        # 检查路径是否在可缓存列表中
        for cacheable_path in self.cacheable_paths:
            if path.startswith(cacheable_path):
                return True
        
        return False
    
    def _should_cache_response(self, response: Response) -> bool:
        """判断是否应该缓存响应"""
        # 只缓存成功的响应
        if response.status_code != 200:
            return False
        
        # 检查响应头中的缓存控制
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False
        
        return True
    
    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        # 基础信息
        method = request.method
        path = request.url.path
        query_params = str(request.query_params)
        
        # 用户信息（如果有认证）
        user_id = getattr(request.state, 'user_id', 'anonymous')
        
        # 生成哈希
        key_data = f"{method}:{path}:{query_params}:{user_id}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        
        return f"{self.cache_key_prefix}:{key_hash}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取响应"""
        try:
            return cache_service.get(cache_key)
        except Exception as e:
            logger.error(f"Failed to get cached response: {e}")
            return None
    
    async def _cache_response(self, cache_key: str, response: Response):
        """缓存响应"""
        try:
            # 读取响应体
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # 重新创建响应体迭代器
            response.body_iterator = self._create_body_iterator(response_body)
            
            # 准备缓存数据
            cache_data = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body.decode('utf-8') if response_body else "",
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # 获取TTL
            ttl = self._get_cache_ttl(response)
            
            # 存储到缓存
            cache_service.set(cache_key, cache_data, ttl)
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
    
    def _create_body_iterator(self, body: bytes):
        """创建响应体迭代器"""
        async def body_iterator():
            yield body
        return body_iterator()
    
    def _create_response_from_cache(self, cached_data: Dict[str, Any]) -> Response:
        """从缓存数据创建响应"""
        try:
            headers = cached_data.get("headers", {})
            
            # 添加缓存标识头
            headers["X-Cache"] = "HIT"
            headers["X-Cache-Date"] = cached_data.get("cached_at", "")
            
            return JSONResponse(
                content=json.loads(cached_data.get("body", "{}")),
                status_code=cached_data.get("status_code", 200),
                headers=headers
            )
        except Exception as e:
            logger.error(f"Failed to create response from cache: {e}")
            # 返回空响应，让请求正常处理
            return JSONResponse(content={"error": "Cache error"}, status_code=500)
    
    def _get_cache_ttl(self, response: Response) -> int:
        """获取缓存TTL"""
        # 检查响应头中的缓存控制
        cache_control = response.headers.get("cache-control", "")
        
        # 解析max-age
        if "max-age=" in cache_control:
            try:
                max_age_part = [part for part in cache_control.split(",") if "max-age=" in part][0]
                max_age = int(max_age_part.split("=")[1].strip())
                return max_age
            except (IndexError, ValueError):
                pass
        
        # 使用默认TTL
        return self.default_ttl


class CacheControlDecorator:
    """缓存控制装饰器"""
    
    @staticmethod
    def cache_for(seconds: int):
        """设置缓存时间的装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                response = func(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers["Cache-Control"] = f"max-age={seconds}"
                return response
            return wrapper
        return decorator
    
    @staticmethod
    def no_cache(func):
        """禁用缓存的装饰器"""
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
            return response
        return wrapper
    
    @staticmethod
    def cache_private(seconds: int = 300):
        """设置私有缓存的装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                response = func(*args, **kwargs)
                if hasattr(response, 'headers'):
                    response.headers["Cache-Control"] = f"private, max-age={seconds}"
                return response
            return wrapper
        return decorator


class CacheInvalidationService:
    """缓存失效服务"""
    
    def __init__(self):
        self.cache_key_prefix = "api_response"
    
    def invalidate_by_pattern(self, pattern: str) -> int:
        """根据模式失效缓存"""
        try:
            full_pattern = f"{self.cache_key_prefix}:*{pattern}*"
            return cache_service.clear_pattern(full_pattern)
        except Exception as e:
            logger.error(f"Failed to invalidate cache by pattern {pattern}: {e}")
            return 0
    
    def invalidate_by_path(self, path: str) -> int:
        """根据路径失效缓存"""
        try:
            # 生成路径相关的缓存键模式
            pattern = f"*{path}*"
            return self.invalidate_by_pattern(pattern)
        except Exception as e:
            logger.error(f"Failed to invalidate cache by path {path}: {e}")
            return 0
    
    def invalidate_user_cache(self, user_id: int) -> int:
        """失效用户相关的缓存"""
        try:
            pattern = f"*:{user_id}"
            return self.invalidate_by_pattern(pattern)
        except Exception as e:
            logger.error(f"Failed to invalidate user cache for {user_id}: {e}")
            return 0
    
    def invalidate_all_api_cache(self) -> int:
        """失效所有API缓存"""
        try:
            pattern = f"{self.cache_key_prefix}:*"
            return cache_service.clear_pattern(pattern)
        except Exception as e:
            logger.error(f"Failed to invalidate all API cache: {e}")
            return 0


# 全局缓存失效服务实例
cache_invalidation_service = CacheInvalidationService()


def setup_response_cache_middleware(app: FastAPI, enabled: bool = True):
    """设置响应缓存中间件"""
    if enabled:
        app.add_middleware(ResponseCacheMiddleware, cache_enabled=enabled)
        logger.info("Response cache middleware enabled")
    else:
        logger.info("Response cache middleware disabled")


# 缓存控制装饰器实例
cache_control = CacheControlDecorator()