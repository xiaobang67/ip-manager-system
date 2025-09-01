-- 创建auth_users表
CREATE TABLE IF NOT EXISTS auth_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    real_name VARCHAR(100),
    display_name VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    employee_id VARCHAR(50),
    password_hash VARCHAR(128),
    is_ldap_user BOOLEAN DEFAULT FALSE,
    ldap_dn VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    last_login DATETIME,
    login_count INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 初始化管理员用户
INSERT INTO auth_users (
    username, 
    display_name, 
    password_hash, 
    is_ldap_user, 
    is_active, 
    is_admin, 
    is_superuser, 
    created_at, 
    updated_at
) 
VALUES (
    'admin', 
    '系统管理员', 
    '$2b$12$jmukJDXzlm76K8NilBWj5Om8LX0YtvW.ZMSWCvEj2a2UC0ogdSO/u', 
    0, 
    1, 
    1, 
    1, 
    NOW(), 
    NOW()
);

-- 创建auth_groups表
CREATE TABLE IF NOT EXISTS auth_groups (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(100),
    description TEXT,
    is_ldap_group BOOLEAN DEFAULT FALSE,
    ldap_dn VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 创建user_group_associations表
CREATE TABLE IF NOT EXISTS user_group_associations (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    PRIMARY KEY (user_id, group_id),
    CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES auth_users(id),
    CONSTRAINT fk_group_id FOREIGN KEY (group_id) REFERENCES auth_groups(id)
);

-- 创建user_sessions表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    refresh_token VARCHAR(255) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT fk_session_user_id FOREIGN KEY (user_id) REFERENCES auth_users(id)
);