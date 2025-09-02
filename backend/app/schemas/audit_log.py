from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ActionType(str, Enum):
    """操作类型枚举"""
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ALLOCATE = "ALLOCATE"
    RELEASE = "RELEASE"
    RESERVE = "RESERVE"


class EntityType(str, Enum):
    """实体类型枚举"""
    IP = "ip"
    SUBNET = "subnet"
    USER = "user"
    CUSTOM_FIELD = "custom_field"
    TAG = "tag"


class AuditLogBase(BaseModel):
    """审计日志基础模型"""
    action: ActionType
    entity_type: EntityType
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """创建审计日志模型"""
    user_id: int


class AuditLogResponse(AuditLogBase):
    """审计日志响应模型"""
    id: int
    user_id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogSearchRequest(BaseModel):
    """审计日志搜索请求模型"""
    user_id: Optional[int] = Field(None, description="用户ID")
    entity_type: Optional[EntityType] = Field(None, description="实体类型")
    action: Optional[ActionType] = Field(None, description="操作类型")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    entity_id: Optional[int] = Field(None, description="实体ID")
    skip: int = Field(0, ge=0, description="跳过记录数")
    limit: int = Field(50, ge=1, le=1000, description="返回记录数")


class AuditLogSearchResponse(BaseModel):
    """审计日志搜索响应模型"""
    items: List[AuditLogResponse]
    total: int
    skip: int
    limit: int


class EntityHistoryResponse(BaseModel):
    """实体历史记录响应模型"""
    entity_type: EntityType
    entity_id: int
    history: List[AuditLogResponse]


class UserActivityResponse(BaseModel):
    """用户活动记录响应模型"""
    user_id: int
    username: str
    activities: List[AuditLogResponse]


class AuditLogExportRequest(BaseModel):
    """审计日志导出请求模型"""
    user_id: Optional[int] = None
    entity_type: Optional[EntityType] = None
    action: Optional[ActionType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field("csv", pattern="^(csv|excel|json)$", description="导出格式")


class AuditLogStatsResponse(BaseModel):
    """审计日志统计响应模型"""
    total_logs: int
    actions_count: Dict[str, int]
    entities_count: Dict[str, int]
    users_count: Dict[str, int]
    recent_activities: List[AuditLogResponse]