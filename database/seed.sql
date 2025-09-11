-- IPAM系统种子数据脚本
-- 用于初始化系统的基础数据

USE ipam;

-- 禁用外键检查
SET FOREIGN_KEY_CHECKS = 0;

-- ===========================================
-- 创建默认管理员用户
-- ===========================================
INSERT INTO users (id, username, password_hash, email, role, theme, is_active, created_at, updated_at) VALUES
(1, 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'admin@example.com', 'admin', 'light', TRUE, NOW(), NOW()),
(2, 'manager', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'manager@example.com', 'manager', 'light', TRUE, NOW(), NOW()),
(3, 'user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.PmvlG.', 'user@example.com', 'user', 'light', TRUE, NOW(), NOW());

-- 注意：上述密码哈希对应的明文密码都是 'password123'
-- 生产环境中请务必修改默认密码

-- ===========================================
-- 创建示例网段
-- ===========================================
INSERT INTO subnets (id, network, netmask, gateway, description, vlan_id, location, created_by, created_at, updated_at) VALUES
(1, '192.168.1.0/24', '255.255.255.0', '192.168.1.1', '办公网络 - 总部', 100, '总部办公楼', 1, NOW(), NOW()),
(2, '192.168.2.0/24', '255.255.255.0', '192.168.2.1', '服务器网络 - 机房A', 200, '数据中心机房A', 1, NOW(), NOW()),
(3, '10.0.1.0/24', '255.255.255.0', '10.0.1.1', '开发环境网络', 300, '开发部门', 1, NOW(), NOW()),
(4, '172.16.1.0/24', '255.255.255.0', '172.16.1.1', '测试环境网络', 400, '测试环境', 1, NOW(), NOW()),
(5, '192.168.100.0/24', '255.255.255.0', '192.168.100.1', '访客网络', 500, '访客区域', 1, NOW(), NOW());

-- ===========================================
-- 创建示例IP地址
-- ===========================================

-- 办公网络IP地址 (192.168.1.0/24)
INSERT INTO ip_addresses (ip_address, subnet_id, status, mac_address, hostname, device_type, location, assigned_to, description, allocated_at, allocated_by, created_at, updated_at) VALUES
-- 网关和基础设施
('192.168.1.1', 1, 'reserved', NULL, 'gateway', 'router', '总部办公楼', '网络管理员', '网关路由器', NOW(), 1, NOW(), NOW()),
('192.168.1.2', 1, 'allocated', '00:11:22:33:44:01', 'dns-server', 'server', '总部办公楼', 'IT部门', 'DNS服务器', NOW(), 1, NOW(), NOW()),
('192.168.1.3', 1, 'allocated', '00:11:22:33:44:02', 'dhcp-server', 'server', '总部办公楼', 'IT部门', 'DHCP服务器', NOW(), 1, NOW(), NOW()),

-- 办公设备
('192.168.1.10', 1, 'allocated', '00:11:22:33:44:10', 'pc-001', 'desktop', '总部办公楼', '张三', '财务部电脑', NOW(), 1, NOW(), NOW()),
('192.168.1.11', 1, 'allocated', '00:11:22:33:44:11', 'pc-002', 'desktop', '总部办公楼', '李四', '人事部电脑', NOW(), 1, NOW(), NOW()),
('192.168.1.12', 1, 'allocated', '00:11:22:33:44:12', 'laptop-001', 'laptop', '总部办公楼', '王五', '销售部笔记本', NOW(), 1, NOW(), NOW()),

-- 打印机和其他设备
('192.168.1.20', 1, 'allocated', '00:11:22:33:44:20', 'printer-001', 'printer', '总部办公楼', 'IT部门', '办公室打印机', NOW(), 1, NOW(), NOW()),
('192.168.1.21', 1, 'allocated', '00:11:22:33:44:21', 'scanner-001', 'scanner', '总部办公楼', 'IT部门', '文档扫描仪', NOW(), 1, NOW(), NOW()),

