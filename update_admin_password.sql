-- 更新admin用户密码哈希
UPDATE auth_users SET password_hash = '$2b$12$S9MzZAALgAJje.52hTo67.0cDChtofejbt6RUcl146zMABkIF6DNi' WHERE username = 'admin';

-- 验证更新
SELECT username, password_hash FROM auth_users WHERE username = 'admin';