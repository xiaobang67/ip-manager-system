# IP地址管理系统 (IPAM)

企业级IP地址管理系统，采用Vue.js前端、Python FastAPI后端和MySQL数据库的现代化架构。

## 项目概述

这是一个功能完整的企业级IP地址管理系统，提供了完整的网络资源管理解决方案，包括IP地址分配、网段管理、用户权限控制、部门管理、设备类型管理和系统监控等功能。系统采用现代化的前后端分离架构，提供直观易用的Web界面和完整的RESTful API。

## 项目结构

```
ipam/
├── frontend/                    # Vue.js 前端应用
│   ├── src/
│   │   ├── components/         # Vue组件
│   │   ├── views/              # 页面视图
│   │   │   ├── Dashboard.vue           # 系统仪表盘
│   │   │   ├── IPManagement.vue        # IP地址管理
│   │   │   ├── SubnetManagement.vue    # 网段管理
│   │   │   ├── UserManagement.vue      # 用户管理
│   │   │   ├── DepartmentManagement.vue # 部门管理
│   │   │   ├── DeviceTypeManagement.vue # 设备类型管理
│   │   │   └── SecurityDashboard.vue   # 安全监控
│   │   ├── router/             # 路由配置
│   │   ├── store/              # Vuex状态管理
│   │   └── api/                # API接口
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── backend/                     # Python FastAPI 后端
│   ├── app/
│   │   ├── api/v1/             # API路由
│   │   ├── core/               # 核心配置
│   │   │   ├── security.py             # 安全配置
│   │   │   ├── database.py             # 数据库配置
│   │   │   └── dependencies.py         # 依赖注入
│   │   ├── models/             # 数据模型
│   │   │   ├── user.py                 # 用户模型
│   │   │   ├── ip_address.py           # IP地址模型
│   │   │   ├── subnet.py               # 网段模型
│   │   │   ├── department.py           # 部门模型
│   │   │   └── audit_log.py            # 审计日志模型
│   │   ├── services/           # 业务逻辑
│   │   ├── repositories/       # 数据访问层
│   │   └── schemas/            # API模式
│   ├── alembic/                # 数据库迁移
│   ├── api_extensions.py       # API扩展
│   ├── enhanced_main.py        # 增强主程序
│   ├── requirements.txt
│   └── Dockerfile
├── database/                    # 数据库脚本
│   ├── init.sql                # 初始化脚本
│   └── seed.sql                # 种子数据
├── nginx/                       # Nginx配置
├── monitoring/                  # 监控配置
├── logs/                        # 日志目录
├── docker-compose.yml          # Docker编排配置
└── README.md
```

## 技术栈

### 前端
- **Vue.js 3** - 渐进式JavaScript框架
- **Vue Router** - 官方路由管理器
- **Vuex** - 状态管理模式
- **Element Plus** - Vue 3 UI组件库
- **Vite** - 现代化构建工具
- **Axios** - HTTP客户端

### 后端
- **FastAPI** - 现代化Python Web框架
- **SQLAlchemy** - Python SQL工具包和ORM
- **Alembic** - 数据库迁移工具
- **Pydantic** - 数据验证库
- **Uvicorn** - ASGI服务器
- **PyMySQL** - MySQL数据库驱动
- **Passlib** - 密码哈希库
- **PyJWT** - JWT令牌处理

### 数据库与缓存
- **MySQL 8.0** - 关系型数据库
- **Redis 6** - 内存数据库（缓存）

### 基础设施
- **Docker** - 容器化部署
- **Docker Compose** - 容器编排
- **Nginx** - 反向代理和静态文件服务

## 核心功能

### ✅ 已完成功能

#### 用户认证与权限管理
- 用户登录/注销
- JWT令牌认证
- 基于角色的权限控制（Admin/Manager/User）
- 密码强度验证和安全哈希
- 用户会话管理

#### IP地址管理
- IP地址分配和释放
- IP地址搜索和过滤
- IP地址状态管理（可用/已分配/保留）
- 批量IP操作
- IP地址使用统计