-- 预留IP
('192.168.1.50', 1, 'reserved', NULL, NULL, NULL, '总部办公楼', 'IT部门', '为新员工预留', NULL, 1, NOW(), NOW()),
('192.168.1.51', 1, 'reserved', NULL, NULL, NULL, '总部办公楼', 'IT部门', '为新设备预留', NULL, 1, NOW(), NOW());

-- 服务器网络IP地址 (192.168.2.0/24)
INSERT INTO ip_addresses (ip_address, subnet_id, status, mac_address, hostname, device_type, location, assigned_to, description, allocated_at, allocated_by, created_at, updated_at) VALUES
-- 网关
('192.168.2.1', 2, 'reserved', NULL, 'srv-gateway', 'router', '数据中心机房A', '网络管理员', '服务器网关', NOW(), 1, NOW(), NOW()),

-- 核心服务器
('192.168.2.10', 2, 'allocated', '00:22:33:44:55:10', 'web-server-01', 'server', '数据中心机房A', 'IT部门', 'Web服务器主节点', NOW(), 1, NOW(), NOW()),
('192.168.2.11', 2, 'allocated', '00:22:33:44:55:11', 'web-server-02', 'server', '数据中心机房A', 'IT部门', 'Web服务器备节点', NOW(), 1, NOW(), NOW()),
('192.168.2.20', 2, 'allocated', '00:22:33:44:55:20', 'db-server-01', 'server', '数据中心机房A', 'IT部门', '数据库服务器主节点', NOW(), 1, NOW(), NOW()),
('192.168.2.21', 2, 'allocated', '00:22:33:44:55:21', 'db-server-02', 'server', '数据中心机房A', 'IT部门', '数据库服务器从节点', NOW(), 1, NOW(), NOW()),
('192.168.2.30', 2, 'allocated', '00:22:33:44:55:30', 'app-server-01', 'server', '数据中心机房A', 'IT部门', '应用服务器', NOW(), 1, NOW(), NOW()),
('192.168.2.40', 2, 'allocated', '00:22:33:44:55:40', 'cache-server-01', 'server', '数据中心机房A', 'IT部门', 'Redis缓存服务器', NOW(), 1, NOW(), NOW()),
('192.168.2.50', 2, 'allocated', '00:22:33:44:55:50', 'monitor-server', 'server', '数据中心机房A', 'IT部门', '监控服务器', NOW(), 1, NOW(), NOW());

-- 开发环境IP地址 (10.0.1.0/24)
INSERT INTO ip_addresses (ip_address, subnet_id, status, mac_address, hostname, device_type, location, assigned_to, description, allocated_at, allocated_by, created_at, updated_at) VALUES
('10.0.1.1', 3, 'reserved', NULL, 'dev-gateway', 'router', '开发部门', '网络管理员', '开发环境网关', NOW(), 1, NOW(), NOW()),
('10.0.1.10', 3, 'allocated', '00:33:44:55:66:10', 'dev-server-01', 'server', '开发部门', '开发团队', '开发服务器', NOW(), 1, NOW(), NOW()),
('10.0.1.20', 3, 'allocated', '00:33:44:55:66:20', 'dev-db', 'server', '开发部门', '开发团队', '开发数据库', NOW(), 1, NOW(), NOW()),
('10.0.1.100', 3, 'allocated', '00:33:44:55:66:30', 'dev-pc-001', 'desktop', '开发部门', '开发者A', '开发工作站', NOW(), 1, NOW(), NOW()),
('10.0.1.101', 3, 'allocated', '00:33:44:55:66:31', 'dev-pc-002', 'desktop', '开发部门', '开发者B', '开发工作站', NOW(), 1, NOW(), NOW());

