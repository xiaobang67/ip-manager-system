-- 修复数据库字符集问题
-- 确保数据库和所有表都使用utf8mb4字符集

-- 设置数据库默认字符集
ALTER DATABASE ipam CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修复所有表的字符集
ALTER TABLE alert_history CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE alert_rules CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE audit_logs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE custom_field_values CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE custom_fields CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE departments CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE ip_addresses CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE ip_tags CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE subnet_tags CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE subnets CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE system_configs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE tags CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE search_history CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修复现有数据中的中文编码问题
UPDATE subnets SET 
    description = CASE 
        WHEN id = 1 THEN '办公网络 - 总部'
        WHEN id = 2 THEN '服务器网络 - 机房A'
        WHEN id = 3 THEN '开发环境网络'
        WHEN id = 4 THEN '测试环境网络'
        WHEN id = 5 THEN '访客网络'
        ELSE description
    END,
    location = CASE 
        WHEN id = 1 THEN '总部办公楼'
        WHEN id = 2 THEN '数据中心机房A'
        WHEN id = 3 THEN '开发部门'
        WHEN id = 4 THEN '测试环境'
        WHEN id = 5 THEN '访客区域'
        ELSE location
    END
WHERE id IN (1, 2, 3, 4, 5);

-- 修复用户表中的中文数据
UPDATE users SET 
    username = CASE 
        WHEN id = 1 THEN 'admin'
        ELSE username
    END,
    email = CASE 
        WHEN id = 1 THEN 'admin@ipam.local'
        ELSE email
    END
WHERE id = 1;

-- 修复其他可能存在中文编码问题的表
UPDATE custom_fields SET 
    field_name = REPLACE(REPLACE(REPLACE(field_name, 'Ã¥', ''), 'Â', ''), 'Æ', '')
WHERE field_name LIKE '%Ã%';

UPDATE tags SET 
    name = REPLACE(REPLACE(REPLACE(name, 'Ã¥', ''), 'Â', ''), 'Æ', '')
WHERE name LIKE '%Ã%';