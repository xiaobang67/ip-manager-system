"""
用户认证相关数据模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

# 用户组关联表
user_group_association = Table(
    'user_group_association',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('auth_users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('auth_groups.id'), primary_key=True)
)

class AuthUser(Base):
    """
    认证用户模型
    扩展原有的用户模型以支持LDAP认证
    """
    __tablename__ = 'auth_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    username = Column(String(150), unique=True, nullable=False, comment="用户名")
    real_name = Column(String(100), nullable=True, comment="真实姓名")
    display_name = Column(String(100), nullable=True, comment="显示名称")
    email = Column(String(255), unique=True, nullable=True, comment="邮箱")
    employee_id = Column(String(50), nullable=True, comment="员工ID")
    
    # 认证相关
    password_hash = Column(String(128), nullable=True, comment="密码哈希（本地用户）")
    is_ldap_user = Column(Boolean, default=False, comment="是否为LDAP用户")
    ldap_dn = Column(String(500), nullable=True, comment="LDAP DN")
    
    # 状态和权限
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_admin = Column(Boolean, default=False, comment="是否为管理员")
    is_superuser = Column(Boolean, default=False, comment="是否为超级用户")
    
    # 登录相关
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 用户组关联
    groups = relationship("AuthGroup", secondary=user_group_association, back_populates="users")
    
    def __repr__(self):
        return f"<AuthUser(id={self.id}, username='{self.username}', real_name='{self.real_name}')>"

    # 添加属性访问器以解决类型问题
    @property
    def id_value(self):
        return self.id
    
    @property
    def username_value(self):
        return self.username
    
    @property
    def real_name_value(self):
        return self.real_name
    
    @property
    def display_name_value(self):
        return self.display_name
    
    @property
    def email_value(self):
        return self.email
    
    @property
    def employee_id_value(self):
        return self.employee_id
    
    @property
    def password_hash_value(self):
        return self.password_hash
    
    @property
    def is_ldap_user_value(self):
        return self.is_ldap_user
    
    @property
    def ldap_dn_value(self):
        return self.ldap_dn
    
    @property
    def is_active_value(self):
        return self.is_active
    
    @property
    def is_admin_value(self):
        return self.is_admin
    
    @property
    def is_superuser_value(self):
        return self.is_superuser


class AuthGroup(Base):
    """
    用户组模型
    """
    __tablename__ = 'auth_groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    name = Column(String(100), unique=True, nullable=False, comment="组名")
    display_name = Column(String(100), nullable=True, comment="显示名称")
    description = Column(Text, nullable=True, comment="描述")
    
    # LDAP相关
    is_ldap_group = Column(Boolean, default=False, comment="是否为LDAP组")
    ldap_dn = Column(String(500), nullable=True, comment="LDAP DN")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 用户关联
    users = relationship("AuthUser", secondary=user_group_association, back_populates="groups")
    
    def __repr__(self):
        return f"<AuthGroup(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"

    # 添加属性访问器以解决类型问题
    @property
    def id_value(self):
        return self.id
    
    @property
    def name_value(self):
        return self.name
    
    @property
    def display_name_value(self):
        return self.display_name
    
    @property
    def description_value(self):
        return self.description
    
    @property
    def is_ldap_group_value(self):
        return self.is_ldap_group
    
    @property
    def ldap_dn_value(self):
        return self.ldap_dn
    
    @property
    def is_active_value(self):
        return self.is_active


class UserSession(Base):
    """
    用户会话模型
    用于跟踪用户登录会话
    """
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('auth_users.id'), nullable=False, comment="用户ID")
    user = relationship("AuthUser")
    
    # 会话信息
    session_token = Column(String(255), unique=True, nullable=False, comment="会话令牌")
    refresh_token = Column(String(255), unique=True, nullable=True, comment="刷新令牌")
    
    # 时间信息
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    last_activity = Column(DateTime, default=func.now(), comment="最后活动时间")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    # 添加属性访问器以解决类型问题
    @property
    def id_value(self):
        return self.id
    
    @property
    def user_id_value(self):
        return self.user_id
    
    @property
    def session_token_value(self):
        return self.session_token
    
    @property
    def refresh_token_value(self):
        return self.refresh_token
    
    @property
    def is_active_value(self):
        return self.is_active