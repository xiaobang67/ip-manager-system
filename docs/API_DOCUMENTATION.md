# IPAM系统API文档

## 概述

IPAM（IP地址管理）系统提供RESTful API接口，用于管理IP地址、网段、用户等资源。所有API接口都需要进行身份认证，并返回JSON格式的数据。

## 基础信息

- **Base URL**: `https://your-domain.com/api`
- **API版本**: v1
- **认证方式**: JWT Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

## 认证

### JWT Token认证

所有API请求（除了登录接口）都需要在请求头中包含JWT token：

```http
Authorization: Bearer <your-jwt-token>
```

### 获取Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

**响应示例:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin"
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "请求参数无效",
    "details": {
      "field": "ip_address",
      "reason": "IP地址格式不正确"
    }
  }
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INVALID_CREDENTIALS | 401 | 用户名或密码错误 |
| TOKEN_EXPIRED | 401 | Token已过期 |
| INSUFFICIENT_PERMISSIONS | 403 | 权限不足 |
| INVALID_IP_FORMAT | 422 | IP地址格式无效 |
| IP_ALREADY_ALLOCATED | 422 | IP地址已被分配 |
| SUBNET_NOT_FOUND | 404 | 网段不存在 |
| RESOURCE_NOT_FOUND | 404 | 资源不存在 |
| INTERNAL_SERVER_ERROR | 500 | 服务器内部错误 |

## API接口

### 1. 认证接口

#### 1.1 用户登录

```http
POST /api/auth/login
```

