"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, JSON, Date, ForeignKey, UniqueConstraint, Index, Table
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base
from datetime import datetime

# 导入认证相关模型
from .auth_user import AuthUser, AuthGroup, UserSession


class Department(Base):
    """部门模型"""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="部门名称")
    code = Column(String(50), unique=True, nullable=False, comment="部门编码")
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True, comment="上级部门ID")
    description = Column(Text, comment="部门描述")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(TINYINT, default=1, comment="是否激活")
    
    # 关系
    parent = relationship("Department", remote_side=[id], backref="children")
    users = relationship("User", back_populates="department")
    network_segments = relationship("NetworkSegment", back_populates="responsible_department")
    ip_addresses = relationship("IPAddress", back_populates="assigned_department")
    reserved_addresses = relationship("ReservedAddress", back_populates="reserved_by_department")
    
    __table_args__ = (
        Index('idx_parent_id', 'parent_id'),
        Index('idx_code', 'code'),
        {'comment': '部门信息表'}
    )


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    real_name = Column(String(100), nullable=False, comment="真实姓名")
    email = Column(String(100), unique=True, comment="邮箱")
    phone = Column(String(20), comment="电话")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="所属部门")
    employee_id = Column(String(50), comment="员工编号")
    position = Column(String(100), comment="职位")
    
    # 认证相关字段
    ldap_dn = Column(String(500), comment="LDAP DN")
    auth_source = Column(String(20), default="ldap", comment="认证来源（ldap/local）")
    password_hash = Column(String(255), comment="密码哈希（本地用户）")
    last_login = Column(DateTime, comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    is_admin = Column(TINYINT, default=0, comment="是否管理员")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(TINYINT, default=1, comment="是否激活")
    
    # 关系
    department = relationship("Department", back_populates="users")
    responsible_segments = relationship("NetworkSegment", back_populates="responsible_user")
    assigned_ips = relationship("IPAddress", back_populates="assigned_user")
    reserved_addresses = relationship("ReservedAddress", back_populates="reserved_by_user")
    
    # 用户组关系
    groups = relationship("UserGroup", secondary="user_group_members", back_populates="users")
    
    __table_args__ = (
        Index('idx_username', 'username'),
        Index('idx_department_id', 'department_id'),
        Index('idx_employee_id', 'employee_id'),
        Index('idx_ldap_dn', 'ldap_dn'),
        Index('idx_auth_source', 'auth_source'),
        {'comment': '用户信息表'}
    )


# 用户组关联表
user_group_members = Table(
    'user_group_members',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('user_groups.id'), primary_key=True),
    Column('created_at', DateTime, default=func.now())
)


class UserGroup(Base):
    """用户组模型"""
    __tablename__ = "user_groups"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="组名")
    description = Column(Text, comment="组描述")
    ldap_dn = Column(String(500), comment="LDAP组DN")
    permissions = Column(JSON, comment="权限配置")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(TINYINT, default=1, comment="是否激活")
    
    # 关系
    users = relationship("User", secondary="user_group_members", back_populates="groups")
    
    __table_args__ = (
        Index('idx_name', 'name'),
        Index('idx_ldap_dn', 'ldap_dn'),
        {'comment': '用户组信息表'}
    )


class NetworkSegment(Base):
    """网段模型"""
    __tablename__ = "network_segments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, comment="网段名称")
    network = Column(String(50), nullable=False, comment="网络地址")
    start_ip = Column(String(15), nullable=False, comment="起始IP地址")
    end_ip = Column(String(15), nullable=False, comment="结束IP地址")
    subnet_mask = Column(String(15), nullable=False, comment="子网掩码")
    gateway = Column(String(15), comment="网关地址")
    dns_servers = Column(JSON, comment="DNS服务器列表")
    vlan_id = Column(Integer, comment="VLAN ID")
    purpose = Column(String(200), comment="用途说明")
    location = Column(String(200), comment="物理位置")
    responsible_department_id = Column(Integer, ForeignKey("departments.id"), comment="负责部门")
    responsible_user_id = Column(Integer, ForeignKey("users.id"), comment="负责人")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(TINYINT, default=1, comment="是否激活")
    
    # 关系
    responsible_department = relationship("Department", back_populates="network_segments")
    responsible_user = relationship("User", back_populates="responsible_segments")
    ip_addresses = relationship("IPAddress", back_populates="network_segment")
    reserved_addresses = relationship("ReservedAddress", back_populates="network_segment")
    
    __table_args__ = (
        Index('idx_network', 'network'),
        Index('idx_start_ip', 'start_ip'),
        Index('idx_end_ip', 'end_ip'),
        Index('idx_responsible_department', 'responsible_department_id'),
        Index('idx_responsible_user', 'responsible_user_id'),
        {'comment': '网段信息表'}
    )


