# IPAM系统配置指南

## 概述

本文档详细介绍了IPAM（IP地址管理）系统的各项配置选项和最佳实践。

## 环境配置

### 1. 环境变量配置

#### 1.1 基础配置 (.env.prod)

```bash
# ===========================================
# 数据库配置
# ===========================================
# MySQL root用户密码（强密码，包含大小写字母、数字、特殊字符）
MYSQL_ROOT_PASSWORD=MyStr0ng!R00tP@ssw0rd

# 应用数据库用户密码
MYSQL_PASSWORD=MyStr0ng!App!P@ssw0rd

# 数据库连接URL（通常不需要修改）
DATABASE_URL=mysql+pymysql://ipam_user:${MYSQL_PASSWORD}@mysql:3306/ipam_db

# ===========================================
# 应用安全配置
# ===========================================
# JWT密钥（用于用户认证，必须是随机字符串）
JWT_SECRET_KEY=your-super-secret-jwt-key-here-make-it-long-and-random

# JWT过期时间（秒）
JWT_EXPIRATION_TIME=3600

# 密码加密轮数
BCRYPT_ROUNDS=12

# ===========================================
# 跨域配置
# ===========================================
# 允许的前端域名（多个域名用逗号分隔）
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,http://localhost:3000

# ===========================================
# Redis配置
# ===========================================
# Redis连接URL
REDIS_URL=redis://redis:6379/0

# Redis密码（可选）
REDIS_PASSWORD=

# ===========================================
# 监控配置
# ===========================================
# Grafana管理员密码
GRAFANA_PASSWORD=MyStr0ng!Gr@f@n@P@ssw0rd

# Prometheus数据保留时间（天）
PROMETHEUS_RETENTION_DAYS=15

# ===========================================
# 备份配置
# ===========================================
# 备份保留天数
BACKUP_RETENTION_DAYS=30

# 备份存储路径
BACKUP_PATH=/app/backups

# ===========================================
# 告警配置
# ===========================================
# 告警邮箱
ALERT_EMAIL=admin@yourdomain.com

# SMTP服务器配置
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=alerts@yourdomain.com
SMTP_PASSWORD=smtp_password
SMTP_TLS=true

# ===========================================
# 日志配置
# ===========================================
# 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE_PATH=/app/logs

# 日志文件大小限制（MB）
LOG_MAX_SIZE=100

# 日志文件保留数量
LOG_BACKUP_COUNT=10

# ===========================================
# 性能配置
# ===========================================
# API工作进程数（建议设置为CPU核心数）
WORKERS=4

# 数据库连接池大小
DB_POOL_SIZE=20

# 数据库连接池最大溢出
DB_MAX_OVERFLOW=30

# Redis连接池大小
REDIS_POOL_SIZE=10

# ===========================================
# 功能开关
# ===========================================
# 启用调试模式（生产环境应设置为false）
DEBUG=false

# 启用API文档（生产环境可设置为false）
ENABLE_DOCS=true

# 启用监控指标
ENABLE_METRICS=true

# 启用审计日志
ENABLE_AUDIT_LOG=true
```

#### 1.2 安全配置最佳实践

```bash
# 生成强密码的方法
# 方法1：使用openssl
openssl rand -base64 32

# 方法2：使用pwgen
pwgen -s 32 1

# 方法3：使用Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 生成JWT密钥
openssl rand -hex 64
```

### 2. 数据库配置

#### 2.1 MySQL配置优化 (mysql/my.cnf)

```ini
[mysqld]
# ===========================================
# 基础设置
# ===========================================
# 默认存储引擎
default-storage-engine = InnoDB

# 字符集设置
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
init-connect = 'SET NAMES utf8mb4'

# ===========================================
# 连接设置
# ===========================================
# 最大连接数（根据服务器配置调整）
max_connections = 500

# 最大连接错误数
max_connect_errors = 1000

# 连接超时时间
wait_timeout = 28800
interactive_timeout = 28800

# ===========================================
# 内存配置（根据服务器内存调整）
# ===========================================
# InnoDB缓冲池大小（建议设置为内存的70-80%）
innodb_buffer_pool_size = 1G

# InnoDB日志文件大小
innodb_log_file_size = 256M

# InnoDB日志缓冲区大小
innodb_log_buffer_size = 64M

# 键缓冲区大小
key_buffer_size = 128M

# 查询缓存大小
query_cache_size = 128M
query_cache_type = 1

# 排序缓冲区大小
sort_buffer_size = 2M

# 读缓冲区大小
read_buffer_size = 2M

# ===========================================
# 性能优化
# ===========================================
# InnoDB刷新日志策略（1=最安全，2=性能更好）
innodb_flush_log_at_trx_commit = 2

# InnoDB刷新方法
innodb_flush_method = O_DIRECT

# 每个表一个文件
innodb_file_per_table = 1

# InnoDB打开文件数
innodb_open_files = 400

# 线程缓存大小
thread_cache_size = 16

# 表缓存大小
table_open_cache = 2000

# ===========================================
# 日志配置
# ===========================================
# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# 错误日志
log-error = /var/log/mysql/error.log

# 二进制日志
log-bin = /var/log/mysql/mysql-bin
binlog_format = ROW
expire_logs_days = 7
max_binlog_size = 100M

# ===========================================
# 安全设置
# ===========================================
# 禁用本地文件加载
local-infile = 0

# 隐藏数据库列表
skip-show-database

# 禁用符号链接
symbolic-links = 0

[mysql]
default-character-set = utf8mb4

[client]
default-character-set = utf8mb4
```