-- 测试环境IP地址 (172.16.1.0/24)
INSERT INTO ip_addresses (ip_address, subnet_id, status, mac_address, hostname, device_type, location, assigned_to, description, allocated_at, allocated_by, created_at, updated_at) VALUES
('172.16.1.1', 4, 'reserved', NULL, 'test-gateway', 'router', '测试环境', '网络管理员', '测试环境网关', NOW(), 1, NOW(), NOW()),
('172.16.1.10', 4, 'allocated', '00:44:55:66:77:10', 'test-server-01', 'server', '测试环境', '测试团队', '测试服务器', NOW(), 1, NOW(), NOW()),
('172.16.1.20', 4, 'allocated', '00:44:55:66:77:20', 'test-db', 'server', '测试环境', '测试团队', '测试数据库', NOW(), 1, NOW(), NOW());

-- 访客网络IP地址 (192.168.100.0/24) - 大部分保持可用状态
INSERT INTO ip_addresses (ip_address, subnet_id, status, mac_address, hostname, device_type, location, assigned_to, description, allocated_at, allocated_by, created_at, updated_at) VALUES
('192.168.100.1', 5, 'reserved', NULL, 'guest-gateway', 'router', '访客区域', '网络管理员', '访客网络网关', NOW(), 1, NOW(), NOW()),
('192.168.100.10', 5, 'allocated', '00:55:66:77:88:10', 'guest-ap-01', 'access_point', '访客区域', 'IT部门', '访客无线接入点', NOW(), 1, NOW(), NOW());

-- ===========================================
-- 创建设备类型
-- ===========================================
INSERT INTO device_types (id, name, code, category, status, description, created_at, updated_at) VALUES
(1, '服务器', 'server', 'computing', 'active', '各类服务器设备，包括Web服务器、数据库服务器、应用服务器等', NOW(), NOW()),
(2, '工作站', 'workstation', 'computing', 'active', '员工办公用台式机和工作站', NOW(), NOW()),
(3, '笔记本电脑', 'laptop', 'computing', 'active', '便携式笔记本电脑设备', NOW(), NOW()),
(4, '台式机', 'desktop', 'computing', 'active', '办公用台式计算机', NOW(), NOW()),
(5, '网络交换机', 'switch', 'network', 'active', '网络交换设备，用于连接网络设备', NOW(), NOW()),
(6, '路由器', 'router', 'network', 'active', '网络路由设备，用于网络间的数据转发', NOW(), NOW()),
(7, '防火墙', 'firewall', 'security', 'active', '网络安全防护设备', NOW(), NOW()),
(8, '无线接入点', 'access_point', 'network', 'active', '无线网络接入设备', NOW(), NOW()),
(9, '打印机', 'printer', 'office', 'active', '办公打印设备', NOW(), NOW()),
(10, '扫描仪', 'scanner', 'office', 'active', '文档扫描设备', NOW(), NOW()),
(11, '存储设备', 'storage', 'storage', 'active', 'NAS、SAN等存储设备', NOW(), NOW()),
(12, '监控摄像头', 'camera', 'security', 'active', '安防监控摄像设备', NOW(), NOW()),
(13, '网络附加存储', 'nas', 'storage', 'active', '网络附加存储设备', NOW(), NOW()),
(14, '负载均衡器', 'load_balancer', 'network', 'active', '负载均衡设备', NOW(), NOW()),
(15, '其他设备', 'other', 'other', 'active', '其他未分类的网络设备', NOW(), NOW());

-- ===========================================
-- 创建标签
-- ===========================================
INSERT INTO tags (id, name, color, description, created_at) VALUES
(1, 'production', '#dc3545', '生产环境', NOW()),
(2, 'development', '#28a745', '开发环境', NOW()),
(3, 'testing', '#ffc107', '测试环境', NOW()),
(4, 'office', '#007bff', '办公设备', NOW()),
(5, 'server', '#6f42c1', '服务器设备', NOW()),
(6, 'network', '#fd7e14', '网络设备', NOW()),
(7, 'critical', '#dc3545', '关键设备', NOW()),
(8, 'guest', '#6c757d', '访客设备', NOW()),
(9, 'printer', '#20c997', '打印设备', NOW()),
(10, 'database', '#e83e8c', '数据库相关', NOW());

