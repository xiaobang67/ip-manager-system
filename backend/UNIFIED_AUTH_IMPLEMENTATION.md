# 统一认证服务实现文档

## 概述

本文档描述了IPAM系统中统一认证服务的实现，确保所有密码操作都使用bcrypt哈希格式，提供一致的认证接口。

## 核心组件

### 1. 统一认证服务 (`auth_service.py`)

这是核心认证服务模块，提供了所有密码相关操作的统一接口。

#### 主要功能

- **用户认证**: `authenticate_user(username, password)`
- **密码修改**: `change_user_password(user_id, old_password, new_password)`
- **密码重置**: `reset_user_password(username, new_password)`
- **创建用户**: `create_user(username, password, email, role)`
- **密码验证**: `verify_user_password(username, password)`
- **用户查询**: `get_user_by_username(username)`, `get_user_by_id(user_id)`

#### 核心特性

1. **统一哈希格式**: 所有密码都使用bcrypt哈希
2. **安全验证**: 使用passlib库进行密码验证
3. **错误处理**: 完善的异常处理和日志记录
4. **数据库事务**: 确保数据一致性

### 2. 安全模块 (`app/core/security.py`)

提供底层的密码加密和JWT token功能。

#### 主要功能

- `get_password_hash(password)`: 生成bcrypt哈希
- `verify_password(plain_password, hashed_password)`: 验证密码
- `create_access_token(data)`: 创建访问令牌
- `create_refresh_token(data)`: 创建刷新令牌
- `verify_token(token, token_type)`: 验证JWT令牌

### 3. 主应用集成 (`enhanced_main.py`)

主应用已更新为使用统一认证服务：

- 登录端点使用 `authenticate_user()`
- 密码修改端点使用 `change_user_password()`
- 所有认证操作都通过统一服务

## 密码哈希迁移

### 迁移工具

1. **`fix_user_passwords.py`**: 将SHA256哈希转换为bcrypt哈希
2. **`reset_user_passwords.py`**: 重置用户密码为已知值
3. **`fix_all_passwords.py`**: 一键执行所有修复操作

### 迁移过程

1. 检测现有密码哈希格式
2. 尝试匹配常见密码的SHA256哈希
3. 将匹配的密码转换为bcrypt哈希
4. 验证转换结果

## API端点

### 认证相关端点

- `POST /api/auth/login`: 用户登录
- `PUT /api/auth/password`: 修改密码
- `GET /api/auth/profile`: 获取用户资料
- `POST /api/auth/logout`: 用户登出
- `POST /api/auth/refresh`: 刷新令牌

### 请求格式

#### 登录请求
```json
{
  "username": "admin",
  "password": "admin"
}
```

#### 修改密码请求
```json
{
  "old_password": "current_password",
  "new_password": "new_password"
}
```

### 响应格式

#### 登录响应
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin"
  }
}
```

## 测试工具

### 1. 统一认证服务测试 (`test_unified_auth.py`)

测试所有认证服务功能：
- 用户认证
- 密码验证
- 密码修改
- 密码重置
- 用户创建
- 哈希格式检查

### 2. API端点测试 (`test_auth_api.py`)

测试HTTP API端点：
- 登录API
- 密码修改API
- 用户资料API
- 服务器状态检查

## 使用示例

### 基本认证

```python
from auth_service import authenticate_user

# 用户登录
user = authenticate_user("admin", "admin")
if user:
    print(f"登录成功: {user['username']}")
else:
    print("登录失败")
```

### 密码操作

```python
from auth_service import change_user_password, reset_user_password

# 用户修改密码
success = change_user_password(user_id=1, old_password="admin", new_password="newpass123")

# 管理员重置密码
success = reset_user_password("username", "newpass123")
```

### 创建用户

```python
from auth_service import create_new_user

user_id = create_new_user(
    username="newuser",
    password="password123",
    email="user@example.com",
    role="user"
)
```

## 安全特性

### 1. 密码哈希

- 使用bcrypt算法，自动加盐
- 成本因子可配置（默认12轮）
- 抗彩虹表攻击

### 2. JWT令牌

- 访问令牌：30分钟过期
- 刷新令牌：7天过期
- 包含用户ID、用户名、角色信息

### 3. 输入验证

- 密码强度验证
- 用户名格式检查
- SQL注入防护

## 配置选项

### 数据库配置

```python
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'ipam_user'),
    'password': os.getenv('DB_PASSWORD', 'ipam_pass123'),
    'database': os.getenv('DB_NAME', 'ipam'),
    'charset': 'utf8mb4'
}
```

### JWT配置

```python
SECRET_KEY = "your-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

## 部署建议

### 1. 生产环境配置

- 更改默认SECRET_KEY
- 使用环境变量配置数据库
- 启用HTTPS
- 配置适当的CORS策略

### 2. 密码策略

- 强制密码复杂度要求
- 定期密码更换提醒
- 账户锁定机制

### 3. 监控和日志

- 记录所有认证尝试
- 监控异常登录行为
- 定期审计用户权限

## 故障排除

### 常见问题

1. **密码验证失败**
   - 检查密码哈希格式
   - 运行 `test_unified_auth.py` 验证

2. **JWT令牌无效**
   - 检查SECRET_KEY配置
   - 验证令牌过期时间

3. **数据库连接失败**
   - 检查数据库配置
   - 验证网络连接

### 调试工具

```bash
# 检查密码哈希格式
python test_unified_auth.py

# 修复密码哈希
python fix_all_passwords.py

# 测试API端点
python test_auth_api.py
```

## 更新日志

### v1.0.0 (当前版本)

- 实现统一认证服务
- 支持bcrypt密码哈希
- 提供完整的API端点
- 包含测试工具和文档

### 未来计划

- 多因素认证支持
- OAuth2集成
- 密码历史记录
- 账户锁定机制
- 审计日志功能