"""
时区配置模块 - 统一管理应用的时区设置
"""

from datetime import datetime, timezone, timedelta
import pytz

# 北京时区
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
UTC_TZ = pytz.UTC

def get_beijing_time():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

def get_utc_time():
    """获取当前UTC时间"""
    return datetime.now(UTC_TZ)

def utc_to_beijing(utc_dt):
    """将UTC时间转换为北京时间"""
    if utc_dt is None:
        return None
    
    if utc_dt.tzinfo is None:
        # 如果没有时区信息，假设是UTC
        utc_dt = UTC_TZ.localize(utc_dt)
    
    return utc_dt.astimezone(BEIJING_TZ)

def beijing_to_utc(beijing_dt):
    """将北京时间转换为UTC时间"""
    if beijing_dt is None:
        return None
    
    if beijing_dt.tzinfo is None:
        # 如果没有时区信息，假设是北京时间
        beijing_dt = BEIJING_TZ.localize(beijing_dt)
    
    return beijing_dt.astimezone(UTC_TZ)

def now_beijing():
    """获取当前北京时间（用于替代now_beijing()）"""
    return get_beijing_time().replace(tzinfo=None)

def format_beijing_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化北京时间"""
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # 假设是北京时间
        dt = BEIJING_TZ.localize(dt)
    else:
        # 转换为北京时间
        dt = dt.astimezone(BEIJING_TZ)
    
    return dt.strftime(format_str)