-- ===========================================
-- 关联IP地址和标签
-- ===========================================
INSERT INTO ip_tags (ip_id, tag_id) VALUES
-- 生产服务器标签
(10, 1), (10, 5), (10, 7),  -- web-server-01
(11, 1), (11, 5),           -- web-server-02
(12, 1), (12, 5), (12, 7), (12, 10), -- db-server-01
(13, 1), (13, 5), (13, 10), -- db-server-02
(14, 1), (14, 5),           -- app-server-01
(15, 1), (15, 5),           -- cache-server-01
(16, 1), (16, 5),           -- monitor-server

-- 办公设备标签
(4, 4),   -- pc-001
(5, 4),   -- pc-002
(6, 4),   -- laptop-001
(7, 4), (7, 9),   -- printer-001
(8, 4),   -- scanner-001

-- 网络设备标签
(1, 6), (1, 7),   -- gateway
(2, 5), (2, 6),   -- dns-server
(3, 5), (3, 6),   -- dhcp-server

-- 开发环境标签
(18, 2), (18, 5), -- dev-server-01
(19, 2), (19, 5), (19, 10), -- dev-db
(20, 2), (20, 4), -- dev-pc-001
(21, 2), (21, 4), -- dev-pc-002

-- 测试环境标签
(23, 3), (23, 5), -- test-server-01
(24, 3), (24, 5), (24, 10), -- test-db

-- 访客网络标签
(26, 8), (26, 6); -- guest-ap-01

-- ===========================================
-- 关联网段和标签
-- ===========================================
INSERT INTO subnet_tags (subnet_id, tag_id) VALUES
(1, 4),   -- 办公网络
(2, 1), (2, 5), (2, 7), -- 服务器网络
(3, 2),   -- 开发环境网络
(4, 3),   -- 测试环境网络
(5, 8);   -- 访客网络

-- ===========================================
-- 创建自定义字段
-- ===========================================
INSERT INTO custom_fields (id, entity_type, field_name, field_type, field_options, is_required, created_at) VALUES
(1, 'ip', 'department', 'select', '["IT部门", "财务部", "人事部", "销售部", "开发部", "测试部"]', FALSE, NOW()),
(2, 'ip', 'contact_person', 'text', NULL, FALSE, NOW()),
(3, 'ip', 'purchase_date', 'date', NULL, FALSE, NOW()),
(4, 'ip', 'warranty_expiry', 'date', NULL, FALSE, NOW()),
(5, 'ip', 'asset_number', 'text', NULL, FALSE, NOW()),
(6, 'subnet', 'business_unit', 'select', '["总部", "分公司A", "分公司B", "数据中心"]', FALSE, NOW()),
(7, 'subnet', 'cost_center', 'text', NULL, FALSE, NOW()),
(8, 'subnet', 'security_level', 'select', '["公开", "内部", "机密", "绝密"]', TRUE, NOW());

-- ===========================================
-- 填充自定义字段值
-- ===========================================
INSERT INTO custom_field_values (field_id, entity_id, entity_type, field_value) VALUES
-- IP地址自定义字段值
(1, 4, 'ip', 'IT部门'),    -- pc-001 部门
(2, 4, 'ip', '张三'),      -- pc-001 联系人
(5, 4, 'ip', 'IT-2024-001'), -- pc-001 资产编号

(1, 5, 'ip', '人事部'),    -- pc-002 部门
(2, 5, 'ip', '李四'),      -- pc-002 联系人
(5, 5, 'ip', 'HR-2024-001'), -- pc-002 资产编号

(1, 6, 'ip', '销售部'),    -- laptop-001 部门
(2, 6, 'ip', '王五'),      -- laptop-001 联系人
(5, 6, 'ip', 'SALES-2024-001'), -- laptop-001 资产编号

