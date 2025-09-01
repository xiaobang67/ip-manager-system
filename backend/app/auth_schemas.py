"""
认证相关的Pydantic模式定义
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.schemas import BaseSchema


# 登录相关
class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, max_length=150, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间（秒）")
    user: 'AuthUserResponse' = Field(..., description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class LogoutRequest(BaseModel):
    """登出请求"""
    refresh_token: Optional[str] = Field(None, description="刷新令牌")


# 用户相关
class AuthUserBase(BaseSchema):
    """用户基础信息"""
    username: str = Field(..., min_length=1, max_length=150, description="用户名")
    real_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    employee_id: Optional[str] = Field(None, max_length=50, description="员工ID")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    location: Optional[str] = Field(None, max_length=200, description="工作地点")
    notes: Optional[str] = Field(None, description="备注")
    is_active: bool = Field(default=True, description="是否激活")
    is_admin: bool = Field(default=False, description="是否为管理员")
    is_superuser: bool = Field(default=False, description="是否为超级用户")
    department_id: Optional[int] = Field(None, description="部门ID")


class AuthUserCreate(AuthUserBase):
    """创建用户"""
    password: Optional[str] = Field(None, min_length=6, description="密码（本地用户）")
    is_ldap_user: bool = Field(default=False, description="是否为LDAP用户")


class AuthUserUpdate(BaseSchema):
    """更新用户"""
    real_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    employee_id: Optional[str] = Field(None, max_length=50, description="员工ID")
    phone: Optional[str] = Field(None, max_length=20, description="电话号码")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    location: Optional[str] = Field(None, max_length=200, description="工作地点")
    notes: Optional[str] = Field(None, description="备注")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_admin: Optional[bool] = Field(None, description="是否为管理员")
    is_superuser: Optional[bool] = Field(None, description="是否为超级用户")
    department_id: Optional[int] = Field(None, description="部门ID")
    password: Optional[str] = Field(None, min_length=6, description="新密码")


class AuthUserResponse(AuthUserBase):
    """用户响应"""
    id: int = Field(..., description="用户ID")
    is_ldap_user: bool = Field(..., description="是否为LDAP用户")
    ldap_dn: Optional[str] = Field(None, description="LDAP DN")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    login_count: int = Field(..., description="登录次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    department: Optional[dict] = Field(None, description="部门信息")
    groups: List[str] = Field(default=[], description="用户组名称列表")
    permissions: List[str] = Field(default=[], description="权限列表")

    class Config:
        from_attributes = True


# 用户组相关
class AuthGroupBase(BaseSchema):
    """用户组基础信息"""
    name: str = Field(..., min_length=1, max_length=100, description="组名")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: bool = Field(default=True, description="是否激活")


class AuthGroupCreate(AuthGroupBase):
    """创建用户组"""
    is_ldap_group: bool = Field(default=False, description="是否为LDAP组")
    ldap_dn: Optional[str] = Field(None, description="LDAP DN")


class AuthGroupUpdate(BaseSchema):
    """更新用户组"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="组名")
    display_name: Optional[str] = Field(None, max_length=100, description="显示名称")
    description: Optional[str] = Field(None, description="描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AuthGroupResponse(AuthGroupBase):
    """用户组响应"""
    id: int = Field(..., description="组ID")
    is_ldap_group: bool = Field(..., description="是否为LDAP组")
    ldap_dn: Optional[str] = Field(None, description="LDAP DN")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    user_count: Optional[int] = Field(None, description="用户数量")

    class Config:
        from_attributes = True


# 会话相关
class UserSessionResponse(BaseSchema):
    """用户会话响应"""
    id: int = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    ip_address: Optional[str] = Field(None, description="客户端IP")
    user_agent: Optional[str] = Field(None, description="用户代理")
    created_at: datetime = Field(..., description="创建时间")
    expires_at: datetime = Field(..., description="过期时间")
    last_activity: datetime = Field(..., description="最后活动时间")
    is_active: bool = Field(..., description="是否激活")

    class Config:
        from_attributes = True


# 当前用户信息
class CurrentUserResponse(BaseSchema):
    """当前用户信息响应"""
    id: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    real_name: Optional[str] = Field(None, description="真实姓名")
    display_name: Optional[str] = Field(None, description="显示名称")
    email: Optional[str] = Field(None, description="邮箱")
    employee_id: Optional[str] = Field(None, description="员工ID")
    is_admin: bool = Field(..., description="是否为管理员")
    is_superuser: bool = Field(..., description="是否为超级用户")
    department: Optional[dict] = Field(None, description="部门信息")
    groups: List[str] = Field(default=[], description="用户组名称列表")
    permissions: List[str] = Field(default=[], description="权限列表")

    class Config:
        from_attributes = True


# 系统管理相关
class SyncLDAPRequest(BaseModel):
    """同步LDAP请求"""
    sync_users: bool = Field(default=True, description="是否同步用户")
    sync_groups: bool = Field(default=True, description="是否同步组")


class SyncLDAPResponse(BaseModel):
    """同步LDAP响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="消息")
    synced_users: int = Field(default=0, description="同步的用户数")
    synced_groups: int = Field(default=0, description="同步的组数")


class PasswordChangeRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="原密码")
    new_password: str = Field(..., min_length=6, description="新密码")


# 统计信息
class AuthStatsResponse(BaseModel):
    """认证统计信息响应"""
    total_users: int = Field(..., description="总用户数")
    active_users: int = Field(..., description="活跃用户数")
    ldap_users: int = Field(..., description="LDAP用户数")
    local_users: int = Field(..., description="本地用户数")
    total_groups: int = Field(..., description="总组数")
    ldap_groups: int = Field(..., description="LDAP组数")
    active_sessions: int = Field(..., description="活跃会话数")


# 更新前向引用
LoginResponse.model_rebuild()
AuthUserResponse.model_rebuild()
AuthGroupResponse.model_rebuild()
CurrentUserResponse.model_rebuild()