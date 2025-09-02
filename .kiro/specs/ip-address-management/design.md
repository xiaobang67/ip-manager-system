# 设计文档

## 概述

企业IP地址管理系统（IPAM）采用现代化的三层架构设计，包括Vue.js前端、Python后端API服务和MySQL数据库。系统设计遵循微服务架构原则，确保高可用性、可扩展性和可维护性。

## 架构

### 系统架构图

```mermaid
graph TB
    subgraph "前端层"
        A[Vue.js 应用]
        B[路由管理]
        C[状态管理 Vuex]
        D[UI组件库]
    end
    
    subgraph "API网关层"
        E[Nginx 反向代理]
        F[负载均衡]
    end
    
    subgraph "后端服务层"
        G[认证服务]
        H[IP管理服务]
        I[网段管理服务]
        J[用户管理服务]
        K[报告服务]
        L[审计服务]
    end
    
    subgraph "数据层"
        M[MySQL 8.0]
        N[Redis 缓存]
        O[日志存储]
    end
    
    A --> E
    E --> G
    E --> H
    E --> I
    E --> J
    E --> K
    E --> L
    G --> M
    H --> M
    I --> M
    J --> M
    K --> M
    L --> O
    G --> N
    H --> N
```

### 技术栈选择

- **前端**: Vue.js 3 + Vue Router + Vuex + Element Plus UI
- **后端**: Python 3.9+ + FastAPI + SQLAlchemy + Alembic
- **数据库**: MySQL 8.0 + Redis 6.0
- **部署**: Docker + Docker Compose
- **监控**: 内置监控仪表盘

## 组件和接口

### 前端组件架构

```mermaid
graph TD
    A[App.vue] --> B[Layout组件]
    B --> C[Header组件]
    B --> D[Sidebar组件]
    B --> E[Main Content]
    
    E --> F[Dashboard]
    E --> G[IP管理模块]
    E --> H[网段管理模块]
    E --> I[用户管理模块]
    E --> J[报告模块]
    
    G --> G1[IP列表组件]
    G --> G2[IP分配组件]
    G --> G3[IP搜索组件]
    
    H --> H1[网段列表组件]
    H --> H2[网段编辑组件]
    H --> H3[网段验证组件]
    
    I --> I1[用户列表组件]
    I --> I2[用户编辑组件]
    I --> I3[权限管理组件]
```

### 后端服务架构

#### 1. 认证服务 (AuthService)
```python
# 接口定义
POST /api/auth/login          # 用户登录
POST /api/auth/logout         # 用户登出
POST /api/auth/refresh        # 刷新token
GET  /api/auth/profile        # 获取用户信息
PUT  /api/auth/profile        # 更新用户信息
PUT  /api/auth/password       # 修改密码
```

#### 2. IP管理服务 (IPService)
```python
# 接口定义
GET    /api/ips               # 获取IP列表
POST   /api/ips/allocate      # 分配IP地址
PUT    /api/ips/{ip}/reserve  # 保留IP地址
PUT    /api/ips/{ip}/release  # 释放IP地址
GET    /api/ips/search        # 搜索IP地址
GET    /api/ips/{ip}/history  # 获取IP历史记录
POST   /api/ips/conflict-check # 冲突检测
```

#### 3. 网段管理服务 (SubnetService)
```python
# 接口定义
GET    /api/subnets           # 获取网段列表
POST   /api/subnets           # 创建网段
PUT    /api/subnets/{id}      # 更新网段
DELETE /api/subnets/{id}      # 删除网段
GET    /api/subnets/{id}/ips  # 获取网段下的IP列表
POST   /api/subnets/validate  # 验证网段格式
```

#### 4. 用户管理服务 (UserService)
```python
# 接口定义
GET    /api/users             # 获取用户列表
POST   /api/users             # 创建用户
PUT    /api/users/{id}        # 更新用户
DELETE /api/users/{id}        # 删除用户
PUT    /api/users/{id}/role   # 更新用户角色
GET    /api/users/{id}/permissions # 获取用户权限
```

#### 5. 报告服务 (ReportService)
```python
# 接口定义
GET    /api/reports/dashboard    # 仪表盘数据
GET    /api/reports/utilization  # 使用率报告
GET    /api/reports/inventory    # 清单报告
POST   /api/reports/export       # 导出报告
GET    /api/reports/alerts       # 获取警报
```

## 数据模型

### 数据库设计

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role ENUM('admin', 'manager', 'user') DEFAULT 'user',
    theme ENUM('light', 'dark') DEFAULT 'light',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 网段表
