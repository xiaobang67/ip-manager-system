# IPAM系统安装指南

## 系统要求

### 硬件要求
- **CPU**: 最低2核，推荐4核或以上
- **内存**: 最低4GB，推荐8GB或以上
- **存储**: 最低20GB可用空间，推荐50GB或以上
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+, RHEL 7+)
- **Docker**: 版本20.10或以上
- **Docker Compose**: 版本1.29或以上
- **Git**: 用于获取源代码

## 安装步骤

### 1. 环境准备

#### 1.1 安装Docker

**Ubuntu/Debian:**
```bash
# 更新包索引
sudo apt-get update

# 安装必要的包
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

**CentOS/RHEL:**
```bash
# 安装必要的包
sudo yum install -y yum-utils

# 添加Docker仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### 1.2 安装Docker Compose

```bash
# 下载Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

#### 1.3 配置用户权限

```bash
# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使权限生效
newgrp docker
```

### 2. 获取源代码

```bash
# 克隆项目仓库
git clone https://github.com/your-org/ipam-system.git
cd ipam-system

# 或者下载并解压源代码包
wget https://github.com/your-org/ipam-system/archive/main.zip
unzip main.zip
cd ipam-system-main
```

### 3. 配置环境

#### 3.1 创建环境配置文件

```bash
# 复制环境配置模板
cp .env.example .env.prod

# 编辑配置文件
nano .env.prod
```

#### 3.2 配置参数说明

```bash
# MySQL数据库配置
MYSQL_ROOT_PASSWORD=your_strong_root_password    # MySQL root密码
MYSQL_PASSWORD=your_strong_password              # 应用数据库密码

# JWT认证配置
JWT_SECRET_KEY=your_jwt_secret_key_here         # JWT密钥，建议使用随机字符串

# CORS跨域配置
CORS_ORIGINS=http://localhost,https://yourdomain.com  # 允许的前端域名

# Grafana监控配置
GRAFANA_PASSWORD=your_grafana_password          # Grafana管理员密码

# 备份配置
BACKUP_RETENTION_DAYS=30                        # 备份保留天数

# 监控告警配置
ALERT_EMAIL=admin@yourdomain.com               # 告警邮箱
```

#### 3.3 生成安全密钥

```bash
# 生成JWT密钥
openssl rand -hex 32

# 生成MySQL密码
openssl rand -base64 32
```

### 4. 部署系统

#### 4.1 使用部署脚本

```bash
# 给部署脚本添加执行权限
chmod +x deploy.sh

# 启动系统
./deploy.sh start
```

#### 4.2 手动部署

```bash
# 创建必要的目录
mkdir -p logs/{nginx,backend,mysql,redis}
mkdir -p backups
mkdir -p nginx/ssl

# 生成SSL证书（自签名）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/server.key \
    -out nginx/ssl/server.crt \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"

# 启动服务
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### 5. 验证安装

#### 5.1 检查服务状态

```bash
# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看服务日志
docker-compose -f docker-compose.prod.yml logs
```

#### 5.2 访问系统

- **主应用**: https://localhost 或 https://your-domain.com
- **Grafana监控**: http://localhost:3000
- **Prometheus**: http://localhost:9090

#### 5.3 健康检查

```bash
# 检查API健康状态
curl -k https://localhost/api/health

# 检查各服务状态
./deploy.sh status
```

## 配置说明

### 1. 数据库配置

#### 1.1 MySQL优化

编辑 `mysql/my.cnf` 文件根据服务器配置调整参数：

```ini
# 根据服务器内存调整缓冲区大小
innodb_buffer_pool_size = 512M  # 建议设置为内存的70-80%

# 根据并发连接数调整
max_connections = 500

# 根据磁盘性能调整
innodb_flush_log_at_trx_commit = 1  # 1=最安全，2=性能更好
```

#### 1.2 Redis配置

编辑 `redis/redis.conf` 文件：

```ini
# 根据内存大小调整
maxmemory 512mb

# 设置密码（推荐）
requirepass your_redis_password
```

