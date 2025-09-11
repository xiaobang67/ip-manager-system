"""
监控和报告相关的数据模式
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class IPStatistics(BaseModel):
    """IP地址统计"""
    total_ips: int
    allocated_ips: int
    reserved_ips: int
    available_ips: int
    conflict_ips: int
    utilization_rate: float

class AlertStatistics(BaseModel):
    """警报统计"""
    unresolved_alerts: int

class DashboardSummary(BaseModel):
    """仪表盘汇总数据"""
    ip_statistics: IPStatistics
    total_subnets: int
    alert_statistics: AlertStatistics

class IPUtilizationStats(BaseModel):
    """IP使用率统计"""
    allocated: int
    reserved: int
    available: int
    conflict: int

class SubnetUtilizationStats(BaseModel):
    """网段使用率统计"""
    subnet_id: int
    network: str
    description: Optional[str]
    total_ips: int
    allocated_ips: int
    utilization_rate: float

class AllocationTrend(BaseModel):
    """分配趋势"""
    date: str
    allocations: int

class TopSubnet(BaseModel):
    """使用率最高的网段"""
    network: str
    description: Optional[str]
    vlan_id: Optional[int]
    location: Optional[str]
    total_ips: int
    allocated_ips: int
    utilization_rate: float