-- 网段自定义字段值
(6, 1, 'subnet', '总部'),     -- 办公网络 业务单元
(7, 1, 'subnet', 'CC-001'),  -- 办公网络 成本中心
(8, 1, 'subnet', '内部'),     -- 办公网络 安全级别

(6, 2, 'subnet', '数据中心'), -- 服务器网络 业务单元
(7, 2, 'subnet', 'CC-002'),  -- 服务器网络 成本中心
(8, 2, 'subnet', '机密'),     -- 服务器网络 安全级别

(6, 3, 'subnet', '总部'),     -- 开发环境网络 业务单元
(7, 3, 'subnet', 'CC-003'),  -- 开发环境网络 成本中心
(8, 3, 'subnet', '内部'),     -- 开发环境网络 安全级别

(6, 5, 'subnet', '总部'),     -- 访客网络 业务单元
(7, 5, 'subnet', 'CC-005'),  -- 访客网络 成本中心
(8, 5, 'subnet', '公开');     -- 访客网络 安全级别

-- ===========================================
-- 创建系统配置
-- ===========================================
INSERT INTO system_configs (config_key, config_value, description, updated_by, updated_at) VALUES
('system_name', 'IPAM企业IP地址管理系统', '系统名称', 1, NOW()),
('system_version', '1.0.0', '系统版本', 1, NOW()),
('default_theme', 'light', '默认主题', 1, NOW()),
('session_timeout', '3600', '会话超时时间（秒）', 1, NOW()),
('max_login_attempts', '5', '最大登录尝试次数', 1, NOW()),
('backup_retention_days', '30', '备份保留天数', 1, NOW()),
('alert_email', 'admin@example.com', '告警邮箱', 1, NOW()),
('smtp_host', 'smtp.example.com', 'SMTP服务器', 1, NOW()),
('smtp_port', '587', 'SMTP端口', 1, NOW()),
('smtp_user', 'alerts@example.com', 'SMTP用户名', 1, NOW()),
('enable_audit_log', 'true', '启用审计日志', 1, NOW()),
('ip_conflict_check', 'true', '启用IP冲突检测', 1, NOW()),
('auto_generate_ips', 'true', '自动生成IP地址', 1, NOW()),
('default_subnet_mask', '255.255.255.0', '默认子网掩码', 1, NOW()),
('pagination_size', '50', '默认分页大小', 1, NOW());

-- ===========================================
-- 创建告警规则
-- ===========================================
INSERT INTO alert_rules (id, name, rule_type, threshold_value, subnet_id, is_active, notification_emails, created_by, created_at) VALUES
(1, '办公网络使用率告警', 'utilization', 80.00, 1, TRUE, '["admin@example.com", "network@example.com"]', 1, NOW()),
(2, '服务器网络使用率告警', 'utilization', 90.00, 2, TRUE, '["admin@example.com", "ops@example.com"]', 1, NOW()),
(3, '全局IP冲突告警', 'conflict', NULL, NULL, TRUE, '["admin@example.com", "security@example.com"]', 1, NOW()),
(4, '开发环境使用率告警', 'utilization', 85.00, 3, TRUE, '["dev@example.com"]', 1, NOW()),
(5, '访客网络使用率告警', 'utilization', 70.00, 5, TRUE, '["admin@example.com"]', 1, NOW());