CREATE TABLE subnets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    network VARCHAR(18) NOT NULL,  -- CIDR格式，如 192.168.1.0/24
    netmask VARCHAR(15) NOT NULL,
    gateway VARCHAR(15),
    description TEXT,
    vlan_id INT,
    location VARCHAR(100),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE KEY unique_network (network)
);

-- IP地址表
CREATE TABLE ip_addresses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ip_address VARCHAR(15) NOT NULL,
    subnet_id INT NOT NULL,
    status ENUM('available', 'allocated', 'reserved', 'conflict') DEFAULT 'available',
    mac_address VARCHAR(17),
    hostname VARCHAR(255),
    device_type VARCHAR(50),
    location VARCHAR(100),
    assigned_to VARCHAR(100),
    description TEXT,
    allocated_at TIMESTAMP NULL,
    allocated_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (subnet_id) REFERENCES subnets(id) ON DELETE CASCADE,
    FOREIGN KEY (allocated_by) REFERENCES users(id),
    UNIQUE KEY unique_ip (ip_address),
    INDEX idx_subnet_status (subnet_id, status),
    INDEX idx_ip_status (ip_address, status)
);

-- 自定义字段表
CREATE TABLE custom_fields (
    id INT PRIMARY KEY AUTO_INCREMENT,
    entity_type ENUM('ip', 'subnet') NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    field_type ENUM('text', 'number', 'date', 'select') NOT NULL,
    field_options JSON,  -- 用于select类型的选项
    is_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 自定义字段值表
CREATE TABLE custom_field_values (
    id INT PRIMARY KEY AUTO_INCREMENT,
    field_id INT NOT NULL,
    entity_id INT NOT NULL,
    entity_type ENUM('ip', 'subnet') NOT NULL,
    field_value TEXT,
    FOREIGN KEY (field_id) REFERENCES custom_fields(id) ON DELETE CASCADE,
    UNIQUE KEY unique_field_entity (field_id, entity_id, entity_type)
);

-- 标签表
CREATE TABLE tags (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#007bff',  -- 十六进制颜色
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IP地址标签关联表
CREATE TABLE ip_tags (
    ip_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (ip_id, tag_id),
    FOREIGN KEY (ip_id) REFERENCES ip_addresses(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 网段标签关联表
CREATE TABLE subnet_tags (
    subnet_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (subnet_id, tag_id),
    FOREIGN KEY (subnet_id) REFERENCES subnets(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- 操作日志表
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(50) NOT NULL,  -- CREATE, UPDATE, DELETE, ALLOCATE, RELEASE
    entity_type VARCHAR(20) NOT NULL,  -- ip, subnet, user
    entity_id INT,
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),  -- 操作者IP
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_action (user_id, action),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_created_at (created_at)
);

-- 系统配置表
CREATE TABLE system_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_by INT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (updated_by) REFERENCES users(id)
);

-- 警报规则表
CREATE TABLE alert_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    rule_type ENUM('utilization', 'conflict', 'expiry') NOT NULL,
    threshold_value DECIMAL(5,2),  -- 阈值，如使用率80%
    subnet_id INT,  -- 可选，针对特定网段的规则
    is_active BOOLEAN DEFAULT TRUE,
    notification_emails TEXT,  -- JSON格式的邮箱列表
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subnet_id) REFERENCES subnets(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 警报历史表
CREATE TABLE alert_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT NOT NULL,
    alert_message TEXT NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium',
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP NULL,
    resolved_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (resolved_by) REFERENCES users(id),
    INDEX idx_rule_created (rule_id, created_at),
    INDEX idx_severity_resolved (severity, is_resolved)
);
```

### 数据模型关系图

```mermaid
erDiagram
    users ||--o{ subnets : creates
    users ||--o{ ip_addresses : allocates
    users ||--o{ audit_logs : performs
    subnets ||--o{ ip_addresses : contains
    ip_addresses ||--o{ ip_tags : has
    subnets ||--o{ subnet_tags : has
    tags ||--o{ ip_tags : tagged_to
    tags ||--o{ subnet_tags : tagged_to
    custom_fields ||--o{ custom_field_values : defines
    alert_rules ||--o{ alert_history : triggers
    subnets ||--o{ alert_rules : monitors
```

## 错误处理

### 错误分类和处理策略

#### 1. 客户端错误 (4xx)
```python
# 错误代码定义
class ErrorCodes:
    # 认证相关
    INVALID_CREDENTIALS = 4001
    TOKEN_EXPIRED = 4002
    INSUFFICIENT_PERMISSIONS = 4003
    
    # 数据验证相关
    INVALID_IP_FORMAT = 4101
    INVALID_SUBNET_FORMAT = 4102
    IP_ALREADY_ALLOCATED = 4103
    SUBNET_OVERLAP = 4104
    
    # 业务逻辑相关
    IP_NOT_FOUND = 4201
    SUBNET_NOT_EMPTY = 4202
    CANNOT_DELETE_ALLOCATED_IP = 4203
```

#### 2. 服务器错误 (5xx)
```python
# 错误处理中间件
class ErrorHandler:
    def handle_database_error(self, error):
        # 数据库连接错误处理
        pass
    
    def handle_network_error(self, error):
        # 网络相关错误处理
        pass
    
    def handle_validation_error(self, error):
        # 数据验证错误处理
        pass
```

#### 3. 前端错误处理
```javascript
// 全局错误处理
const errorHandler = {
  // API错误处理
  handleApiError(error) {
    const { status, data } = error.response;
    switch (status) {
      case 401:
        // 重定向到登录页
        router.push('/login');
        break;
      case 403:
        // 显示权限不足提示
        this.$message.error('权限不足');
        break;
      case 422:
        // 显示验证错误
        this.showValidationErrors(data.errors);
        break;
      default:
        this.$message.error('系统错误，请稍后重试');
    }
  }
};
```

## 测试策略

### 测试金字塔

```mermaid
graph TD
    A[E2E测试] --> B[集成测试]
    B --> C[单元测试]
    
    style A fill:#ff6b6b
    style B fill:#4ecdc4
    style C fill:#45b7d1
```

#### 1. 单元测试 (70%)
- **后端**: 使用pytest测试所有服务层和数据层逻辑
- **前端**: 使用Jest + Vue Test Utils测试组件逻辑

#### 2. 集成测试 (20%)
- API接口测试
- 数据库集成测试
- 第三方服务集成测试

#### 3. E2E测试 (10%)
- 使用Cypress测试关键用户流程
- 跨浏览器兼容性测试

### 测试覆盖率目标
- 单元测试覆盖率: ≥ 90%
- 集成测试覆盖率: ≥ 80%
- E2E测试覆盖率: ≥ 60%

### 性能测试
- 负载测试: 支持1000并发用户
- 压力测试: 数据库查询响应时间 < 100ms
- 容量测试: 支持100万IP地址记录
## 安全设计


### 认证和授权

#### 1. JWT Token认证
```python
# Token结构
{
  "user_id": 123,
  "username": "admin",
  "role": "admin",
  "permissions": ["ip:read", "ip:write", "subnet:manage"],
  "exp": 1640995200,
  "iat": 1640908800
}
```

#### 2. 权限控制矩阵
| 角色 | IP查看 | IP分配 | 网段管理 | 用户管理 | 系统配置 |
|------|--------|--------|----------|----------|----------|
| 超级管理员 | ✓ | ✓ | ✓ | ✓ | ✓ |
| 网络管理员 | ✓ | ✓ | ✓ | ✗ | ✗ |
| 只读用户 | ✓ | ✗ | ✗ | ✗ | ✗ |

#### 3. 数据加密
- 密码使用bcrypt加密存储
- 敏感配置信息使用AES-256加密
- 数据库连接使用SSL/TLS

### 输入验证和防护

#### 1. IP地址验证
```python
import ipaddress
from typing import Union

def validate_ip_address(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_subnet(subnet: str) -> bool:
    try:
        ipaddress.ip_network(subnet, strict=False)
        return True
    except ValueError:
        return False
```

#### 2. SQL注入防护
- 使用SQLAlchemy ORM参数化查询
- 输入数据严格验证和清理
- 数据库用户权限最小化

#### 3. XSS防护
- 前端输出转义
- CSP (Content Security Policy) 头设置
- 输入数据HTML标签过滤

## 性能优化

### 数据库优化

#### 1. 索引策略
```sql
-- 复合索引优化查询
CREATE INDEX idx_ip_subnet_status ON ip_addresses(subnet_id, status, ip_address);
CREATE INDEX idx_audit_user_time ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_subnet_network ON subnets(network);

-- 全文索引支持搜索
CREATE FULLTEXT INDEX idx_ip_search ON ip_addresses(hostname, description);
CREATE FULLTEXT INDEX idx_subnet_search ON subnets(description);
```

#### 2. 查询优化
```python
# 分页查询优化
def get_ip_addresses_paginated(
    page: int = 1, 
    size: int = 50,
    subnet_id: Optional[int] = None,
    status: Optional[str] = None
):
    query = session.query(IPAddress)
    
    if subnet_id:
        query = query.filter(IPAddress.subnet_id == subnet_id)
    if status:
        query = query.filter(IPAddress.status == status)
    
    # 使用offset和limit进行分页
    offset = (page - 1) * size
    return query.offset(offset).limit(size).all()
```

#### 3. 缓存策略
```python
# Redis缓存配置
CACHE_CONFIG = {
    'subnet_list': {'ttl': 300},  # 网段列表缓存5分钟
    'ip_statistics': {'ttl': 60}, # 统计数据缓存1分钟
    'user_permissions': {'ttl': 1800}, # 用户权限缓存30分钟
}

# 缓存装饰器
from functools import wraps
import redis

def cache_result(key_prefix: str, ttl: int = 300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

### 前端性能优化

#### 1. 组件懒加载
```javascript
// 路由懒加载
const routes = [
  {
    path: '/ip-management',
    component: () => import('@/views/IPManagement.vue')
  },
  {
    path: '/subnet-management', 
    component: () => import('@/views/SubnetManagement.vue')
  }
];
```

#### 2. 虚拟滚动
```vue
<!-- 大数据量列表优化 -->
<template>
  <virtual-list
    :data-sources="ipList"
    :data-key="'id'"
    :keeps="50"
    :estimate-size="60"
  >
    <template v-slot="{ record }">
      <ip-list-item :ip="record" />
    </template>
  </virtual-list>
</template>
```

#### 3. 防抖搜索
```javascript
// 搜索防抖优化
import { debounce } from 'lodash';

export default {
  data() {
    return {
      searchQuery: '',
      searchResults: []
    };
  },
  created() {
    this.debouncedSearch = debounce(this.performSearch, 300);
  },
  watch: {
    searchQuery() {
      this.debouncedSearch();
    }
  },
  methods: {
    performSearch() {
      if (this.searchQuery.length >= 2) {
        this.searchIPs(this.searchQuery);
      }
    }
  }
};
```

## 监控和日志

### 应用监控

#### 1. 健康检查端点
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "database": await check_database_connection(),
        "redis": await check_redis_connection()
    }
```

#### 2. 性能指标收集
```python
# 自定义中间件收集请求指标
import time
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # 记录请求指标
        metrics.record_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=process_time
        )
        
        return response
```

### 日志管理

#### 1. 结构化日志
```python
import structlog

logger = structlog.get_logger()

# 业务操作日志
logger.info(
    "IP address allocated",
    ip_address="192.168.1.100",
    user_id=123,
    subnet_id=1,
    action="allocate"
)

# 错误日志
logger.error(
    "Database connection failed",
    error=str(e),
    retry_count=3,
    component="database"
)
```

#### 2. 审计日志
```python
class AuditLogger:
    @staticmethod
    def log_operation(
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: int,
        old_values: dict = None,
        new_values: dict = None
    ):
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            ip_address=get_client_ip(),
            user_agent=get_user_agent()
        )
        session.add(audit_log)
        session.commit()
```

## 部署架构

### Docker容器化

#### 1. 多阶段构建
```dockerfile
# 前端构建
FROM node:16-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ .
RUN npm run build

# 后端构建
FROM python:3.9-slim AS backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .

# 最终镜像
FROM nginx:alpine
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY --from=backend /app /backend
COPY nginx.conf /etc/nginx/nginx.conf
```

#### 2. Docker Compose配置
```yaml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
  
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql://user:pass@mysql:3306/ipam
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mysql
      - redis
  
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: ipam
      MYSQL_USER: ipam_user
      MYSQL_PASSWORD: ipam_pass
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
  
  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  mysql_data:
  redis_data:
```

### 扩展性设计

#### 1. 水平扩展
- 后端API服务无状态设计，支持多实例部署
- 数据库读写分离，支持读副本扩展
- Redis集群支持缓存扩展

#### 2. 微服务拆分准备
```python
# 服务接口抽象
from abc import ABC, abstractmethod

class IPServiceInterface(ABC):
    @abstractmethod
    async def allocate_ip(self, subnet_id: int, user_id: int) -> str:
        pass
    
    @abstractmethod
    async def release_ip(self, ip_address: str, user_id: int) -> bool:
        pass

class SubnetServiceInterface(ABC):
    @abstractmethod
    async def create_subnet(self, network: str, user_id: int) -> int:
        pass
    
    @abstractmethod
    async def delete_subnet(self, subnet_id: int, user_id: int) -> bool:
        pass
```

这个设计文档涵盖了企业级IPAM系统的所有关键技术方面，包括架构设计、数据模型、安全性、性能优化、监控和部署策略。设计遵循了现代软件开发的最佳实践，确保系统的可靠性、可扩展性和可维护性。