class IPAddress(Base):
    """IP地址模型"""
    __tablename__ = "ip_addresses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(15), nullable=False, unique=True, comment="IP地址")
    network_segment_id = Column(Integer, ForeignKey("network_segments.id"), nullable=False, comment="所属网段")
    status = Column(Enum('available', 'allocated', 'reserved', 'blacklisted'), 
                   default='available', comment="IP状态")
    allocation_type = Column(Enum('static', 'dhcp', 'reserved'), comment="分配类型")
    device_name = Column(String(100), comment="设备名称")
    device_type = Column(String(50), comment="设备类型")
    mac_address = Column(String(17), comment="MAC地址")
    hostname = Column(String(100), comment="主机名")
    os_type = Column(String(50), comment="操作系统")
    assigned_user_id = Column(Integer, ForeignKey("users.id"), comment="分配给用户")
    assigned_department_id = Column(Integer, ForeignKey("departments.id"), comment="分配给部门")
    location = Column(String(200), comment="物理位置")
    purpose = Column(String(500), comment="用途说明")
    notes = Column(Text, comment="备注")
    allocated_at = Column(DateTime, comment="分配时间")
    expires_at = Column(DateTime, comment="到期时间")
    last_seen = Column(DateTime, comment="最后检测时间")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    network_segment = relationship("NetworkSegment", back_populates="ip_addresses")
    assigned_user = relationship("User", back_populates="assigned_ips")
    assigned_department = relationship("Department", back_populates="ip_addresses")
    
    __table_args__ = (
        UniqueConstraint('ip_address', name='unique_ip'),
        Index('idx_ip_address', 'ip_address'),
        Index('idx_network_segment_id', 'network_segment_id'),
        Index('idx_status', 'status'),
        Index('idx_assigned_user_id', 'assigned_user_id'),
        Index('idx_assigned_department_id', 'assigned_department_id'),
        Index('idx_mac_address', 'mac_address'),
        {'comment': 'IP地址信息表'}
    )


class ReservedAddress(Base):
    """地址保留模型"""
    __tablename__ = "reserved_addresses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(15), nullable=False, comment="保留的IP地址")
    network_segment_id = Column(Integer, ForeignKey("network_segments.id"), nullable=False, comment="所属网段")
    reserved_for = Column(String(200), nullable=False, comment="保留用途")
    reserved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="保留人")
    reserved_by_department_id = Column(Integer, ForeignKey("departments.id"), comment="保留部门")
    start_date = Column(Date, nullable=False, comment="保留开始日期")
    end_date = Column(Date, comment="保留结束日期")
    is_permanent = Column(TINYINT, default=0, comment="是否永久保留")
    priority = Column(Enum('low', 'medium', 'high', 'critical'), 
                     default='medium', comment="优先级")
    notes = Column(Text, comment="保留说明")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(TINYINT, default=1, comment="是否生效")
    
    # 关系
    network_segment = relationship("NetworkSegment", back_populates="reserved_addresses")
    reserved_by_user = relationship("User", back_populates="reserved_addresses")
    reserved_by_department = relationship("Department", back_populates="reserved_addresses")
    
    __table_args__ = (
        Index('idx_ip_address', 'ip_address'),
        Index('idx_network_segment_id', 'network_segment_id'),
        Index('idx_reserved_by_user_id', 'reserved_by_user_id'),
        Index('idx_reserved_by_department_id', 'reserved_by_department_id'),
        Index('idx_start_date', 'start_date'),
        Index('idx_end_date', 'end_date'),
        {'comment': '地址保留表'}
    )


class IPUsageHistory(Base):
    """IP使用历史模型"""
    __tablename__ = "ip_usage_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(15), nullable=False, comment="IP地址")
    action = Column(Enum('allocate', 'release', 'reserve', 'unreserve', 'modify'), 
                   nullable=False, comment="操作类型")
    old_status = Column(String(50), comment="原状态")
    new_status = Column(String(50), comment="新状态")
    user_id = Column(Integer, ForeignKey("users.id"), comment="操作用户")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="相关部门")
    device_info = Column(JSON, comment="设备信息")
    notes = Column(Text, comment="操作说明")
    operation_time = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_ip_address', 'ip_address'),
        Index('idx_action', 'action'),
        Index('idx_operation_time', 'operation_time'),
        {'comment': 'IP使用历史记录表'}
    )