-- ===========================================
-- 创建示例审计日志
-- ===========================================
INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values, new_values, ip_address, user_agent, created_at) VALUES
(1, 'CREATE', 'subnet', 1, NULL, '{"network": "192.168.1.0/24", "description": "办公网络 - 总部"}', '192.168.1.10', 'Mozilla/5.0 (Admin Setup)', DATE_SUB(NOW(), INTERVAL 30 DAY)),
(1, 'CREATE', 'subnet', 2, NULL, '{"network": "192.168.2.0/24", "description": "服务器网络 - 机房A"}', '192.168.1.10', 'Mozilla/5.0 (Admin Setup)', DATE_SUB(NOW(), INTERVAL 29 DAY)),
(1, 'ALLOCATE', 'ip', 10, '{"status": "available"}', '{"status": "allocated", "hostname": "web-server-01"}', '192.168.1.10', 'Mozilla/5.0 (Admin Setup)', DATE_SUB(NOW(), INTERVAL 25 DAY)),
(1, 'ALLOCATE', 'ip', 12, '{"status": "available"}', '{"status": "allocated", "hostname": "db-server-01"}', '192.168.1.10', 'Mozilla/5.0 (Admin Setup)', DATE_SUB(NOW(), INTERVAL 24 DAY)),
(2, 'ALLOCATE', 'ip', 4, '{"status": "available"}', '{"status": "allocated", "hostname": "pc-001", "assigned_to": "张三"}', '192.168.1.11', 'Mozilla/5.0 (Manager)', DATE_SUB(NOW(), INTERVAL 20 DAY)),
(2, 'ALLOCATE', 'ip', 5, '{"status": "available"}', '{"status": "allocated", "hostname": "pc-002", "assigned_to": "李四"}', '192.168.1.11', 'Mozilla/5.0 (Manager)', DATE_SUB(NOW(), INTERVAL 19 DAY)),
(1, 'RESERVE', 'ip', 9, '{"status": "available"}', '{"status": "reserved", "description": "为新员工预留"}', '192.168.1.10', 'Mozilla/5.0 (Admin)', DATE_SUB(NOW(), INTERVAL 10 DAY)),
(1, 'CREATE', 'user', 2, NULL, '{"username": "manager", "role": "manager"}', '192.168.1.10', 'Mozilla/5.0 (Admin)', DATE_SUB(NOW(), INTERVAL 15 DAY)),
(1, 'CREATE', 'user', 3, NULL, '{"username": "user", "role": "user"}', '192.168.1.10', 'Mozilla/5.0 (Admin)', DATE_SUB(NOW(), INTERVAL 14 DAY));

-- 启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- ===========================================
-- 创建视图和存储过程
-- ===========================================

-- 创建IP地址统计视图
CREATE VIEW ip_statistics AS
SELECT 
    s.id as subnet_id,
    s.network,
    s.description as subnet_description,
    COUNT(ip.id) as total_ips,
    SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) as allocated_ips,
    SUM(CASE WHEN ip.status = 'available' THEN 1 ELSE 0 END) as available_ips,
    SUM(CASE WHEN ip.status = 'reserved' THEN 1 ELSE 0 END) as reserved_ips,
    SUM(CASE WHEN ip.status = 'conflict' THEN 1 ELSE 0 END) as conflict_ips,
    ROUND(
        (SUM(CASE WHEN ip.status = 'allocated' THEN 1 ELSE 0 END) / COUNT(ip.id)) * 100, 
        2
    ) as utilization_percentage
FROM subnets s
LEFT JOIN ip_addresses ip ON s.id = ip.subnet_id
GROUP BY s.id, s.network, s.description;

-- 创建用户活动统计视图
CREATE VIEW user_activity_stats AS
SELECT 
    u.id as user_id,
    u.username,
    u.role,
    COUNT(al.id) as total_actions,
    SUM(CASE WHEN al.action = 'ALLOCATE' THEN 1 ELSE 0 END) as allocate_count,
    SUM(CASE WHEN al.action = 'RELEASE' THEN 1 ELSE 0 END) as release_count,
    SUM(CASE WHEN al.action = 'RESERVE' THEN 1 ELSE 0 END) as reserve_count,
    MAX(al.created_at) as last_activity
FROM users u
LEFT JOIN audit_logs al ON u.id = al.user_id
GROUP BY u.id, u.username, u.role;

