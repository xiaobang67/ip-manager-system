"""
Pydantic 数据模式定义
用于API请求和响应数据验证
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any, TypeVar, Generic
from datetime import datetime, date
from enum import Enum


class IPStatusEnum(str, Enum):
    available = "available"
    allocated = "allocated"
    reserved = "reserved"
    blacklisted = "blacklisted"


class AllocationTypeEnum(str, Enum):
    static = "static"
    dhcp = "dhcp"
    reserved = "reserved"


class PriorityEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ActionTypeEnum(str, Enum):
    allocate = "allocate"
    release = "release"
    reserve = "reserve"
    unreserve = "unreserve"
    modify = "modify"


class OSTypeEnum(str, Enum):
    windows_server_2019 = "Windows Server 2019"
    windows_server_2022 = "Windows Server 2022"
    windows_10 = "Windows 10"
    windows_11 = "Windows 11"
    ubuntu_20_04 = "Ubuntu 20.04"
    ubuntu_22_04 = "Ubuntu 22.04"
    centos_7 = "CentOS 7"
    centos_8 = "CentOS 8"
    debian_10 = "Debian 10"
    debian_11 = "Debian 11"
    redhat_8 = "Red Hat Enterprise Linux 8"
    redhat_9 = "Red Hat Enterprise Linux 9"
    suse_15 = "SUSE Linux Enterprise 15"
    macos_monterey = "macOS Monterey"
    macos_ventura = "macOS Ventura"
    macos_sonoma = "macOS Sonoma"
    vmware_esxi_7 = "VMware vSphere ESXi 7"
    vmware_esxi_8 = "VMware vSphere ESXi 8"
    other = "其他"


# 泛型类型变量
T = TypeVar('T')


# 基础模式
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True


# 部门相关模式
class DepartmentBase(BaseSchema):
    name: str = Field(..., max_length=100, description="部门名称")
    code: str = Field(..., max_length=50, description="部门编码")
    parent_id: Optional[int] = Field(None, description="上级部门ID")
    description: Optional[str] = Field(None, description="部门描述")
    is_active: Optional[bool] = Field(True, description="是否激活")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# 简化的部门响应模式，避免循环引用
class DepartmentSimple(BaseSchema):
    id: int
    name: str
    code: str

class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    # 关联数据 - 使用简化模式避免循环引用
    children: Optional[List['DepartmentSimple']] = None
    parent: Optional[DepartmentSimple] = None


# 用户相关模式
class UserBase(BaseSchema):
    username: str = Field(..., max_length=50, description="用户名")
    real_name: str = Field(..., max_length=100, description="真实姓名")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="电话")
    department_id: Optional[int] = Field(None, description="所属部门")
    employee_id: Optional[str] = Field(None, max_length=50, description="员工编号")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    is_active: Optional[bool] = Field(True, description="是否激活")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseSchema):
    username: Optional[str] = Field(None, max_length=50)
    real_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    department_id: Optional[int] = None
    employee_id: Optional[str] = Field(None, max_length=50)
    position: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime
    department: Optional[DepartmentResponse] = None


# 网段相关模式
class NetworkSegmentBase(BaseSchema):
    name: str = Field(..., max_length=100, description="网段名称")
    network: str = Field(..., max_length=50, description="网络地址")
    start_ip: str = Field(..., max_length=15, description="起始IP地址")
    end_ip: str = Field(..., max_length=15, description="结束IP地址")
    subnet_mask: str = Field(..., max_length=15, description="子网掩码")
    gateway: Optional[str] = Field(None, max_length=15, description="网关地址")
    dns_servers: Optional[List[str]] = Field(None, description="DNS服务器列表")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")
    purpose: Optional[str] = Field(None, max_length=200, description="用途说明")
    location: Optional[str] = Field(None, max_length=200, description="物理位置")
    responsible_department_id: Optional[int] = Field(None, description="负责部门")
    responsible_user_id: Optional[int] = Field(None, description="负责人")
    is_active: Optional[bool] = Field(True, description="是否激活")

    @validator('start_ip', 'end_ip', 'gateway')
    def validate_ip(cls, v):
        if v is not None:
            import ipaddress
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError('Invalid IP address format')
        return v


class NetworkSegmentCreate(NetworkSegmentBase):
    pass


class NetworkSegmentUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=100)
    network: Optional[str] = Field(None, max_length=50)
    start_ip: Optional[str] = Field(None, max_length=15)
    end_ip: Optional[str] = Field(None, max_length=15)
    subnet_mask: Optional[str] = Field(None, max_length=15)
    gateway: Optional[str] = Field(None, max_length=15)
    dns_servers: Optional[List[str]] = None
    vlan_id: Optional[int] = None
    purpose: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    responsible_department_id: Optional[int] = None
    responsible_user_id: Optional[int] = None
    is_active: Optional[bool] = None


class NetworkSegmentResponse(NetworkSegmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    responsible_department: Optional[DepartmentResponse] = None
    responsible_user: Optional[UserResponse] = None


# IP地址相关模式
class IPAddressBase(BaseSchema):
    ip_address: str = Field(..., max_length=15, description="IP地址")
    network_segment_id: int = Field(..., description="所属网段")
    status: Optional[IPStatusEnum] = Field(IPStatusEnum.available, description="IP状态")
    allocation_type: Optional[AllocationTypeEnum] = Field(None, description="分配类型")
    device_name: Optional[str] = Field(None, max_length=100, description="设备名称")
    device_type: Optional[str] = Field(None, max_length=50, description="设备类型")
    mac_address: Optional[str] = Field(None, max_length=17, description="MAC地址")
    hostname: Optional[str] = Field(None, max_length=100, description="主机名")
    os_type: Optional[OSTypeEnum] = Field(None, description="操作系统")
    assigned_user_id: Optional[int] = Field(None, description="分配给用户")
    assigned_department_id: Optional[int] = Field(None, description="分配给部门")
    location: Optional[str] = Field(None, max_length=200, description="物理位置")
    purpose: Optional[str] = Field(None, max_length=500, description="用途说明")
    notes: Optional[str] = Field(None, description="备注")
    allocated_at: Optional[datetime] = Field(None, description="分配时间")
    expires_at: Optional[datetime] = Field(None, description="到期时间")
    last_seen: Optional[datetime] = Field(None, description="最后检测时间")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v

    @validator('mac_address')
    def validate_mac_address(cls, v):
        if v is not None:
            import re
            if not re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', v):
                raise ValueError('Invalid MAC address format')
        return v


class IPAddressCreate(IPAddressBase):
    pass


class IPAddressUpdate(BaseSchema):
    status: Optional[IPStatusEnum] = None
    allocation_type: Optional[AllocationTypeEnum] = None
    device_name: Optional[str] = Field(None, max_length=100)
    device_type: Optional[str] = Field(None, max_length=50)
    mac_address: Optional[str] = Field(None, max_length=17)
    hostname: Optional[str] = Field(None, max_length=100)
    os_type: Optional[OSTypeEnum] = Field(None, description="操作系统")
    assigned_user_id: Optional[int] = None
    assigned_department_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=200)
    purpose: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    allocated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    last_seen: Optional[datetime] = None


class IPAddressResponse(IPAddressBase):
    id: int
    created_at: datetime
    updated_at: datetime
    network_segment: Optional[NetworkSegmentResponse] = None
    assigned_user: Optional[UserResponse] = None
    assigned_department: Optional[DepartmentResponse] = None


# 地址保留相关模式
class ReservedAddressBase(BaseSchema):
    ip_address: str = Field(..., max_length=15, description="保留的IP地址")
    network_segment_id: int = Field(..., description="所属网段")
    reserved_for: str = Field(..., max_length=200, description="保留用途")
    reserved_by_user_id: int = Field(..., description="保留人")
    reserved_by_department_id: Optional[int] = Field(None, description="保留部门")
    start_date: date = Field(..., description="保留开始日期")
    end_date: Optional[date] = Field(None, description="保留结束日期")
    is_permanent: Optional[bool] = Field(False, description="是否永久保留")
    priority: Optional[PriorityEnum] = Field(PriorityEnum.medium, description="优先级")
    notes: Optional[str] = Field(None, description="保留说明")
    is_active: Optional[bool] = Field(True, description="是否生效")

    @validator('ip_address')
    def validate_ip_address(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError('Invalid IP address format')
        return v


class ReservedAddressCreate(ReservedAddressBase):
    pass


class ReservedAddressUpdate(BaseSchema):
    reserved_for: Optional[str] = Field(None, max_length=200)
    reserved_by_department_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_permanent: Optional[bool] = None
    priority: Optional[PriorityEnum] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ReservedAddressResponse(ReservedAddressBase):
    id: int
    created_at: datetime
    updated_at: datetime
    network_segment: Optional[NetworkSegmentResponse] = None
    reserved_by_user: Optional[UserResponse] = None
    reserved_by_department: Optional[DepartmentResponse] = None


# 通用响应模式
class MessageResponse(BaseSchema):
    message: str
    code: int = 200


class PaginatedResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


# 统计相关模式
class NetworkSegmentStats(BaseSchema):
    total_ips: int
    available_ips: int
    allocated_ips: int
    reserved_ips: int
    blacklisted_ips: int
    utilization_rate: float


class DashboardStats(BaseSchema):
    total_segments: int
    total_ips: int
    allocated_ips: int
    available_ips: int
    reserved_ips: int
    total_users: int
    total_departments: int




# 批量操作相关模式
class IPAddressBatchCreate(BaseSchema):
    """IP地址批量创建模式"""
    network_segment_id: int = Field(..., description="所属网段")
    ip_addresses: List[str] = Field(..., description="IP地址列表")
    device_name_prefix: Optional[str] = Field(None, max_length=50, description="设备名前缀")
    device_type: Optional[str] = Field(None, max_length=50, description="设备类型")
    assigned_user_id: Optional[int] = Field(None, description="分配用户ID")
    assigned_department_id: Optional[int] = Field(None, description="分配部门ID")
    purpose: Optional[str] = Field(None, max_length=500, description="用途说明")
    auto_assign_names: Optional[bool] = Field(True, description="自动分配设备名")


class IPAddressImportItem(BaseSchema):
    """Excel导入单条记录模式"""
    ip_address: str = Field(..., description="IP地址")
    network_segment_name: Optional[str] = Field(None, description="网段名称")
    device_name: Optional[str] = Field(None, description="设备名称")
    device_type: Optional[str] = Field(None, description="设备类型")
    mac_address: Optional[str] = Field(None, description="MAC地址")
    hostname: Optional[str] = Field(None, description="主机名")
    os_type: Optional[str] = Field(None, description="操作系统")
    assigned_user_name: Optional[str] = Field(None, description="分配用户姓名")
    assigned_department_name: Optional[str] = Field(None, description="分配部门名称")
    location: Optional[str] = Field(None, description="物理位置")
    purpose: Optional[str] = Field(None, description="用途说明")
    notes: Optional[str] = Field(None, description="备注")


class IPAddressImportResult(BaseSchema):
    """Excel导入结果模式"""
    total_rows: int = Field(..., description="总行数")
    success_count: int = Field(..., description="成功导入数")
    error_count: int = Field(..., description="错误数")
    errors: List[Dict[str, Any]] = Field(..., description="错误详情")
    success_items: List[IPAddressResponse] = Field(..., description="成功导入的记录")


class ExportIPAddressRequest(BaseSchema):
    """IP地址导出请求模式"""
    network_segment_ids: Optional[List[int]] = Field(None, description="网段ID列表")
    status_list: Optional[List[IPStatusEnum]] = Field(None, description="状态列表")
    assigned_user_ids: Optional[List[int]] = Field(None, description="分配用户ID列表")
    assigned_department_ids: Optional[List[int]] = Field(None, description="分配部门ID列表")
    include_history: Optional[bool] = Field(False, description="是否包含历史数据")
    search: Optional[str] = Field(None, description="搜索关键词")


class BatchOperationResult(BaseSchema):
    """批量操作结果模式"""
    total_count: int = Field(..., description="总数")
    success_count: int = Field(..., description="成功数")
    error_count: int = Field(..., description="失败数")
    success_items: List[IPAddressResponse] = Field(..., description="成功处理的记录")
    errors: List[Dict[str, Any]] = Field(..., description="错误详情")