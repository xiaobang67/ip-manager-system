-- Database initialization script for IPAM system
-- This file will be executed when MySQL container starts

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS ipam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant permissions to ipam_user
GRANT ALL PRIVILEGES ON ipam.* TO 'ipam_user'@'%';
FLUSH PRIVILEGES;

-- Use the database
USE ipam;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'manager', 'user', 'readonly') DEFAULT 'user',
    theme ENUM('light', 'dark') DEFAULT 'light',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_active (is_active)
);

-- 网段表
CREATE TABLE IF NOT EXISTS subnets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    network VARCHAR(18) NOT NULL,  -- CIDR格式，如 192.168.1.0/24
    netmask VARCHAR(15) NOT NULL,
    gateway VARCHAR(15),
    description TEXT,
    vlan_id INT,
    location VARCHAR(100),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE KEY unique_network (network),
    INDEX idx_network (network),
    INDEX idx_vlan (vlan_id),
    INDEX idx_created_by (created_by)
);

-- IP地址表
CREATE TABLE IF NOT EXISTS ip_addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(15) NOT NULL,
    subnet_id INT NOT NULL,
    status ENUM('available', 'allocated', 'reserved', 'conflict') DEFAULT 'available',
    mac_address VARCHAR(17),
    hostname VARCHAR(255),
    device_type VARCHAR(50),
    location VARCHAR(100),
    assigned_to VARCHAR(100),
    description TEXT,
    allocated_at TIMESTAMP NULL,
    allocated_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (subnet_id) REFERENCES subnets(id) ON DELETE CASCADE,
    FOREIGN KEY (allocated_by) REFERENCES users(id),
    UNIQUE KEY unique_ip (ip_address),
    INDEX idx_subnet_status (subnet_id, status),
    INDEX idx_ip_status (ip_address, status),
    INDEX idx_hostname (hostname),
    INDEX idx_mac_address (mac_address)
);

-- 自定义字段表
CREATE TABLE IF NOT EXISTS custom_fields (
    id INT PRIMARY KEY AUTO_INCREMENT,
    entity_type ENUM('ip', 'subnet') NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    field_type ENUM('text', 'number', 'date', 'select') NOT NULL,
    field_options JSON,  -- 用于select类型的选项
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_entity_type (entity_type),
    INDEX idx_field_name (field_name)
);

-- 自定义字段值表
CREATE TABLE IF NOT EXISTS custom_field_values (
    id INT PRIMARY KEY AUTO_INCREMENT,
    field_id INT NOT NULL,
    entity_id INT NOT NULL,
    entity_type ENUM('ip', 'subnet') NOT NULL,
    field_value TEXT,
    FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
    UNIQUE KEY unique_field_entity (field_id, entity_id, entity_type),
    INDEX idx_entity (entity_type, entity_id)
);

-- 标签表
CREATE TABLE IF NOT EXISTS tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#007bff',  -- 十六进制颜色
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- IP地址标签关联表
CREATE TABLE IF NOT EXISTS ip_tags (
    ip_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (ip_id, tag_id),
    FOREIGN KEY (ip_id) REFERENCES ip_addresses(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 网段标签关联表
CREATE TABLE IF NOT EXISTS subnet_tags (
    subnet_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (subnet_id, tag_id),
    FOREIGN KEY (subnet_id) REFERENCES subnets(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 操作日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE, ALLOCATE, RELEASE
    entity_type VARCHAR(20) NOT NULL,  -- ip, subnet, user
    entity_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),  -- 操作者IP
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_action (user_id, action),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created_at (created_at),
    INDEX idx_action (action)
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id),
    INDEX idx_config_key (config_key)
);

-- 警报规则表
CREATE TABLE IF NOT EXISTS alert_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    rule_type ENUM('utilization', 'conflict', 'expiry') NOT NULL,
    threshold_value DECIMAL(5,2),  -- 阈值，如使用率80%
    subnet_id INT,  -- 可选，针对特定网段的规则
    is_active BOOLEAN DEFAULT TRUE,
    notification_emails TEXT,  -- JSON格式的邮箱列表
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subnet_id) REFERENCES subnets(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_rule_type (rule_type),
    INDEX idx_active (is_active)
);

-- 警报历史表
CREATE TABLE IF NOT EXISTS alert_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT NOT NULL,
    alert_message TEXT NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    resolved_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    INDEX idx_rule_created (rule_id, created_at),
    INDEX idx_severity_resolved (severity, is_resolved)
);

-- 设备类型表
CREATE TABLE IF NOT EXISTS device_types (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    code VARCHAR(30) UNIQUE NOT NULL,
    category ENUM('computing', 'network', 'storage', 'security', 'office', 'other') DEFAULT 'other',
    status ENUM('active', 'inactive') DEFAULT 'active',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_code (code),
    INDEX idx_category (category),
    INDEX idx_status (status),
    INDEX idx_name (name)
);