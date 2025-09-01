# Docker部署指南

## 系统要求

- **操作系统**: Windows 10/11 (支持WSL2)
- **Docker Desktop**: 4.0.0 或更高版本
- **内存**: 至少 4GB 可用内存
- **磁盘空间**: 至少 2GB 可用空间

## 快速开始

### 1. 安装Docker Desktop

1. 访问 [Docker官网](https://www.docker.com/products/docker-desktop) 下载Docker Desktop for Windows
2. 运行安装程序并按照提示完成安装
3. 启动Docker Desktop并确保WSL2后端已启用
4. 验证安装：打开命令行运行 `docker --version`

### 2. 一键部署

1. 打开项目根目录
2. 双击运行 `start.bat` 脚本
3. 等待自动构建和启动完成
4. 浏览器自动打开 http://localhost

### 3. 手动部署（可选）

如果自动脚本有问题，可以手动执行以下命令：

```bash
# 进入项目目录
cd d:\Python-Project\ipmanagersystem

# 构建并启动所有服务
docker-compose up --build -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

## 服务访问地址

- **前端应用**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **数据库**: localhost:3306

## 默认账号信息

### 数据库连接信息
- **主机**: localhost:3306
- **数据库名**: ip_management_system
- **用户名**: ipuser
- **密码**: ippassword
- **Root密码**: rootpassword

### 系统管理员账号
系统启动后，数据库会自动初始化以下用户：
- 用户名: admin
- 姓名: 系统管理员
- 邮箱: admin@company.com

## 常用Docker管理命令

### 服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up --build -d
```

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### 容器管理
```bash
# 查看容器状态
docker-compose ps

# 进入容器内部
docker-compose exec backend bash
docker-compose exec mysql bash

# 查看容器资源使用
docker stats
```

### 数据管理
```bash
# 备份数据库
docker-compose exec mysql mysqldump -u ipuser -pippassword ip_management_system > backup.sql

# 恢复数据库
docker-compose exec -T mysql mysql -u ipuser -pippassword ip_management_system < backup.sql
```

## 故障排除

### 1. Docker Desktop未启动
**错误**: `error during connect: This error may indicate that the docker daemon is not running`

**解决方案**:
- 启动Docker Desktop应用
- 等待Docker引擎完全启动（状态变为绿色）

### 2. 端口被占用
**错误**: `Port 80 is already in use`

**解决方案**:
- 停止占用端口的其他服务
- 或修改docker-compose.yml中的端口映射

### 3. 内存不足
**错误**: 容器频繁重启或构建失败

**解决方案**:
- 在Docker Desktop设置中增加分配给Docker的内存
- 关闭其他占用内存的应用程序

### 4. 数据库连接失败
**错误**: `Can't connect to MySQL server`

**解决方案**:
- 等待MySQL容器完全启动（可能需要1-2分钟）
- 检查MySQL容器状态：`docker-compose ps`
- 查看MySQL日志：`docker-compose logs mysql`

### 5. 前端页面无法访问
**错误**: 浏览器显示连接错误

**解决方案**:
- 检查所有容器是否正常运行：`docker-compose ps`
- 检查Nginx配置是否正确
- 确认防火墙未阻止80端口

## 生产环境部署

### 1. 环境变量配置
复制 `.env.example` 为 `.env` 并修改配置：
```bash
# 数据库密码（生产环境请使用强密码）
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_PASSWORD=your_user_password

# 后端配置
DEBUG_MODE=false
```

### 2. SSL证书配置
在生产环境中，建议配置HTTPS：

1. 获取SSL证书
2. 修改nginx.conf配置
3. 更新docker-compose.yml端口映射

### 3. 数据备份策略
```bash
# 创建备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec mysql mysqldump -u ipuser -pippassword ip_management_system > backup_$DATE.sql
```

## 性能优化

### 1. 资源限制
在docker-compose.yml中添加资源限制：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### 2. 数据库优化
- 配置MySQL的my.cnf文件
- 设置合适的缓冲区大小
- 启用查询缓存

### 3. 前端优化
- 启用Nginx的gzip压缩
- 配置静态资源缓存
- 使用CDN加速

## 监控和维护

### 1. 健康检查
Docker Compose已配置健康检查，可通过以下命令查看：
```bash
docker-compose ps
```

### 2. 日志轮转
配置日志轮转防止日志文件过大：
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 3. 自动重启
Docker Compose已配置容器自动重启策略：
```yaml
restart: unless-stopped
```

## 卸载

### 完全清理
```bash
# 停止并删除所有容器
docker-compose down

# 删除数据卷（注意：这会删除所有数据）
docker-compose down -v

# 删除镜像
docker-compose down --rmi all

# 清理未使用的资源
docker system prune -a
```

需要帮助？请查看项目文档或提交Issue。