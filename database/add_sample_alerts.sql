-- 添加示例警报数据
USE ipam;

-- 插入一些示例警报历史记录
INSERT INTO alert_history (rule_id, alert_message, severity, is_resolved, resolved_at, resolved_by, created_at) VALUES
(1, '办公网络(192.168.1.0/24)使用率已达到85%，建议关注IP地址分配情况', 'medium', FALSE, NULL, NULL, DATE_SUB(NOW(), INTERVAL 2 HOUR)),
(2, '服务器网络(192.168.2.0/24)使用率已达到92%，接近告警阈值', 'high', FALSE, NULL, NULL, DATE_SUB(NOW(), INTERVAL 1 HOUR)),
(3, '检测到IP地址冲突：192.168.1.100 同时被两个设备使用', 'critical', FALSE, NULL, NULL, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
(1, '办公网络(192.168.1.0/24)使用率已达到82%', 'medium', TRUE, DATE_SUB(NOW(), INTERVAL 1 DAY), 1, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(4, '开发环境网络(10.0.1.0/24)使用率已达到88%', 'medium', TRUE, DATE_SUB(NOW(), INTERVAL 3 HOUR), 1, DATE_SUB(NOW(), INTERVAL 6 HOUR)),
(5, '访客网络(192.168.100.0/24)使用率已达到75%', 'low', FALSE, NULL, NULL, DATE_SUB(NOW(), INTERVAL 4 HOUR)),
(2, '服务器网络(192.168.2.0/24)使用率已达到95%，已超过告警阈值', 'critical', TRUE, DATE_SUB(NOW(), INTERVAL 12 HOUR), 1, DATE_SUB(NOW(), INTERVAL 1 DAY)),
(3, '检测到MAC地址冲突：00:11:22:33:44:55 在多个IP地址中出现', 'high', FALSE, NULL, NULL, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(1, '办公网络(192.168.1.0/24)新增大量IP分配请求', 'low', TRUE, DATE_SUB(NOW(), INTERVAL 2 DAY), 2, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(4, '开发环境网络(10.0.1.0/24)检测到异常流量模式', 'medium', FALSE, NULL, NULL, DATE_SUB(NOW(), INTERVAL 5 DAY));

-- 显示插入的警报统计
SELECT 
    '警报数据插入完成' as status,
    COUNT(*) as total_alerts,
    SUM(CASE WHEN is_resolved = FALSE THEN 1 ELSE 0 END) as unresolved_alerts,
    SUM(CASE WHEN severity = 'critical' AND is_resolved = FALSE THEN 1 ELSE 0 END) as critical_unresolved
FROM alert_history;