#### 2.2 Redis配置优化 (redis/redis.conf)

```ini
# ===========================================
# 网络配置
# ===========================================
# 绑定地址
bind 0.0.0.0

# 端口
port 6379

# 客户端超时时间
timeout 300

# TCP keepalive
tcp-keepalive 60

# ===========================================
# 内存配置
# ===========================================
# 最大内存限制
maxmemory 512mb

# 内存淘汰策略
maxmemory-policy allkeys-lru

# ===========================================
# 持久化配置
# ===========================================
# RDB持久化
save 900 1
save 300 10
save 60 10000

# RDB文件压缩
rdbcompression yes

# RDB文件校验
rdbchecksum yes

# AOF持久化
appendonly yes
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# ===========================================
# 日志配置
# ===========================================
# 日志级别
loglevel notice

# 日志文件
logfile /var/log/redis/redis.log

# ===========================================
# 安全配置
# ===========================================
# 密码认证（建议启用）
# requirepass your_strong_redis_password

# 重命名危险命令
# rename-command FLUSHDB ""
# rename-command FLUSHALL ""
# rename-command CONFIG ""

# ===========================================
# 性能配置
# ===========================================
# 数据库数量
databases 16

# TCP监听队列长度
tcp-backlog 511

# 后台任务频率
hz 10

# 最大客户端连接数
maxclients 10000

# ===========================================
# 慢日志配置
# ===========================================
# 慢查询阈值（微秒）
slowlog-log-slower-than 10000

# 慢查询日志长度
slowlog-max-len 128
```

### 3. Web服务器配置

#### 3.1 Nginx配置优化 (nginx/nginx.conf)

```nginx
# ===========================================
# 全局配置
# ===========================================
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

# 工作进程文件描述符限制
worker_rlimit_nofile 65535;

events {
    # 每个工作进程的最大连接数
    worker_connections 2048;
    
    # 使用epoll事件模型
    use epoll;
    
    # 允许一个工作进程同时接受多个连接
    multi_accept on;
}

http {
    # ===========================================
    # 基础设置
    # ===========================================
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 隐藏Nginx版本信息
    server_tokens off;

    # 文件传输优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # 连接超时设置
    keepalive_timeout 65;
    keepalive_requests 100;

    # 类型哈希表大小
    types_hash_max_size 2048;

    # 客户端请求体大小限制
    client_max_body_size 10M;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;

    # ===========================================
    # 日志配置
    # ===========================================
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # ===========================================
    # Gzip压缩配置
    # ===========================================
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # ===========================================
    # 安全头配置
    # ===========================================
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';" always;

    # ===========================================
    # 上游服务配置
    # ===========================================
    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    # ===========================================
    # 限流配置
    # ===========================================
    # 定义限流区域
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # ===========================================
    # 缓存配置
    # ===========================================
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # ===========================================
    # SSL配置
    # ===========================================
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # OCSP装订
    ssl_stapling on;
    ssl_stapling_verify on;

    # 包含服务器配置
    include /etc/nginx/conf.d/*.conf;
}
```

## 监控配置

### 1. Prometheus配置

#### 1.1 基础配置 (monitoring/prometheus.yml)

```yaml
global:
  # 抓取间隔
  scrape_interval: 15s
  
  # 评估间隔
  evaluation_interval: 15s
  
  # 外部标签
  external_labels:
    monitor: 'ipam-monitor'
    environment: 'production'

# 规则文件
rule_files:
  - "alert_rules.yml"

# 告警管理器配置
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# 抓取配置
scrape_configs:
  # Prometheus自身监控
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 30s

  # IPAM后端服务监控
  - job_name: 'ipam-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  # Nginx监控
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/nginx_status'
    scrape_interval: 30s

  # MySQL监控
  - job_name: 'mysql'
    static_configs:
      - targets: ['mysql-exporter:9104']
    scrape_interval: 30s

  # Redis监控
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    scrape_interval: 30s

  # 系统监控
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 30s

  # 容器监控
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
    scrape_interval: 30s
```

#### 1.2 告警规则配置

详细的告警规则配置请参考 `monitoring/alert_rules.yml` 文件。

### 2. Grafana配置

#### 2.1 数据源配置

Grafana会自动配置Prometheus作为数据源，配置文件位于 `monitoring/grafana/datasources/prometheus.yml`。

#### 2.2 仪表盘配置

可以导入预定义的仪表盘或创建自定义仪表盘：

