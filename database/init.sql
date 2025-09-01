-- 企业IP地址管理系统数据库脚本
-- 创建日期: 2025-08-26

-- 创建数据库
CREATE DATABASE IF NOT EXISTS ip_management_system 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE ip_management_system;

-- 1. 部门表
CREATE TABLE departments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '部门名称',
    code VARCHAR(50) UNIQUE NOT NULL COMMENT '部门编码',
    parent_id INT NULL COMMENT '上级部门ID',
    description TEXT COMMENT '部门描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1 COMMENT '是否激活',
    INDEX idx_parent_id (parent_id),
    INDEX idx_code (code),
    FOREIGN KEY (parent_id) REFERENCES departments(id) ON DELETE SET NULL
) COMMENT='部门信息表';

-- 2. 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    real_name VARCHAR(100) NOT NULL COMMENT '真实姓名',
    email VARCHAR(100) UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) COMMENT '电话',
    department_id INT COMMENT '所属部门',
    employee_id VARCHAR(50) COMMENT '员工编号',
    position VARCHAR(100) COMMENT '职位',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1 COMMENT '是否激活',
    INDEX idx_username (username),
    INDEX idx_department_id (department_id),
    INDEX idx_employee_id (employee_id),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
) COMMENT='用户信息表';

-- 3. 网段表
CREATE TABLE network_segments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '网段名称',
    network VARCHAR(50) NOT NULL COMMENT '网络地址 (如: 192.168.1.0/24)',
    start_ip VARCHAR(15) NOT NULL COMMENT '起始IP地址',
    end_ip VARCHAR(15) NOT NULL COMMENT '结束IP地址',
    subnet_mask VARCHAR(15) NOT NULL COMMENT '子网掩码',
    gateway VARCHAR(15) COMMENT '网关地址',
    dns_servers JSON COMMENT 'DNS服务器列表',
    vlan_id INT COMMENT 'VLAN ID',
    purpose VARCHAR(200) COMMENT '用途说明',
    location VARCHAR(200) COMMENT '物理位置',
    responsible_department_id INT COMMENT '负责部门',
    responsible_user_id INT COMMENT '负责人',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1 COMMENT '是否激活',
    INDEX idx_network (network),
    INDEX idx_start_ip (start_ip),
    INDEX idx_end_ip (end_ip),
    INDEX idx_responsible_department (responsible_department_id),
    INDEX idx_responsible_user (responsible_user_id),
    FOREIGN KEY (responsible_department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (responsible_user_id) REFERENCES users(id) ON DELETE SET NULL
) COMMENT='网段信息表';

-- 4. IP地址表
CREATE TABLE ip_addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(15) NOT NULL COMMENT 'IP地址',
    network_segment_id INT NOT NULL COMMENT '所属网段',
    status ENUM('available', 'allocated', 'reserved', 'blacklisted') DEFAULT 'available' COMMENT 'IP状态',
    allocation_type ENUM('static', 'dhcp', 'reserved') COMMENT '分配类型',
    device_name VARCHAR(100) COMMENT '设备名称',
    device_type VARCHAR(50) COMMENT '设备类型 (服务器/工作站/打印机等)',
    mac_address VARCHAR(17) COMMENT 'MAC地址',
    hostname VARCHAR(100) COMMENT '主机名',
    os_type VARCHAR(50) COMMENT '操作系统',
    assigned_user_id INT COMMENT '分配给用户',
    assigned_department_id INT COMMENT '分配给部门',
    location VARCHAR(200) COMMENT '物理位置',
    purpose VARCHAR(500) COMMENT '用途说明',
    notes TEXT COMMENT '备注',
    allocated_at DATETIME COMMENT '分配时间',
    expires_at DATETIME COMMENT '到期时间',
    last_seen DATETIME COMMENT '最后检测时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_ip (ip_address),
    INDEX idx_ip_address (ip_address),
    INDEX idx_network_segment_id (network_segment_id),
    INDEX idx_status (status),
    INDEX idx_assigned_user_id (assigned_user_id),
    INDEX idx_assigned_department_id (assigned_department_id),
    INDEX idx_mac_address (mac_address),
    FOREIGN KEY (network_segment_id) REFERENCES network_segments(id) ON DELETE CASCADE,
    FOREIGN KEY (assigned_user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_department_id) REFERENCES departments(id) ON DELETE SET NULL
) COMMENT='IP地址信息表';

