# 企业IP地址管理系统

## 项目简介
企业内部IP地址管理系统，用于管理企业内部复杂的IP地址分配、网段规划和地址保留等功能。

## 技术栈
- 前端：Vue.js 3
- 后端：Python FastAPI
- 数据库：MySQL
- 其他：Element Plus (UI组件库)

## 功能特性
- IP地址管理（增删改查）
- 网段管理（增删改查）
- 地址保留功能
- 使用者管理（用户、部门）
- 网段使用范围管理

## 项目结构
```
ipmanagersystem/
├── backend/                 # 后端API服务
│   ├── app/                # 应用主目录
│   ├── models/             # 数据模型
│   ├── api/                # API路由
│   ├── services/           # 业务逻辑
│   ├── database/           # 数据库配置
│   └── requirements.txt    # Python依赖
├── frontend/               # 前端Vue应用
│   ├── src/               # 源代码
│   ├── components/        # 组件
│   ├── views/             # 页面视图
│   └── package.json       # Node.js依赖
├── database/              # 数据库脚本
└── docs/                  # 项目文档
```

## 快速开始

### Docker一键部署（推荐）

1. 安装 [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. 双击运行 `start.bat` 脚本
3. 等待自动构建和启动完成
4. 浏览器自动打开 http://localhost

详细部署说明请参考 [Docker部署指南](docs/docker-deployment.md)

### 手动安装

### 环境要求
- Python 3.8+
- Node.js 16+
- MySQL 8.0+

### 安装步骤
1. 克隆项目
2. 安装后端依赖：`pip install -r backend/requirements.txt`
3. 安装前端依赖：`npm install`
4. 配置数据库
5. 启动服务

详细安装说明请参考 docs/installation.md