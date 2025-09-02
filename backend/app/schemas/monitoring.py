"""
监控相关的数据模式定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ReportFormat(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"


class IPUtilizationStats(BaseModel):
    total_ips: int
    allocated_ips: int
    reserved_ips: int
    available_ips: int
    conflict_ips: int
    utilization_rate: float
    allocation_rate: float
    reservation_rate: float


class SubnetUtilizationStats(BaseModel):
    subnet_id: int
    network: str
    description: Optional[str]
    vlan_id: Optional[int]
    location: Optional[str]
    total_ips: int
    allocated_ips: int
    reserved_ips: int
    available_ips: int
    conflict_ips: int
    utilization_rate: float
    created_at: datetime


class AllocationTrend(BaseModel):
    date: str
    allocations: int


class AlertStatistics(BaseModel):
    active_rules: int
    recent_alerts: int
    unresolved_alerts: int
    severity_breakdown: Dict[str, int]


class DashboardSummary(BaseModel):
    ip_statistics: IPUtilizationStats
    alert_statistics: AlertStatistics
    total_subnets: int
    total_users: int
    recent_allocations_24h: int
    timestamp: str


class AlertRuleCreate(BaseModel):
    name: str = Field(..., description="警报规则名称")
    rule_type: str = Field(..., description="规则类型")
    threshold_value: Optional[float] = Field(None, description="阈值")
    subnet_id: Optional[int] = Field(None, description="网段ID")
    notification_emails: Optional[str] = Field(None, description="通知邮箱列表")


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    threshold_value: Optional[float] = None
    subnet_id: Optional[int] = None
    notification_emails: Optional[str] = None
    is_active: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    id: int
    name: str
    rule_type: str
    threshold_value: Optional[float]
    subnet_id: Optional[int]
    is_active: bool
    notification_emails: Optional[str]
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    id: int
    rule_id: int
    alert_message: str
    severity: str
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ReportRequest(BaseModel):
    report_type: str = Field(..., description="报告类型: utilization, inventory, subnet_planning")
    format: ReportFormat = Field(ReportFormat.PDF, description="导出格式")
    subnet_ids: Optional[List[int]] = Field(None, description="指定网段ID列表")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期范围")
    include_details: bool = Field(True, description="是否包含详细信息")


class ReportResponse(BaseModel):
    report_id: str
    report_type: str
    format: str
    file_url: str
    generated_at: datetime
    expires_at: datetime