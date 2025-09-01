# 企业IP地址管理系统 - 安装部署指南

## 系统要求

### 硬件要求
- CPU: 2核心及以上
- 内存: 4GB及以上
- 存储: 20GB及以上可用空间
- 网络: 100Mbps及以上

### 软件要求
- 操作系统: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.15+
- Python: 3.8或更高版本
- Node.js: 16.0或更高版本
- MySQL: 8.0或更高版本

## 安装步骤

### 1. 环境准备

#### 安装Python
```bash
# Windows (使用官网下载安装包)
# 或使用Chocolatey
choco install python

# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip

# macOS (使用Homebrew)
brew install python
```

#### 安装Node.js
```bash
# Windows (使用官网下载安装包)
# 或使用Chocolatey
choco install nodejs

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_lts.x | sudo bash -
sudo yum install -y nodejs

# macOS (使用Homebrew)
brew install node
```

#### 安装MySQL
```bash
# Windows (使用官网下载安装包)

# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server mysql-client
sudo mysql_secure_installation

# CentOS/RHEL
sudo yum install mysql-server mysql
sudo systemctl start mysqld
sudo mysql_secure_installation

# macOS (使用Homebrew)
brew install mysql
brew services start mysql
```

### 2. 项目部署

#### 下载项目
```bash
git clone <项目地址>
cd ipmanagersystem
```

#### 后端部署

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置数据库
```bash
# 复制配置文件
cp config.env.example config.env

# 编辑配置文件，修改数据库连接信息
# vim config.env (Linux/macOS)
# notepad config.env (Windows)
```

配置文件示例：
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ip_management_system
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=True
```

5. 初始化数据库
```bash
# 登录MySQL
mysql -u root -p

# 创建数据库和执行初始化脚本
mysql> source ../database/init.sql;
```

6. 启动后端服务
```bash
python start.py
# 或
python app/main.py
```

#### 前端部署

1. 进入前端目录
```bash
cd ../frontend
```

2. 安装依赖
```bash
npm install
# 或使用yarn
yarn install
```

3. 开发环境启动
```bash
npm run dev
# 或
yarn dev
```

4. 生产环境构建
```bash
npm run build
# 或
yarn build
```

### 3. 生产环境部署

#### 使用Nginx部署前端

1. 安装Nginx
```bash
# Ubuntu/Debian
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx

# Windows
# 下载Nginx官网安装包
```

2. 配置Nginx
```nginx
# /etc/nginx/sites-available/ip-management
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/ipmanagersystem/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. 启用站点
```bash
sudo ln -s /etc/nginx/sites-available/ip-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 使用Supervisor管理后端进程

1. 安装Supervisor
```bash
sudo apt install supervisor  # Ubuntu/Debian
sudo yum install supervisor  # CentOS/RHEL
```

2. 创建配置文件
```ini
# /etc/supervisor/conf.d/ip-management-backend.conf
[program:ip-management-backend]
command=/path/to/ipmanagersystem/backend/venv/bin/python start.py
directory=/path/to/ipmanagersystem/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ip-management/backend.log
environment=PATH="/path/to/ipmanagersystem/backend/venv/bin"
```

3. 启动服务
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ip-management-backend
```

### 4. 域名和SSL配置

#### 使用Let's Encrypt获取SSL证书
```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx  # Ubuntu/Debian
sudo yum install certbot python3-certbot-nginx  # CentOS/RHEL

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加以下行
0 12 * * * /usr/bin/certbot renew --quiet
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DB_HOST | 数据库主机 | localhost |
| DB_PORT | 数据库端口 | 3306 |
| DB_USER | 数据库用户名 | root |
| DB_PASSWORD | 数据库密码 | - |
| DB_NAME | 数据库名称 | ip_management_system |
| API_HOST | API监听地址 | 0.0.0.0 |
| API_PORT | API监听端口 | 8000 |
| DEBUG_MODE | 调试模式 | False |

### 数据库配置

确保MySQL服务正在运行并且可以连接：
```bash
# 检查MySQL服务状态
sudo systemctl status mysql

# 测试连接
mysql -h localhost -u root -p -e "SELECT VERSION();"
```

### 防火墙配置

开放必要的端口：
```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## 常见问题

### 1. 数据库连接失败
- 检查MySQL服务是否启动
- 验证数据库连接信息
- 确认防火墙设置
- 检查MySQL用户权限

### 2. 前端无法访问后端API
- 检查后端服务是否启动
- 验证CORS配置
- 确认代理配置正确

### 3. 权限错误
- 确保文件目录权限正确
- 检查用户组设置
- 验证虚拟环境路径

### 4. 端口冲突
- 检查端口是否被占用：`netstat -tlnp | grep :8000`
- 修改配置文件中的端口号
- 重启相关服务

## 性能优化

### 数据库优化
1. 设置合适的连接池大小
2. 启用查询缓存
3. 优化索引
4. 定期清理日志

### 前端优化
1. 启用Gzip压缩
2. 配置缓存策略
3. 使用CDN加速
4. 代码分割和懒加载

### 后端优化
1. 使用异步处理
2. 实现缓存机制
3. 优化数据库查询
4. 配置负载均衡

## 监控和日志

### 日志位置
- 后端日志：`backend/logs/app.log`
- Nginx日志：`/var/log/nginx/`
- MySQL日志：`/var/log/mysql/`

### 监控建议
1. 设置服务监控
2. 配置错误报警
3. 监控资源使用情况
4. 定期备份数据

## 备份和恢复

### 数据库备份
```bash
# 备份
mysqldump -u root -p ip_management_system > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复
mysql -u root -p ip_management_system < backup_file.sql
```

### 应用备份
```bash
# 备份整个项目
tar -czf ip-management-backup-$(date +%Y%m%d).tar.gz ipmanagersystem/
```

## 升级指南

1. 备份数据库和应用文件
2. 停止服务
3. 更新代码
4. 安装新的依赖
5. 运行数据库迁移（如有）
6. 重新构建前端
7. 重启服务
8. 验证功能

联系支持：如有问题，请查看项目文档或提交Issue。