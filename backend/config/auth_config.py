"""
LDAP认证配置
基于您提供的LDAP配置信息
"""
import os
from typing import Optional

# LDAP配置开关
ENABLE_LDAP = False  # 禁用LDAP认证，改为使用本地认证

# LDAP服务器配置
LDAP_CONFIG = {
    # LDAP服务器地址
    "server_uri": os.getenv("LDAP_SERVER_URI", "ldap://192.168.0.38:389"),
    
    # 绑定DN和密码（用于连接LDAP服务器）
    "bind_dn": os.getenv("LDAP_BIND_DN", "cn=jumpserver,ou=技术部,ou=研发中心,dc=ost,dc=com"),
    "bind_password": os.getenv("LDAP_BIND_PASSWORD", "Abc123456"),
    
    # 用户搜索配置
    "user_search_base": os.getenv("LDAP_USER_SEARCH_BASE", "ou=技术部,ou=研发中心,dc=ost,dc=com"),
    "user_search_filter": os.getenv("LDAP_USER_SEARCH_FILTER", "(sAMAccountName={username})"),
    
    # 用户属性映射
    "user_attr_map": {
        "username": "sAMAccountName",
        "display_name": "displayName", 
        "email": "mail",
        "real_name": "cn",
        "employee_id": "employeeID"
    },
    
    # 组搜索配置
    "group_search_base": os.getenv("LDAP_GROUP_SEARCH_BASE", "ou=技术部,ou=研发中心,dc=ost,dc=com"),
    "group_search_filter": os.getenv("LDAP_GROUP_SEARCH_FILTER", "(objectClass=group)"),
    "group_attr_map": {
        "name": "cn",
        "description": "description",
        "members": "member"
    },
    
    # 连接配置
    "connect_timeout": 10,
    "read_timeout": 30,
    "always_update_user": True  # 每次登录从LDAP同步用户信息
}

# JWT配置
JWT_CONFIG = {
    "secret_key": os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"),
    "algorithm": "HS256",
    "access_token_expire_minutes": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
    "refresh_token_expire_days": int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
}