-- 创建获取可用IP地址的存储过程
DELIMITER //
CREATE PROCEDURE GetAvailableIPs(IN subnet_id_param INT, IN limit_param INT)
BEGIN
    SELECT ip_address, id
    FROM ip_addresses 
    WHERE subnet_id = subnet_id_param 
    AND status = 'available'
    ORDER BY INET_ATON(ip_address)
    LIMIT limit_param;
END //
DELIMITER ;

-- 创建IP地址分配存储过程
DELIMITER //
CREATE PROCEDURE AllocateIP(
    IN ip_id_param INT,
    IN user_id_param INT,
    IN hostname_param VARCHAR(255),
    IN mac_address_param VARCHAR(17),
    IN device_type_param VARCHAR(50),
    IN assigned_to_param VARCHAR(100),
    IN description_param TEXT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- 更新IP地址状态
    UPDATE ip_addresses 
    SET 
        status = 'allocated',
        hostname = hostname_param,
        mac_address = mac_address_param,
        device_type = device_type_param,
        assigned_to = assigned_to_param,
        description = description_param,
        allocated_at = NOW(),
        allocated_by = user_id_param,
        updated_at = NOW()
    WHERE id = ip_id_param AND status = 'available';
    
    -- 检查是否成功更新
    IF ROW_COUNT() = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'IP地址不可用或不存在';
    END IF;
    
    -- 记录审计日志
    INSERT INTO audit_logs (user_id, action, entity_type, entity_id, old_values, new_values, created_at)
    VALUES (
        user_id_param, 
        'ALLOCATE', 
        'ip', 
        ip_id_param,
        '{"status": "available"}',
        JSON_OBJECT(
            'status', 'allocated',
            'hostname', hostname_param,
            'assigned_to', assigned_to_param
        ),
        NOW()
    );
    
    COMMIT;
END //
DELIMITER ;

-- ===========================================
-- 创建索引优化查询性能
-- ===========================================

-- IP地址相关索引
CREATE INDEX idx_ip_subnet_status ON ip_addresses(subnet_id, status);
CREATE INDEX idx_ip_address_status ON ip_addresses(ip_address, status);
CREATE INDEX idx_ip_hostname ON ip_addresses(hostname);
CREATE INDEX idx_ip_mac_address ON ip_addresses(mac_address);
CREATE INDEX idx_ip_allocated_at ON ip_addresses(allocated_at);

-- 审计日志索引
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_action_time ON audit_logs(action, created_at DESC);

-- 网段相关索引
CREATE INDEX idx_subnet_network ON subnets(network);
CREATE INDEX idx_subnet_vlan ON subnets(vlan_id);

-- 用户相关索引
CREATE INDEX idx_user_username ON users(username);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_role_active ON users(role, is_active);

-- 标签相关索引
CREATE INDEX idx_tag_name ON tags(name);

-- 全文搜索索引
CREATE FULLTEXT INDEX idx_ip_search ON ip_addresses(hostname, description, assigned_to);
CREATE FULLTEXT INDEX idx_subnet_search ON subnets(description, location);

-- ===========================================
-- 插入完成提示
-- ===========================================
INSERT INTO system_configs (config_key, config_value, description, updated_by, updated_at) VALUES
('seed_data_version', '1.0.0', '种子数据版本', 1, NOW()),
('seed_data_created', NOW(), '种子数据创建时间', 1, NOW());

-- 显示统计信息
SELECT 
    '数据初始化完成' as status,
    (SELECT COUNT(*) FROM users) as users_count,
    (SELECT COUNT(*) FROM subnets) as subnets_count,
    (SELECT COUNT(*) FROM ip_addresses) as ip_addresses_count,
    (SELECT COUNT(*) FROM tags) as tags_count,
    (SELECT COUNT(*) FROM custom_fields) as custom_fields_count,
    (SELECT COUNT(*) FROM audit_logs) as audit_logs_count;