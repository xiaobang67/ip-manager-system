from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.ip_address import IPStatus
import ipaddress


class IPAddressBase(BaseModel):
    ip_address: str = Field(..., description="IP地址")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    device_type: Optional[str] = Field(None, description="设备类型")
    location: Optional[str] = Field(None, description="位置")
    assigned_to: Optional[str] = Field(None, description="分配给")
    description: Optional[str] = Field(None, description="描述")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('无效的IP地址格式')

    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is None:
            return v
        # 简单的MAC地址格式验证
        if len(v.replace(':', '').replace('-', '')) != 12:
            raise ValueError('无效的MAC地址格式')
        return v


class IPAddressCreate(IPAddressBase):
    subnet_id: int = Field(..., description="所属网段ID")
    status: Optional[IPStatus] = Field(IPStatus.AVAILABLE, description="IP状态")


class IPAddressUpdate(BaseModel):
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    device_type: Optional[str] = Field(None, description="设备类型")
    location: Optional[str] = Field(None, description="位置")
    assigned_to: Optional[str] = Field(None, description="分配给")
    description: Optional[str] = Field(None, description="描述")
    status: Optional[IPStatus] = Field(None, description="IP状态")

    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is None:
            return v
        if len(v.replace(':', '').replace('-', '')) != 12:
            raise ValueError('无效的MAC地址格式')
        return v


class IPAddressResponse(IPAddressBase):
    id: int
    subnet_id: int
    status: IPStatus
    allocated_at: Optional[datetime] = None
    allocated_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IPAddressWithSubnet(IPAddressResponse):
    subnet_network: Optional[str] = Field(None, description="所属网段")
    subnet_description: Optional[str] = Field(None, description="网段描述")


class IPAllocationRequest(BaseModel):
    subnet_id: int = Field(..., description="网段ID")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    device_type: Optional[str] = Field(None, description="设备类型")
    location: Optional[str] = Field(None, description="位置")
    assigned_to: Optional[str] = Field(None, description="分配给")
    description: Optional[str] = Field(None, description="描述")
    preferred_ip: Optional[str] = Field(None, description="首选IP地址")

    @validator('preferred_ip')
    def validate_preferred_ip(cls, v):
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('无效的IP地址格式')


class IPReservationRequest(BaseModel):
    ip_address: str = Field(..., description="要保留的IP地址")
    reason: Optional[str] = Field(None, description="保留原因")
    reserved_until: Optional[datetime] = Field(None, description="保留到期时间")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('无效的IP地址格式')


class IPReleaseRequest(BaseModel):
    ip_address: str = Field(..., description="要释放的IP地址")
    reason: Optional[str] = Field(None, description="释放原因")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('无效的IP地址格式')


class IPSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="搜索关键词")
    subnet_id: Optional[int] = Field(None, description="网段ID")
    status: Optional[IPStatus] = Field(None, description="IP状态")
    device_type: Optional[str] = Field(None, description="设备类型")
    location: Optional[str] = Field(None, description="位置")
    assigned_to: Optional[str] = Field(None, description="分配给")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    ip_range_start: Optional[str] = Field(None, description="IP范围起始")
    ip_range_end: Optional[str] = Field(None, description="IP范围结束")
    allocated_date_start: Optional[str] = Field(None, description="分配日期起始")
    allocated_date_end: Optional[str] = Field(None, description="分配日期结束")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    sort_by: Optional[str] = Field("ip_address", description="排序字段")
    sort_order: Optional[str] = Field("asc", description="排序方向: asc, desc")
    skip: int = Field(0, ge=0, description="跳过记录数")
    limit: int = Field(50, ge=1, le=1000, description="返回记录数")

    @validator('ip_range_start', 'ip_range_end')
    def validate_ip_range(cls, v):
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('无效的IP地址格式')

    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'ip_address', 'status', 'hostname', 'mac_address', 
            'device_type', 'location', 'assigned_to', 'allocated_at', 'created_at'
        ]
        if v not in allowed_fields:
            raise ValueError(f'排序字段必须是以下之一: {", ".join(allowed_fields)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('排序方向必须是 asc 或 desc')
        return v


class IPSearchResponse(BaseModel):
    items: List[IPAddressResponse] = Field(..., description="搜索结果")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页记录数")
    total_pages: int = Field(..., description="总页数")


class SearchHistoryRequest(BaseModel):
    search_name: Optional[str] = Field(None, description="搜索名称")
    search_params: dict = Field(..., description="搜索参数")
    is_favorite: bool = Field(False, description="是否收藏")


class SearchHistoryResponse(BaseModel):
    id: int
    search_name: Optional[str]
    search_params: dict
    is_favorite: bool
    created_at: datetime
    used_count: int


class IPConflictResponse(BaseModel):
    ip_address: str
    conflict_count: int
    conflicted_records: List[IPAddressResponse]


class IPStatisticsResponse(BaseModel):
    total: int = Field(..., description="总IP数量")
    available: int = Field(..., description="可用IP数量")
    allocated: int = Field(..., description="已分配IP数量")
    reserved: int = Field(..., description="保留IP数量")
    conflict: int = Field(..., description="冲突IP数量")
    utilization_rate: float = Field(..., description="使用率")


class IPSyncResponse(BaseModel):
    subnet_id: int
    network: str
    added: int = Field(..., description="新增IP数量")
    removed: int = Field(..., description="删除IP数量")
    kept: int = Field(..., description="保持不变IP数量")
    message: str


class IPRangeStatusRequest(BaseModel):
    start_ip: str = Field(..., description="起始IP地址")
    end_ip: str = Field(..., description="结束IP地址")

    @validator('start_ip', 'end_ip')
    def validate_ip_addresses(cls, v):
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError('无效的IP地址格式')


class IPRangeStatusResponse(BaseModel):
    ip_address: str
    status: str
    hostname: Optional[str] = None
    mac_address: Optional[str] = None
    assigned_to: Optional[str] = None


class BulkIPOperationRequest(BaseModel):
    ip_addresses: List[str] = Field(..., description="IP地址列表")
    operation: str = Field(..., description="操作类型: allocate, reserve, release")
    reason: Optional[str] = Field(None, description="操作原因")

    @validator('ip_addresses')
    def validate_ip_addresses(cls, v):
        for ip in v:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise ValueError(f'无效的IP地址格式: {ip}')
        return v

    @validator('operation')
    def validate_operation(cls, v):
        if v not in ['allocate', 'reserve', 'release']:
            raise ValueError('无效的操作类型')
        return v


class BulkIPOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    success_ips: List[str]
    failed_ips: List[dict]  # [{"ip": "x.x.x.x", "error": "error message"}]
    message: str