**请求参数:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "theme": "light"
  }
}
```

#### 1.2 用户登出

```http
POST /api/auth/logout
```

**响应:**
```json
{
  "message": "登出成功"
}
```

#### 1.3 刷新Token

```http
POST /api/auth/refresh
```

**响应:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 1.4 获取用户信息

```http
GET /api/auth/profile
```

**响应:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "theme": "light",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 1.5 更新用户信息

```http
PUT /api/auth/profile
```

**请求参数:**
```json
{
  "email": "newemail@example.com",
  "theme": "dark"
}
```

#### 1.6 修改密码

```http
PUT /api/auth/password
```

**请求参数:**
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

### 2. IP地址管理接口

#### 2.1 获取IP地址列表

```http
GET /api/ips
```

**查询参数:**
- `page` (int): 页码，默认1
- `size` (int): 每页数量，默认50
- `subnet_id` (int): 网段ID过滤
- `status` (string): 状态过滤 (available, allocated, reserved)
- `search` (string): 搜索关键词
- `sort` (string): 排序字段，默认ip_address
- `order` (string): 排序方向 (asc, desc)，默认asc

**响应:**
```json
{
  "data": [
    {
      "id": 1,
      "ip_address": "192.168.1.100",
      "subnet_id": 1,
      "status": "allocated",
      "mac_address": "00:11:22:33:44:55",
      "hostname": "server01",
      "device_type": "server",
      "location": "机房A",
      "assigned_to": "张三",
      "description": "Web服务器",
      "allocated_at": "2024-01-01T10:00:00Z",
      "allocated_by": 1,
      "tags": ["production", "web"],
      "custom_fields": {
        "department": "IT部门",
        "contact": "zhangsan@example.com"
      },
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 1000,
    "pages": 20
  }
}
```

#### 2.2 分配IP地址

```http
POST /api/ips/allocate
```

**请求参数:**
```json
{
  "subnet_id": 1,
  "ip_address": "192.168.1.100",  // 可选，不指定则自动分配
  "mac_address": "00:11:22:33:44:55",
  "hostname": "server01",
  "device_type": "server",
  "location": "机房A",
  "assigned_to": "张三",
  "description": "Web服务器",
  "tags": ["production", "web"],
  "custom_fields": {
    "department": "IT部门"
  }
}
```

**响应:**
```json
{
  "id": 1,
  "ip_address": "192.168.1.100",
  "status": "allocated",
  "allocated_at": "2024-01-01T10:00:00Z",
  "message": "IP地址分配成功"
}
```

#### 2.3 保留IP地址

```http
PUT /api/ips/{ip_address}/reserve
```

**请求参数:**
```json
{
  "reason": "为新服务器预留",
  "reserved_until": "2024-12-31T23:59:59Z"  // 可选
}
```

#### 2.4 释放IP地址

```http
PUT /api/ips/{ip_address}/release
```

**请求参数:**
```json
{
  "reason": "设备下线"
}
```

#### 2.5 搜索IP地址

```http
GET /api/ips/search
```

**查询参数:**
- `q` (string): 搜索关键词
- `fields` (string): 搜索字段，逗号分隔 (ip_address,hostname,mac_address,description)
- `subnet_id` (int): 限制搜索范围
- `status` (string): 状态过滤
- `tags` (string): 标签过滤，逗号分隔

#### 2.6 获取IP地址历史

```http
GET /api/ips/{ip_address}/history
```

**响应:**
```json
{
  "data": [
    {
      "id": 1,
      "action": "allocate",
      "old_values": {},
      "new_values": {
        "status": "allocated",
        "hostname": "server01"
      },
      "user_id": 1,
      "user_name": "admin",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### 2.7 IP冲突检测

```http
POST /api/ips/conflict-check
```

**请求参数:**
```json
{
  "ip_addresses": ["192.168.1.100", "192.168.1.101"]
}
```

### 3. 网段管理接口

#### 3.1 获取网段列表

```http
GET /api/subnets
```

**查询参数:**
- `page` (int): 页码
- `size` (int): 每页数量
- `search` (string): 搜索关键词
- `vlan_id` (int): VLAN ID过滤

**响应:**
```json
{
  "data": [
    {
      "id": 1,
      "network": "192.168.1.0/24",
      "netmask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "description": "办公网络",
      "vlan_id": 100,
      "location": "总部",
      "total_ips": 254,
      "allocated_ips": 50,
      "available_ips": 204,
      "utilization": 19.69,
      "tags": ["office", "internal"],
      "created_by": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 10,
    "pages": 1
  }
}
```

#### 3.2 创建网段

```http
POST /api/subnets
```

**请求参数:**
```json
{
  "network": "192.168.2.0/24",
  "gateway": "192.168.2.1",
  "description": "新办公网络",
  "vlan_id": 200,
  "location": "分部",
  "tags": ["office", "branch"]
}
```

#### 3.3 更新网段

```http
PUT /api/subnets/{id}
```

#### 3.4 删除网段

```http
DELETE /api/subnets/{id}
```

#### 3.5 获取网段下的IP列表

```http
GET /api/subnets/{id}/ips
```

#### 3.6 验证网段格式

```http
POST /api/subnets/validate
```

**请求参数:**
```json
{
  "network": "192.168.1.0/24"
}
```

### 4. 用户管理接口

#### 4.1 获取用户列表

```http
GET /api/users
```

**响应:**
```json
{
  "data": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com",
      "role": "admin",
      "is_active": true,
      "last_login": "2024-01-01T10:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 4.2 创建用户

```http
POST /api/users
```

**请求参数:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "password123",
  "role": "user"
}
```

#### 4.3 更新用户

```http
PUT /api/users/{id}
```

#### 4.4 删除用户

```http
DELETE /api/users/{id}
```

#### 4.5 更新用户角色

```http
PUT /api/users/{id}/role
```

**请求参数:**
```json
{
  "role": "manager"
}
```

#### 4.6 获取用户权限

```http
GET /api/users/{id}/permissions
```

### 5. 报告接口

#### 5.1 获取仪表盘数据

```http
GET /api/reports/dashboard
```

**响应:**
```json
{
  "summary": {
    "total_subnets": 10,
    "total_ips": 2540,
    "allocated_ips": 500,
    "available_ips": 2040,
    "reserved_ips": 0,
    "utilization": 19.69
  },
  "subnet_utilization": [
    {
      "subnet_id": 1,
      "network": "192.168.1.0/24",
      "utilization": 19.69,
      "total_ips": 254,
      "allocated_ips": 50
    }
  ],
  "recent_activities": [
    {
      "action": "allocate",
      "ip_address": "192.168.1.100",
      "user": "admin",
      "timestamp": "2024-01-01T10:00:00Z"
    }
  ]
}
```

#### 5.2 获取使用率报告

```http
GET /api/reports/utilization
```

**查询参数:**
- `subnet_id` (int): 特定网段
- `start_date` (string): 开始日期 (YYYY-MM-DD)
- `end_date` (string): 结束日期 (YYYY-MM-DD)
- `format` (string): 输出格式 (json, csv, pdf)

#### 5.3 获取清单报告

```http
GET /api/reports/inventory
```

#### 5.4 导出报告

```http
POST /api/reports/export
```

**请求参数:**
```json
{
  "report_type": "utilization",
  "format": "pdf",
  "filters": {
    "subnet_id": 1,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31"
  }
}
```

#### 5.5 获取告警

```http
GET /api/reports/alerts
```

### 6. 标签管理接口

#### 6.1 获取标签列表

```http
GET /api/tags
```

#### 6.2 创建标签

```http
POST /api/tags
```

**请求参数:**
```json
{
  "name": "production",
  "color": "#ff0000",
  "description": "生产环境"
}
```

#### 6.3 更新标签

```http
PUT /api/tags/{id}
```

#### 6.4 删除标签

```http
DELETE /api/tags/{id}
```

### 7. 自定义字段接口

#### 7.1 获取自定义字段

```http
GET /api/custom-fields
```

**查询参数:**
- `entity_type` (string): 实体类型 (ip, subnet)

#### 7.2 创建自定义字段

```http
POST /api/custom-fields
```

**请求参数:**
```json
{
  "entity_type": "ip",
  "field_name": "department",
  "field_type": "text",
  "is_required": false,
  "field_options": null
}
```

### 8. 审计日志接口

#### 8.1 获取审计日志

```http
GET /api/audit-logs
```

**查询参数:**
- `user_id` (int): 用户ID过滤
- `action` (string): 操作类型过滤
- `entity_type` (string): 实体类型过滤
- `start_date` (string): 开始日期
- `end_date` (string): 结束日期
- `page` (int): 页码
- `size` (int): 每页数量

**响应:**
```json
{
  "data": [
    {
      "id": 1,
      "user_id": 1,
      "user_name": "admin",
      "action": "CREATE",
      "entity_type": "ip",
      "entity_id": 1,
      "old_values": null,
      "new_values": {
        "ip_address": "192.168.1.100",
        "status": "allocated"
      },
      "ip_address": "192.168.1.10",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2024-01-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "size": 50,
    "total": 1000,
    "pages": 20
  }
}
```

### 9. 系统配置接口

#### 9.1 获取系统配置

```http
GET /api/system/config
```

#### 9.2 更新系统配置

```http
PUT /api/system/config
```

**请求参数:**
```json
{
  "smtp_host": "smtp.example.com",
  "smtp_port": 587,
  "alert_email": "admin@example.com",
  "backup_retention_days": 30
}
```

### 10. 健康检查接口

#### 10.1 系统健康检查

```http
GET /api/health
```

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T10:00:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "response_time": 5
    },
    "redis": {
      "status": "healthy",
      "response_time": 2
    }
  },
  "metrics": {
    "uptime": 86400,
    "memory_usage": 45.2,
    "cpu_usage": 12.5
  }
}
```

## 数据模型

### IP地址模型

```json
{
  "id": 1,
  "ip_address": "192.168.1.100",
  "subnet_id": 1,
  "status": "allocated|available|reserved|conflict",
  "mac_address": "00:11:22:33:44:55",
  "hostname": "server01",
  "device_type": "server",
  "location": "机房A",
  "assigned_to": "张三",
  "description": "Web服务器",
  "allocated_at": "2024-01-01T10:00:00Z",
  "allocated_by": 1,
  "tags": ["production", "web"],
  "custom_fields": {},
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

### 网段模型

```json
{
  "id": 1,
  "network": "192.168.1.0/24",
  "netmask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "description": "办公网络",
  "vlan_id": 100,
  "location": "总部",
  "total_ips": 254,
  "allocated_ips": 50,
  "available_ips": 204,
  "utilization": 19.69,
  "tags": ["office", "internal"],
  "created_by": 1,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### 用户模型

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin|manager|user",
  "theme": "light|dark",
  "is_active": true,
  "last_login": "2024-01-01T10:00:00Z",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## 权限系统

### 角色权限矩阵

| 功能 | 超级管理员 | 网络管理员 | 只读用户 |
|------|-----------|-----------|----------|
| 查看IP地址 | ✓ | ✓ | ✓ |
| 分配IP地址 | ✓ | ✓ | ✗ |
| 释放IP地址 | ✓ | ✓ | ✗ |
| 管理网段 | ✓ | ✓ | ✗ |
| 用户管理 | ✓ | ✗ | ✗ |
| 系统配置 | ✓ | ✗ | ✗ |
| 查看报告 | ✓ | ✓ | ✓ |
| 导出数据 | ✓ | ✓ | ✗ |

### 权限检查

所有需要权限的接口都会检查用户的角色和权限。如果权限不足，将返回403错误。

## 限流策略

为了保护系统免受滥用，API实施了以下限流策略：

- **登录接口**: 每分钟最多5次尝试
- **一般API**: 每秒最多10个请求
- **搜索接口**: 每秒最多5个请求
- **导出接口**: 每分钟最多2个请求

## 示例代码

### JavaScript/Axios示例

```javascript
// 配置axios实例
const api = axios.create({
  baseURL: 'https://your-domain.com/api',
  timeout: 10000
});

// 添加认证拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 登录
async function login(username, password) {
  try {
    const response = await api.post('/auth/login', {
      username,
      password
    });
    
    localStorage.setItem('access_token', response.data.access_token);
    return response.data;
  } catch (error) {
    console.error('登录失败:', error.response.data);
    throw error;
  }
}

// 获取IP地址列表
async function getIPAddresses(params = {}) {
  try {
    const response = await api.get('/ips', { params });
    return response.data;
  } catch (error) {
    console.error('获取IP地址列表失败:', error);
    throw error;
  }
}

// 分配IP地址
async function allocateIP(data) {
  try {
    const response = await api.post('/ips/allocate', data);
    return response.data;
  } catch (error) {
    console.error('分配IP地址失败:', error);
    throw error;
  }
}
```

### Python/Requests示例

```python
import requests
import json

class IPAMClient:
    def __init__(self, base_url, username=None, password=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.token = None
        
        if username and password:
            self.login(username, password)
    
    def login(self, username, password):
        """用户登录"""
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"username": username, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.token = data['access_token']
        self.session.headers.update({
            'Authorization': f"Bearer {self.token}"
        })
        return data
    
    def get_ip_addresses(self, **params):
        """获取IP地址列表"""
        response = self.session.get(
            f"{self.base_url}/ips",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def allocate_ip(self, **data):
        """分配IP地址"""
        response = self.session.post(
            f"{self.base_url}/ips/allocate",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_subnets(self, **params):
        """获取网段列表"""
        response = self.session.get(
            f"{self.base_url}/subnets",
            params=params
        )
        response.raise_for_status()
        return response.json()

# 使用示例
client = IPAMClient("https://your-domain.com/api", "admin", "password")

# 获取IP地址列表
ips = client.get_ip_addresses(subnet_id=1, status="available")

# 分配IP地址
result = client.allocate_ip(
    subnet_id=1,
    hostname="server01",
    device_type="server",
    assigned_to="张三"
)
```

## 版本更新

### v1.0.0 (当前版本)
- 基础IP地址管理功能
- 网段管理功能
- 用户认证和权限管理
- 基础报告功能

### 计划中的功能
- IPv6支持
- DHCP集成
- DNS集成
- 更多报告类型
- 移动端API优化

## 支持

如果您在使用API时遇到问题，请：

1. 查看错误响应中的详细信息
2. 检查请求参数和格式
3. 确认认证token是否有效
4. 查看系统日志获取更多信息
5. 联系技术支持：api-support@your-domain.com