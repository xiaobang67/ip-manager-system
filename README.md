# IP地址管理系统 (IPAM)

企业级IP地址管理系统，采用Vue.js前端、Python FastAPI后端和MySQL数据库的现代化架构。

## 项目结构

```
ipam/
├── frontend/           # Vue.js 前端应用
│   ├── src/
│   │   ├── components/ # Vue组件
│   │   ├── views/      # 页面视图
│   │   ├── router/     # 路由配置
│   │   ├── store/      # Vuex状态管理
│   │   └── main.js     # 应用入口
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── backend/            # Python FastAPI 后端
│   ├── app/
│   │   ├── api/        # API路由
│   │   ├── core/       # 核心配置
│   │   ├── models/     # 数据模型
│   │   └── services/   # 业务逻辑
│   ├── alembic/        # 数据库迁移
│   ├── requirements.txt
│   ├── main.py
│   └── Dockerfile
├── database/           # 数据库脚本
│   └── init.sql
├── docker-compose.yml  # Docker编排配置
└── README.md
```

## 技术栈

### 前端
- **Vue.js 3** - 渐进式JavaScript框架
- **Vue Router** - 官方路由管理器
- **Vuex** - 状态管理模式
- **Element Plus** - Vue 3 UI组件库
- **Vite** - 现代化构建工具

### 后端
- **FastAPI** - 现代化Python Web框架
- **SQLAlchemy** - Python SQL工具包和ORM
- **Alembic** - 数据库迁移工具
- **Pydantic** - 数据验证库
- **Uvicorn** - ASGI服务器

### 数据库
- **MySQL 8.0** - 关系型数据库
- **Redis** - 内存数据库（缓存）

## 快速开始

### 环境要求
- Docker & Docker Compose
- Node.js 16+ (开发环境)
- Python 3.9+ (开发环境)

### 使用Docker启动

1. 克隆项目
```bash
git clone <repository-url>
cd ipam
```

2. 复制环境配置文件
```bash
cp .env.example .env
```

3. 启动所有服务
```bash
docker-compose up -d
```

4. 访问应用
- 前端: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 开发环境设置

#### 前端开发
```bash
cd frontend
npm install
npm run dev
```

#### 后端开发
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

## 功能模块

- ✅ 项目基础架构
- 🚧 用户认证系统
- 🚧 IP地址管理
- 🚧 网段管理
- 🚧 用户管理
- 🚧 监控仪表盘
- 🚧 审计日志

## 开发指南

### 数据库迁移
```bash
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
```

### 测试
```bash
# 后端测试
cd backend
pytest

# 前端测试
cd frontend
npm run test
```

## 部署

生产环境部署请参考 `docker-compose.yml` 配置，确保：
1. 修改默认密码
2. 配置SSL证书
3. 设置环境变量
4. 配置备份策略

## 许可证

MIT License