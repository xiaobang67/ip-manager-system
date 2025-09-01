"""
数据库迁移脚本 - 添加认证相关表
"""

from sqlalchemy import text

# 添加认证相关表的SQL
MIGRATION_SQL = """
-- 创建认证用户表
CREATE TABLE IF NOT EXISTS auth_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    real_name VARCHAR(100),
    display_name VARCHAR(100),
    email VARCHAR(254),
    employee_id VARCHAR(50),
    department VARCHAR(100),
    
    -- 认证相关字段
    password_hash VARCHAR(255),
    is_ldap_user BOOLEAN DEFAULT FALSE,
    ldap_dn VARCHAR(500),
    
    -- 权限字段
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    
    -- 时间字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_login DATETIME,
    login_count INT DEFAULT 0,
    
    -- 索引
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_employee_id (employee_id),
    INDEX idx_ldap_dn (ldap_dn),
    INDEX idx_is_active (is_active),
    INDEX idx_is_admin (is_admin)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='认证用户表';

-- 创建认证用户组表
CREATE TABLE IF NOT EXISTS auth_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- LDAP相关
    is_ldap_group BOOLEAN DEFAULT FALSE,
    ldap_dn VARCHAR(500),
    
    -- 权限配置
    permissions JSON,
    
    -- 状态字段
    is_active BOOLEAN DEFAULT TRUE,
    
    -- 时间字段
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_name (name),
    INDEX idx_display_name (display_name),
    INDEX idx_ldap_dn (ldap_dn),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='认证用户组表';

-- 创建用户组关联表
CREATE TABLE IF NOT EXISTS user_group_association (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES auth_groups(id) ON DELETE CASCADE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_group_id (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户组关联表';

-- 创建用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(500) NOT NULL,
    refresh_token VARCHAR(500),
    
    -- 会话信息
    client_ip VARCHAR(45),
    user_agent TEXT,
    
    -- 状态和时间
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES auth_users(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_user_id (user_id),
    INDEX idx_session_token (session_token),
    INDEX idx_refresh_token (refresh_token),
    INDEX idx_is_active (is_active),
    INDEX idx_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户会话表';

-- 创建默认管理员用户
INSERT IGNORE INTO auth_users (
    username, 
    real_name, 
    display_name, 
    email, 
    password_hash, 
    is_ldap_user, 
    is_active, 
    is_admin, 
    is_superuser
) VALUES (
    'admin', 
    '系统管理员', 
    '管理员', 
    'admin@company.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewA5L0eYwLCekOyG', -- 密码: admin123
    FALSE, 
    TRUE, 
    TRUE, 
    TRUE
);

-- 创建默认用户组
INSERT IGNORE INTO auth_groups (
    name, 
    display_name, 
    description, 
    permissions, 
    is_ldap_group, 
    is_active
) VALUES 
('administrators', '管理员组', '系统管理员组，拥有所有权限', 
 JSON_ARRAY('superuser', 'admin', 'user', 'system_settings', 'user_management', 'ip_management', 'network_management', 'data_export', 'data_import', 'data_delete'), 
 FALSE, TRUE),
('users', '普通用户组', '普通用户组，拥有基本查看权限', 
 JSON_ARRAY('user'), 
 FALSE, TRUE),
('ip_managers', 'IP管理员组', 'IP地址管理员组', 
 JSON_ARRAY('user', 'ip_management', 'network_management', 'data_export'), 
 FALSE, TRUE);

-- 将默认管理员添加到管理员组
INSERT IGNORE INTO user_group_association (user_id, group_id)
SELECT u.id, g.id 
FROM auth_users u, auth_groups g 
WHERE u.username = 'admin' AND g.name = 'administrators';
"""

def run_migration(db_session):
    """执行数据库迁移"""
    try:
        # 拆分SQL语句并逐个执行
        statements = MIGRATION_SQL.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement:  # 跳过空语句
                print(f"执行SQL: {statement[:100]}...")
                db_session.execute(text(statement))
        
        db_session.commit()
        print("数据库迁移完成!")
        
    except Exception as e:
        db_session.rollback()
        print(f"数据库迁移失败: {e}")
        raise

if __name__ == "__main__":
    # 如果直接运行此脚本，连接数据库并执行迁移
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from database.connection import SessionLocal
    
    db = SessionLocal()
    try:
        run_migration(db)
    finally:
        db.close()