#### 网段管理
- 网段创建和编辑
- 网段IP地址自动生成
- 网段重叠检测
- CIDR格式验证
- 网段使用率统计

#### 用户管理
- 用户CRUD操作
- 用户角色分配
- 用户状态管理
- 密码重置功能
- 用户活动统计

#### 部门管理
- 部门信息管理
- 部门与IP分配关联
- 部门层级结构
- 部门使用统计

#### 设备类型管理
- 设备类型定义和管理
- 设备类型与IP分配关联
- 设备类型统计分析
- 自定义设备类型支持

#### 安全监控
- 登录安全监控
- 操作审计日志
- 安全事件告警
- 系统健康检查

#### 系统仪表盘
- IP地址使用分布图表
- IP分配趋势分析
- 网段使用率排行
- 实时数据刷新功能
- 系统统计概览

## 快速开始

### 环境要求
- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Node.js** 16+ (开发环境)
- **Python** 3.9+ (开发环境)

### 使用Docker启动（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd ipam
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置数据库密码等配置
```

3. **启动所有服务**
```bash
# 使用启动脚本（Windows）
start.bat

# 或使用Docker Compose
docker-compose up -d --build
```

4. **访问应用**
- **前端应用**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **默认登录**: admin / admin123

### 开发环境设置

#### 前端开发
```bash
cd frontend
npm install
npm run dev
# 访问: http://localhost:5173
```

#### 后端开发
```bash
cd backend
pip install -r requirements.txt
uvicorn enhanced_main:app --reload --host 0.0.0.0 --port 8000
# 访问: http://localhost:8000
```

## 部署指南

### 开发环境部署
```bash
# Windows
start.bat

# Linux/macOS
./deploy.sh start
```

### 生产环境部署
1. **配置生产环境变量**
2. **设置SSL证书**
3. **配置数据库备份**
4. **启用监控服务**

```bash
# 生产环境部署
./deploy.sh start
```

## API文档

系统提供完整的RESTful API，支持以下主要端点：

### 认证相关
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/logout` - 用户注销
- `PUT /api/auth/password` - 修改密码

### IP地址管理
- `GET /api/ips/` - 获取IP地址列表
- `POST /api/ips/allocate` - 分配IP地址
- `PUT /api/ips/{ip_id}/release` - 释放IP地址
- `GET /api/ips/search` - 搜索IP地址

### 网段管理
- `GET /api/subnets/` - 获取网段列表
- `POST /api/subnets/` - 创建网段
- `PUT /api/subnets/{subnet_id}` - 更新网段
- `DELETE /api/subnets/{subnet_id}` - 删除网段

### 用户管理
- `GET /api/users/` - 获取用户列表
- `POST /api/users/` - 创建用户
- `PUT /api/users/{user_id}` - 更新用户
- `DELETE /api/users/{user_id}` - 删除用户

### 部门管理
- `GET /api/departments/` - 获取部门列表
- `POST /api/departments/` - 创建部门
- `PUT /api/departments/{dept_id}` - 更新部门
- `DELETE /api/departments/{dept_id}` - 删除部门

### 设备类型管理
- `GET /api/device-types/` - 获取设备类型列表
- `POST /api/device-types/` - 创建设备类型
- `PUT /api/device-types/{type_id}` - 更新设备类型
- `DELETE /api/device-types/{type_id}` - 删除设备类型

### 监控和统计
- `GET /api/v1/monitoring/dashboard` - 获取仪表盘数据
- `GET /api/v1/monitoring/ip-utilization` - 获取IP使用率统计
- `GET /api/v1/monitoring/subnet-utilization` - 获取网段使用率统计
- `GET /api/v1/monitoring/allocation-trends` - 获取IP分配趋势
- `GET /api/v1/monitoring/top-utilized-subnets` - 获取使用率最高的网段

详细API文档请访问: http://localhost:8000/docs

## 数据库管理

### 数据库迁移
```bash
cd backend
python run_migration.py
```

### 数据库备份
```bash
# 手动备份
./deploy.sh backup

# 自动备份（生产环境）
# 配置在 docker-compose.yml 中
```

