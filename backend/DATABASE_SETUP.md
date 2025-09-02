# 数据库设置指南

本文档说明如何设置和管理IPAM系统的数据库。

## 快速开始

### 1. 启动数据库服务

使用Docker Compose启动MySQL和Redis服务：

```bash
# 在项目根目录执行
docker-compose up -d mysql redis
```

### 2. 完整数据库设置

执行一键设置命令：

```bash
cd backend
python manage_db.py setup
```

这个命令会自动执行以下步骤：
- 等待数据库连接可用
- 执行数据库迁移
- 初始化种子数据
- 执行健康检查

### 3. 启动后端服务

```bash
cd backend
python main.py
```

## 数据库管理命令

### 连接检查

```bash
# 检查数据库连接
python manage_db.py check

# 等待数据库连接可用（用于容器启动）
python manage_db.py wait

# 执行详细健康检查
python manage_db.py health

# 显示连接池信息
python manage_db.py pool
```

### 数据库操作

```bash
# 初始化数据库表结构（仅开发环境）
python manage_db.py init

# 执行Alembic数据库迁移（推荐）
python manage_db.py migrate

# 删除所有数据库表（危险操作）
python manage_db.py drop
```

### 数据管理

```bash
# 初始化种子数据（默认用户和配置）
python manage_db.py seed

# 初始化种子数据和演示数据
python manage_db.py seed-demo

# 重置admin用户密码
python manage_db.py reset-password
```

## 数据库架构

### 核心表结构

1. **users** - 用户表
   - 存储用户账号、角色、主题偏好等信息
   - 默认创建admin用户（用户名：admin，密码：admin123）

2. **subnets** - 网段表
   - 存储网络网段信息（CIDR格式）
   - 包含网关、VLAN、位置等属性

3. **ip_addresses** - IP地址表
   - 存储所有IP地址及其分配状态
   - 关联到网段，支持设备信息和标签

4. **tags** - 标签表
   - 支持为IP地址和网段添加分类标签
   - 预设常用标签（服务器、网络设备、打印机等）

5. **audit_logs** - 审计日志表
   - 记录所有操作历史
   - 支持操作回溯和安全审计

6. **system_configs** - 系统配置表
   - 存储系统级配置参数
   - 支持动态配置管理

7. **alert_rules** / **alert_history** - 警报系统
   - 支持使用率警报和冲突检测
   - 记录警报历史和处理状态

8. **custom_fields** / **custom_field_values** - 自定义字段
   - 支持为IP和网段添加自定义属性
   - 灵活的字段类型支持

### 关系设计

- 用户与网段：一对多（创建者关系）
- 网段与IP地址：一对多（级联删除）
- 用户与IP地址：一对多（分配者关系）
- 标签与IP/网段：多对多关系
- 自定义字段：支持IP和网段的扩展属性

## 连接池配置

系统使用SQLAlchemy连接池管理数据库连接：

```python
# 连接池配置
pool_size=20          # 基础连接数
max_overflow=30       # 最大溢出连接
pool_timeout=30       # 获取连接超时
pool_recycle=3600     # 连接回收时间（1小时）
pool_pre_ping=True    # 连接预检查
```

### 监控连接池

```bash
# 查看连接池详细信息
python manage_db.py pool
```

输出示例：
```
连接池配置:
  基础连接数: 20
  最大溢出连接: 30
  连接超时: 30秒
  连接回收时间: 3600秒

当前状态:
  总连接数: 5
  使用率: 25.0%
  活跃连接: 5
  空闲连接: 15
  溢出连接: 0
  无效连接: 0

优化建议:
  1. 连接池状态良好
```

## 健康检查

系统提供多层次的健康检查：

### 1. 快速健康检查

```bash
curl http://localhost:8000/health
```

### 2. 详细健康检查

```bash
curl http://localhost:8000/health/detailed
```

### 3. 命令行健康检查

```bash
python manage_db.py health
```

健康状态说明：
- **healthy**: 所有指标正常
- **degraded**: 部分指标异常但系统可用
- **unhealthy**: 系统不可用

## 数据库迁移

### Alembic迁移管理

```bash
# 查看当前迁移状态
alembic current

# 查看迁移历史
alembic history

# 升级到最新版本
alembic upgrade head

# 降级到指定版本
alembic downgrade <revision>

# 生成新的迁移文件
alembic revision --autogenerate -m "描述信息"
```

### 迁移文件位置

- 迁移脚本：`backend/alembic/versions/`
- 配置文件：`backend/alembic.ini`
- 环境配置：`backend/alembic/env.py`

## 种子数据

### 默认数据包含

1. **管理员用户**
   - 用户名：admin
   - 密码：admin123（⚠️ 生产环境请修改）
   - 角色：超级管理员

2. **系统配置**
   - 系统名称和版本
   - 分页配置
   - 安全策略
   - 警报阈值

3. **默认标签**
   - 服务器、网络设备、打印机
   - 测试环境、生产环境、开发环境
   - 重要标记

### 演示数据（可选）

使用 `seed-demo` 命令还会创建：
- 演示网段：192.168.1.0/24
- 示例IP地址分配
- 设备信息示例

## 故障排除

### 常见问题

1. **连接被拒绝**
   ```
   ConnectionRefusedError: [WinError 10061] 由于目标计算机积极拒绝，无法连接
   ```
   解决方案：确保MySQL服务正在运行

2. **权限错误**
   ```
   Access denied for user 'ipam_user'@'localhost'
   ```
   解决方案：检查数据库用户权限和密码

3. **表不存在**
   ```
   Table 'ipam.users' doesn't exist
   ```
   解决方案：执行数据库迁移或初始化

### 诊断命令

```bash
# 检查数据库连接
python manage_db.py check

# 查看详细错误信息
python manage_db.py health

# 检查连接池状态
python manage_db.py pool
```

### 重置数据库

如果需要完全重置数据库：

```bash
# 1. 删除所有表
python manage_db.py drop

# 2. 重新初始化
python manage_db.py setup
```

## 生产环境注意事项

1. **修改默认密码**
   ```bash
   python manage_db.py reset-password
   ```

2. **使用环境变量**
   ```bash
   export DATABASE_URL="mysql+pymysql://user:pass@host:port/db"
   export SECRET_KEY="your-production-secret-key"
   ```

3. **启用SSL连接**
   在DATABASE_URL中添加SSL参数

4. **定期备份**
   设置数据库自动备份策略

5. **监控连接池**
   定期检查连接池使用情况，根据负载调整配置

## API端点

系统提供以下健康检查端点：

- `GET /health` - 快速健康检查
- `GET /health/detailed` - 详细健康检查
- `GET /api/health` - API健康检查

这些端点可用于负载均衡器和监控系统的健康检查。