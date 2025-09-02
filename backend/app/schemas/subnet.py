from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
import ipaddress
import re


class SubnetBase(BaseModel):
    network: str = Field(..., description="网段CIDR格式，如192.168.1.0/24")
    netmask: str = Field(..., description="子网掩码")
    gateway: Optional[str] = Field(None, description="网关地址")
    description: Optional[str] = Field(None, description="网段描述")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")
    location: Optional[str] = Field(None, description="位置信息")

    @validator('network')
    def validate_network(cls, v):
        """验证网段CIDR格式"""
        try:
            network = ipaddress.ip_network(v, strict=False)
            return str(network)
        except ValueError:
            raise ValueError('无效的网段格式，请使用CIDR格式如192.168.1.0/24')

    @validator('netmask')
    def validate_netmask(cls, v):
        """验证子网掩码格式"""
        try:
            ipaddress.ip_address(v)
            # 验证是否为有效的子网掩码
            mask_int = int(ipaddress.ip_address(v))
            # 检查是否为连续的1后跟连续的0
            binary = bin(mask_int)[2:].zfill(32)
            if not re.match(r'^1*0*$', binary):
                raise ValueError('无效的子网掩码')
            return v
        except ValueError:
            raise ValueError('无效的子网掩码格式')

    @validator('gateway')
    def validate_gateway(cls, v, values):
        """验证网关地址是否在网段范围内"""
        if v is None:
            return v
        try:
            gateway_ip = ipaddress.ip_address(v)
            if 'network' in values:
                network = ipaddress.ip_network(values['network'], strict=False)
                if gateway_ip not in network:
                    raise ValueError('网关地址必须在网段范围内')
            return v
        except ValueError as e:
            if "网关地址必须在网段范围内" in str(e):
                raise e
            raise ValueError('无效的网关地址格式')

    @validator('vlan_id')
    def validate_vlan_id(cls, v):
        """验证VLAN ID范围"""
        if v is not None and (v < 1 or v > 4094):
            raise ValueError('VLAN ID必须在1-4094范围内')
        return v


class SubnetCreate(SubnetBase):
    """创建网段的请求模型"""
    pass


class SubnetUpdate(BaseModel):
    """更新网段的请求模型"""
    network: Optional[str] = Field(None, description="网段CIDR格式")
    netmask: Optional[str] = Field(None, description="子网掩码")
    gateway: Optional[str] = Field(None, description="网关地址")
    description: Optional[str] = Field(None, description="网段描述")
    vlan_id: Optional[int] = Field(None, description="VLAN ID")
    location: Optional[str] = Field(None, description="位置信息")

    @validator('network')
    def validate_network(cls, v):
        if v is not None:
            try:
                network = ipaddress.ip_network(v, strict=False)
                return str(network)
            except ValueError:
                raise ValueError('无效的网段格式，请使用CIDR格式如192.168.1.0/24')
        return v

    @validator('netmask')
    def validate_netmask(cls, v):
        if v is not None:
            try:
                ipaddress.ip_address(v)
                mask_int = int(ipaddress.ip_address(v))
                binary = bin(mask_int)[2:].zfill(32)
                if not re.match(r'^1*0*$', binary):
                    raise ValueError('无效的子网掩码')
                return v
            except ValueError:
                raise ValueError('无效的子网掩码格式')
        return v

    @validator('gateway')
    def validate_gateway(cls, v, values):
        if v is not None:
            try:
                gateway_ip = ipaddress.ip_address(v)
                if 'network' in values and values['network']:
                    network = ipaddress.ip_network(values['network'], strict=False)
                    if gateway_ip not in network:
                        raise ValueError('网关地址必须在网段范围内')
                return v
            except ValueError as e:
                if "网关地址必须在网段范围内" in str(e):
                    raise e
                raise ValueError('无效的网关地址格式')
        return v

    @validator('vlan_id')
    def validate_vlan_id(cls, v):
        if v is not None and (v < 1 or v > 4094):
            raise ValueError('VLAN ID必须在1-4094范围内')
        return v


class SubnetResponse(SubnetBase):
    """网段响应模型"""
    id: int
    created_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    ip_count: Optional[int] = Field(None, description="IP地址总数")
    allocated_count: Optional[int] = Field(None, description="已分配IP数量")
    available_count: Optional[int] = Field(None, description="可用IP数量")

    class Config:
        from_attributes = True


class SubnetListResponse(BaseModel):
    """网段列表响应模型"""
    subnets: List[SubnetResponse]
    total: int
    page: int
    size: int


class SubnetValidationRequest(BaseModel):
    """网段验证请求模型"""
    network: str = Field(..., description="要验证的网段CIDR格式")
    exclude_id: Optional[int] = Field(None, description="排除的网段ID（用于更新时验证）")


class SubnetValidationResponse(BaseModel):
    """网段验证响应模型"""
    is_valid: bool
    message: str
    overlapping_subnets: Optional[List[SubnetResponse]] = Field(None, description="重叠的网段列表")