"""
缓存配置和策略定义
定义不同数据类型的缓存策略和TTL设置
"""
from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass


class CacheStrategy(Enum):
    """缓存策略枚举"""
    WRITE_THROUGH = "write_through"      # 写入时同时更新缓存
    WRITE_BEHIND = "write_behind"        # 异步写入缓存
    CACHE_ASIDE = "cache_aside"          # 旁路缓存
    REFRESH_AHEAD = "refresh_ahead"      # 提前刷新


@dataclass
class CacheConfig:
    """缓存配置类"""
    ttl: int                            # 过期时间（秒）
    strategy: CacheStrategy             # 缓存策略
    serialize: str = 'json'             # 序列化方式
    auto_refresh: bool = False          # 是否自动刷新
    refresh_threshold: float = 0.8      # 刷新阈值（TTL的百分比）


# 缓存配置字典
CACHE_CONFIGS: Dict[str, CacheConfig] = {
    # 用户相关缓存
    "user_profile": CacheConfig(
        ttl=1800,  # 30分钟
        strategy=CacheStrategy.CACHE_ASIDE,
        auto_refresh=True,
        refresh_threshold=0.7
    ),
    "user_permissions": CacheConfig(
        ttl=3600,  # 1小时
        strategy=CacheStrategy.CACHE_ASIDE,
        auto_refresh=True
    ),
    "user_list": CacheConfig(
        ttl=300,   # 5分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    
    # IP地址相关缓存
    "ip_list": CacheConfig(
        ttl=180,   # 3分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    "ip_detail": CacheConfig(
        ttl=600,   # 10分钟
        strategy=CacheStrategy.CACHE_ASIDE,
        auto_refresh=True
    ),
    "ip_statistics": CacheConfig(
        ttl=60,    # 1分钟
        strategy=CacheStrategy.REFRESH_AHEAD,
        auto_refresh=True,
        refresh_threshold=0.5
    ),
    "ip_search_results": CacheConfig(
        ttl=300,   # 5分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    
    # 网段相关缓存
    "subnet_list": CacheConfig(
        ttl=600,   # 10分钟
        strategy=CacheStrategy.CACHE_ASIDE,
        auto_refresh=True
    ),
    "subnet_detail": CacheConfig(
        ttl=900,   # 15分钟
        strategy=CacheStrategy.CACHE_ASIDE,
        auto_refresh=True
    ),
    "subnet_utilization": CacheConfig(
        ttl=120,   # 2分钟
        strategy=CacheStrategy.REFRESH_AHEAD,
        auto_refresh=True
    ),
    
    # 标签和自定义字段缓存
    "tags_list": CacheConfig(
        ttl=1800,  # 30分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    "custom_fields": CacheConfig(
        ttl=3600,  # 1小时
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    
    # 系统配置缓存
    "system_config": CacheConfig(
        ttl=7200,  # 2小时
        strategy=CacheStrategy.CACHE_ASIDE,
        auto_refresh=True
    ),
    
    # 报告和统计缓存
    "dashboard_stats": CacheConfig(
        ttl=60,    # 1分钟
        strategy=CacheStrategy.REFRESH_AHEAD,
        auto_refresh=True,
        refresh_threshold=0.3
    ),
    "utilization_report": CacheConfig(
        ttl=300,   # 5分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    "audit_logs": CacheConfig(
        ttl=180,   # 3分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    
    # 搜索相关缓存
    "search_suggestions": CacheConfig(
        ttl=1800,  # 30分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    "search_history": CacheConfig(
        ttl=86400, # 24小时
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    
    # API响应缓存
    "api_response": CacheConfig(
        ttl=60,    # 1分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    
    # 会话相关缓存
    "user_session": CacheConfig(
        ttl=1800,  # 30分钟
        strategy=CacheStrategy.WRITE_THROUGH
    ),
    "login_attempts": CacheConfig(
        ttl=900,   # 15分钟
        strategy=CacheStrategy.WRITE_THROUGH
    ),
    
    # 临时数据缓存
    "temp_data": CacheConfig(
        ttl=300,   # 5分钟
        strategy=CacheStrategy.CACHE_ASIDE
    ),
    "rate_limit": CacheConfig(
        ttl=3600,  # 1小时
        strategy=CacheStrategy.WRITE_THROUGH
    )
}


def get_cache_config(cache_type: str) -> CacheConfig:
    """获取缓存配置"""
    return CACHE_CONFIGS.get(cache_type, CacheConfig(
        ttl=300,
        strategy=CacheStrategy.CACHE_ASIDE
    ))


# 缓存键前缀定义
CACHE_KEY_PREFIXES = {
    # 用户相关
    "user_profile": "user:profile",
    "user_permissions": "user:permissions",
    "user_list": "user:list",
    "user_session": "session",
    
    # IP地址相关
    "ip_list": "ip:list",
    "ip_detail": "ip:detail",
    "ip_statistics": "ip:stats",
    "ip_search": "ip:search",
    
    # 网段相关
    "subnet_list": "subnet:list",
    "subnet_detail": "subnet:detail",
    "subnet_utilization": "subnet:util",
    
    # 标签和字段
    "tags_list": "tags:list",
    "custom_fields": "fields:custom",
    
    # 系统配置
    "system_config": "system:config",
    
    # 报告统计
    "dashboard_stats": "dashboard:stats",
    "utilization_report": "report:util",
    "audit_logs": "audit:logs",
    
    # 搜索
    "search_suggestions": "search:suggest",
    "search_history": "search:history",
    
    # API响应
    "api_response": "api:response",
    
    # 临时数据
    "temp_data": "temp",
    "rate_limit": "rate:limit",
    "login_attempts": "login:attempts"
}


def get_cache_key(cache_type: str, identifier: str = "") -> str:
    """生成缓存键"""
    prefix = CACHE_KEY_PREFIXES.get(cache_type, cache_type)
    if identifier:
        return f"{prefix}:{identifier}"
    return prefix


# 缓存失效策略
CACHE_INVALIDATION_RULES = {
    # 当用户信息更新时，需要清除的缓存
    "user_updated": [
        "user:profile:*",
        "user:list:*",
        "user:permissions:*"
    ],
    
    # 当IP地址状态变更时，需要清除的缓存
    "ip_updated": [
        "ip:list:*",
        "ip:detail:*",
        "ip:stats:*",
        "subnet:util:*",
        "dashboard:stats:*"
    ],
    
    # 当网段变更时，需要清除的缓存
    "subnet_updated": [
        "subnet:list:*",
        "subnet:detail:*",
        "subnet:util:*",
        "ip:list:*",
        "dashboard:stats:*"
    ],
    
    # 当标签变更时，需要清除的缓存
    "tag_updated": [
        "tags:list:*",
        "ip:list:*",
        "subnet:list:*"
    ],
    
    # 当系统配置变更时，需要清除的缓存
    "config_updated": [
        "system:config:*"
    ]
}


def get_invalidation_patterns(event_type: str) -> list:
    """获取缓存失效模式"""
    return CACHE_INVALIDATION_RULES.get(event_type, [])


# 缓存预热配置
CACHE_WARMUP_TASKS = [
    {
        "name": "warm_user_list",
        "cache_type": "user_list",
        "function": "user_service.get_users_cached",
        "schedule": "0 */6 * * *",  # 每6小时执行一次
        "priority": 1
    },
    {
        "name": "warm_subnet_list", 
        "cache_type": "subnet_list",
        "function": "subnet_service.get_subnets_cached",
        "schedule": "5 */6 * * *",
        "priority": 2
    },
    {
        "name": "warm_dashboard_stats",
        "cache_type": "dashboard_stats", 
        "function": "monitoring_service.get_dashboard_stats_cached",
        "schedule": "*/5 * * * *",  # 每5分钟执行一次
        "priority": 3
    },
    {
        "name": "warm_tags_list",
        "cache_type": "tags_list",
        "function": "tag_service.get_tags_cached", 
        "schedule": "10 */12 * * *",  # 每12小时执行一次
        "priority": 4
    }
]