1. **系统概览仪表盘**: 显示系统整体状态
2. **应用性能仪表盘**: 显示应用性能指标
3. **数据库监控仪表盘**: 显示数据库性能
4. **网络监控仪表盘**: 显示网络相关指标

## 安全配置

### 1. 防火墙配置

```bash
# Ubuntu/Debian使用ufw
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3000/tcp  # Grafana (可选，建议仅内网访问)

# CentOS/RHEL使用firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --reload
```

### 2. SSL/TLS配置

#### 2.1 使用Let's Encrypt证书

```bash
# 安装certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d yourdomain.com

# 设置自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

#### 2.2 证书配置

将证书文件复制到正确位置：

```bash
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/server.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/server.key
```

### 3. 访问控制

#### 3.1 IP白名单

在Nginx配置中添加IP限制：

```nginx
# 限制管理接口访问
location /admin {
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    
    proxy_pass http://backend;
}
```

#### 3.2 基础认证

为监控接口添加基础认证：

```nginx
# Grafana访问控制
location /grafana/ {
    auth_basic "Monitoring Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://grafana:3000/;
}
```

## 性能调优

### 1. 数据库性能调优

#### 1.1 索引优化

```sql
-- 为常用查询添加索引
CREATE INDEX idx_ip_subnet_status ON ip_addresses(subnet_id, status);
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_subnet_network ON subnets(network);

-- 全文索引
CREATE FULLTEXT INDEX idx_ip_search ON ip_addresses(hostname, description);
```

#### 1.2 查询优化

```sql
-- 分析慢查询
SHOW PROCESSLIST;
SHOW FULL PROCESSLIST;

-- 查看查询执行计划
EXPLAIN SELECT * FROM ip_addresses WHERE subnet_id = 1;

-- 优化表
OPTIMIZE TABLE ip_addresses;
OPTIMIZE TABLE subnets;
```

### 2. 缓存策略

#### 2.1 Redis缓存配置

```python
# 缓存配置
CACHE_CONFIG = {
    'subnet_list': {'ttl': 300},      # 网段列表缓存5分钟
    'ip_statistics': {'ttl': 60},     # 统计数据缓存1分钟
    'user_permissions': {'ttl': 1800}, # 用户权限缓存30分钟
}
```

#### 2.2 HTTP缓存

```nginx
# 静态资源缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# API响应缓存
location /api/public/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$scheme$request_method$host$request_uri";
}
```

## 备份策略

### 1. 数据库备份

#### 1.1 自动备份脚本

```bash
#!/bin/bash
# 数据库备份脚本

BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mysql_backup_$DATE.sql"

# 创建备份
docker-compose exec -T mysql mysqldump \
    -u root -p"$MYSQL_ROOT_PASSWORD" \
    --all-databases \
    --routines \
    --triggers \
    --single-transaction > "$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_FILE"

# 清理旧备份
find "$BACKUP_DIR" -name "mysql_backup_*.sql.gz" -mtime +30 -delete
```

#### 1.2 定时备份

```bash
# 添加到crontab
0 2 * * * /app/scripts/backup.sh
```

### 2. 配置文件备份

```bash
# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    .env.prod \
    nginx/ \
    mysql/ \
    redis/ \
    monitoring/
```

## 故障排除

### 1. 日志分析

#### 1.1 应用日志

```bash
# 查看后端日志
docker-compose logs -f backend

# 查看Nginx日志
docker-compose logs -f nginx

# 查看数据库日志
docker-compose logs -f mysql
```

#### 1.2 系统日志

```bash
# 查看系统日志
journalctl -u docker
journalctl -f

# 查看容器资源使用
docker stats
```

### 2. 性能监控

#### 2.1 数据库性能

```sql
-- 查看当前连接
SHOW PROCESSLIST;

-- 查看InnoDB状态
SHOW ENGINE INNODB STATUS;

-- 查看慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

#### 2.2 系统性能

```bash
# CPU使用率
top
htop

# 内存使用
free -h

# 磁盘使用
df -h
iostat

# 网络状态
netstat -tlnp
ss -tlnp
```

## 最佳实践

### 1. 安全最佳实践

1. **定期更新密码**: 每3-6个月更新一次系统密码
2. **最小权限原则**: 只给用户必要的权限
3. **定期备份**: 每日自动备份，每周验证备份
4. **监控告警**: 设置完善的监控告警机制
5. **安全审计**: 定期检查访问日志和审计日志

### 2. 性能最佳实践

1. **资源监控**: 持续监控CPU、内存、磁盘使用情况
2. **数据库优化**: 定期分析和优化数据库查询
3. **缓存策略**: 合理使用缓存减少数据库压力
4. **负载均衡**: 在高负载情况下考虑负载均衡
5. **容量规划**: 根据业务增长预测资源需求

### 3. 运维最佳实践

1. **版本控制**: 所有配置文件纳入版本控制
2. **自动化部署**: 使用脚本自动化部署流程
3. **文档维护**: 及时更新文档和操作手册
4. **故障预案**: 制定详细的故障处理预案
5. **定期演练**: 定期进行故障恢复演练