-- 5. 地址保留表
CREATE TABLE reserved_addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(15) NOT NULL COMMENT '保留的IP地址',
    network_segment_id INT NOT NULL COMMENT '所属网段',
    reserved_for VARCHAR(200) NOT NULL COMMENT '保留用途',
    reserved_by_user_id INT NOT NULL COMMENT '保留人',
    reserved_by_department_id INT COMMENT '保留部门',
    start_date DATE NOT NULL COMMENT '保留开始日期',
    end_date DATE COMMENT '保留结束日期',
    is_permanent TINYINT DEFAULT 0 COMMENT '是否永久保留',
    priority ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium' COMMENT '优先级',
    notes TEXT COMMENT '保留说明',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT DEFAULT 1 COMMENT '是否生效',
    INDEX idx_ip_address (ip_address),
    INDEX idx_network_segment_id (network_segment_id),
    INDEX idx_reserved_by_user_id (reserved_by_user_id),
    INDEX idx_reserved_by_department_id (reserved_by_department_id),
    INDEX idx_start_date (start_date),
    INDEX idx_end_date (end_date),
    FOREIGN KEY (network_segment_id) REFERENCES network_segments(id) ON DELETE CASCADE,
    FOREIGN KEY (reserved_by_user_id) REFERENCES users(id) ON DELETE RESTRICT,
    FOREIGN KEY (reserved_by_department_id) REFERENCES departments(id) ON DELETE SET NULL
) COMMENT='地址保留表';

-- 6. IP使用历史表 (可选，用于审计)
CREATE TABLE ip_usage_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(15) NOT NULL COMMENT 'IP地址',
    action ENUM('allocate', 'release', 'reserve', 'unreserve', 'modify') NOT NULL COMMENT '操作类型',
    old_status VARCHAR(50) COMMENT '原状态',
    new_status VARCHAR(50) COMMENT '新状态',
    user_id INT COMMENT '操作用户',
    department_id INT COMMENT '相关部门',
    device_info JSON COMMENT '设备信息',
    notes TEXT COMMENT '操作说明',
    operation_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ip_address (ip_address),
    INDEX idx_action (action),
    INDEX idx_operation_time (operation_time),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
) COMMENT='IP使用历史记录表';

-- 插入初始数据
-- 根部门
INSERT INTO departments (name, code, description) VALUES 
('总公司', 'ROOT', '公司根部门'),
('技术部', 'TECH', '技术开发部门'),
('运维部', 'OPS', '运维支持部门'),
('行政部', 'ADMIN', '行政管理部门');

-- 系统管理员用户
INSERT INTO users (username, real_name, email, department_id, position) VALUES 
('admin', '系统管理员', 'admin@company.com', 1, '系统管理员'),
('tech_lead', '技术主管', 'tech@company.com', 2, '技术主管'),
('ops_lead', '运维主管', 'ops@company.com', 3, '运维主管');

-- 示例网段
INSERT INTO network_segments (name, network, start_ip, end_ip, subnet_mask, gateway, purpose, responsible_department_id) VALUES 
('办公网段', '192.168.1.0/24', '192.168.1.1', '192.168.1.254', '255.255.255.0', '192.168.1.1', '办公区域网络', 2),
('服务器网段', '192.168.10.0/24', '192.168.10.1', '192.168.10.254', '255.255.255.0', '192.168.10.1', '服务器专用网络', 3),
('访客网段', '192.168.100.0/24', '192.168.100.1', '192.168.100.254', '255.255.255.0', '192.168.100.1', '访客网络', 4);