### 2. Nginx配置

#### 2.1 SSL证书配置

**使用Let's Encrypt证书:**

```bash
# 安装certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书到nginx目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/server.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/server.key
```

#### 2.2 性能优化

编辑 `nginx/nginx.conf` 文件：

```nginx
# 根据CPU核心数调整
worker_processes auto;

# 根据并发连接数调整
worker_connections 2048;

# 启用HTTP/2
listen 443 ssl http2;
```

### 3. 监控配置

#### 3.1 Prometheus配置

编辑 `monitoring/prometheus.yml` 添加自定义监控目标：

```yaml
scrape_configs:
  - job_name: 'custom-app'
    static_configs:
      - targets: ['app:8080']
```

#### 3.2 告警配置

编辑 `monitoring/alert_rules.yml` 添加自定义告警规则：

```yaml
- alert: CustomAlert
  expr: custom_metric > 100
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "自定义告警"
```

## 维护操作

### 1. 日常维护

```bash
# 查看系统状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 备份数据库
./deploy.sh backup

# 更新系统
./deploy.sh update
```

### 2. 数据备份

#### 2.1 自动备份

系统会在每次停止服务时自动备份数据库，备份文件保存在 `backups/` 目录。

#### 2.2 手动备份

```bash
# 备份数据库
./deploy.sh backup

# 备份整个数据目录
docker run --rm -v ipam_mysql_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/mysql_data_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### 3. 数据恢复

```bash
# 恢复数据库
docker-compose -f docker-compose.prod.yml exec mysql mysql -u root -p < backups/mysql_backup_YYYYMMDD_HHMMSS.sql

# 恢复数据目录
docker run --rm -v ipam_mysql_data:/data -v $(pwd)/backups:/backup alpine tar xzf /backup/mysql_data_YYYYMMDD_HHMMSS.tar.gz -C /data
```

## 故障排除

### 1. 常见问题

#### 1.1 容器启动失败

```bash
# 查看容器日志
docker-compose -f docker-compose.prod.yml logs [service_name]

# 检查端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :443
```

#### 1.2 数据库连接失败

```bash
# 检查MySQL容器状态
docker-compose -f docker-compose.prod.yml ps mysql

# 测试数据库连接
docker-compose -f docker-compose.prod.yml exec mysql mysql -u root -p -e "SELECT 1"
```

#### 1.3 前端无法访问

```bash
# 检查Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -t

# 重新加载Nginx配置
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

### 2. 性能问题

#### 2.1 数据库性能

```bash
# 查看MySQL慢查询
docker-compose -f docker-compose.prod.yml exec mysql mysql -u root -p -e "SHOW PROCESSLIST"

# 分析慢查询日志
docker-compose -f docker-compose.prod.yml exec mysql tail -f /var/log/mysql/slow.log
```

#### 2.2 内存使用

```bash
# 查看容器资源使用
docker stats

# 查看系统资源使用
free -h
df -h
```

### 3. 安全问题

#### 3.1 更新密码

```bash
# 更新MySQL密码
docker-compose -f docker-compose.prod.yml exec mysql mysql -u root -p -e "ALTER USER 'root'@'%' IDENTIFIED BY 'new_password'"

# 更新应用配置
nano .env.prod
./deploy.sh restart
```

#### 3.2 SSL证书更新

```bash
# 更新Let's Encrypt证书
sudo certbot renew

# 重新加载Nginx
docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
```

## 升级指南

### 1. 版本升级

```bash
# 备份当前数据
./deploy.sh backup

# 获取最新代码
git pull origin main

# 更新系统
./deploy.sh update
```

### 2. 数据库迁移

```bash
# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## 联系支持

如果遇到问题，请：

1. 查看日志文件：`logs/` 目录下的相关日志
2. 检查系统状态：`./deploy.sh status`
3. 查看文档：`docs/` 目录下的相关文档
4. 联系技术支持：support@your-domain.com