## 监控和日志

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 系统监控
- **健康检查**: http://localhost:8000/health
- **系统状态**: 通过仪表盘查看
- **安全监控**: 安全仪表盘页面

## 安全特性

- **密码安全**: bcrypt哈希加密
- **JWT认证**: 安全的令牌认证
- **权限控制**: 基于角色的访问控制
- **审计日志**: 完整的操作记录
- **输入验证**: 防止SQL注入和XSS攻击
- **CORS配置**: 跨域请求安全控制

## 故障排除

### 常见问题

1. **服务启动失败**
   - 检查Docker是否运行
   - 检查端口是否被占用
   - 查看服务日志

2. **数据库连接失败**
   - 检查数据库服务状态
   - 验证数据库配置
   - 检查网络连接

3. **前端页面空白**
   - 清除浏览器缓存
   - 检查后端API是否正常
   - 查看浏览器控制台错误

### 获取帮助
- 查看项目文档
- 检查日志文件
- 提交Issue到项目仓库

## 性能优化

### 数据库优化
- **索引优化**: 为常用查询字段添加索引
- **连接池**: 配置合适的数据库连接池大小
- **查询优化**: 使用分页查询避免大数据量加载

### 前端优化
- **懒加载**: 大表格数据采用分页和虚拟滚动
- **缓存策略**: 合理使用浏览器缓存和API缓存
- **组件优化**: 避免不必要的组件重渲染

### 后端优化
- **异步处理**: 使用FastAPI的异步特性
- **缓存机制**: Redis缓存热点数据
- **批量操作**: 优化批量IP操作的性能

## 最佳实践

### 网段规划
- **合理划分**: 根据组织结构合理划分网段
- **预留空间**: 为未来扩展预留足够的IP地址空间
- **避免重叠**: 确保网段之间不存在重叠

### 权限管理
- **最小权限**: 遵循最小权限原则分配用户权限
- **定期审查**: 定期审查和更新用户权限
- **密码策略**: 实施强密码策略和定期更换

### 数据管理
- **定期备份**: 建立定期数据备份机制
- **数据清理**: 定期清理过期和无用数据
- **审计日志**: 保持完整的操作审计日志

## 常见问题 (FAQ)

### Q: 如何重置管理员密码？
A: 可以通过以下方式重置：
```bash
# 进入后端容器
docker exec -it ipam-backend bash
# 运行密码重置脚本
python reset_admin_password.py
```

### Q: 如何备份和恢复数据？
A: 使用以下命令：
```bash
# 备份数据
./deploy.sh backup

# 恢复数据
./deploy.sh restore backup_file.sql
```

### Q: 如何添加新的设备类型？
A: 在设备类型管理页面点击"添加设备类型"，填写类型代码和名称即可。

### Q: 系统支持多少个IP地址？
A: 理论上支持IPv4的全部地址空间，实际容量取决于硬件配置和数据库性能。

### Q: 如何配置HTTPS？
A: 修改nginx配置文件，添加SSL证书：
```bash
# 生成SSL证书
./generate-ssl.bat

# 重启nginx服务
docker-compose restart nginx
```

### Q: 如何监控系统性能？
A: 系统提供以下监控方式：
- 健康检查端点: `/health`
- 系统仪表盘: 实时查看使用情况
- 日志监控: 查看应用和访问日志

## 开发指南

### 代码结构
- 前端采用组件化开发
- 后端采用分层架构
- 数据库采用ORM模式
- API采用RESTful设计

### 开发规范
- 代码注释完整
- 遵循PEP8规范（Python）
- 使用ESLint（JavaScript）
- Git提交信息规范

## 更新日志

### v1.0.0 (当前版本)
- ✅ 完整的IP地址管理功能
- ✅ 用户认证和权限系统
- ✅ 网段管理和自动IP生成
- ✅ 部门管理和关联
- ✅ 安全监控和审计日志
- ✅ 现代化Web界面
- ✅ Docker容器化部署

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

---

**项目状态**: 生产就绪 ✅  
**最后更新**: 2025年9月11日