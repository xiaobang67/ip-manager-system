# 只读角色实现文档

## 概述

本文档描述了IP管理系统中只读角色的实现，该角色专门用于IP地址查询，具有以下特点：

- 只能访问网络资源管理-IP地址管理模块
- 只允许使用搜索框进行IP地址查询
- 不显示任何操作按钮（分配、编辑、保留、删除、释放、批量操作等）
- 只能查看IP地址信息和统计数据

## ✅ 实现状态

**已完成并测试通过！** 所有功能已成功实现并部署。

## 实现内容

### 1. 后端实现

#### 1.1 用户角色模型更新
- 文件：`backend/app/models/user.py`
- 在 `UserRole` 枚举中添加了 `READONLY = "readonly"` 角色

#### 1.2 权限控制更新
- 文件：`backend/app/core/dependencies.py`
- 更新角色层级，将 `READONLY` 设为最低权限级别（0级）
- 添加 `require_write_permission()` 函数，阻止只读用户执行写操作

#### 1.3 API权限控制
- 文件：`backend/app/api/v1/endpoints/ips.py`
- 为所有写操作API添加 `require_write_permission` 依赖：
  - IP分配 (`/allocate`)
  - IP保留 (`/reserve`)
  - IP释放 (`/release`)
  - IP删除 (`/delete`)
- 保持查询操作对所有用户开放：
  - IP列表查询 (`/`)
  - IP搜索 (`/search`, `/advanced-search`)
  - 统计信息 (`/statistics`)
  - 历史记录 (`/{ip_address}/history`)

#### 1.4 数据库迁移
- 文件：`backend/add_readonly_role_migration.py`
- 更新MySQL数据库中的用户角色枚举类型，添加 `readonly` 选项

#### 1.5 只读用户创建脚本
- 文件：`backend/create_readonly_user.py`
- 提供创建只读用户的便捷脚本
- 默认创建用户名为 `readonly`，密码为 `readonly123` 的只读用户

### 2. 前端实现

#### 2.1 权限控制
- 文件：`frontend/src/views/IPManagement.vue`
- 添加 `isReadonly` 计算属性，判断当前用户是否为只读用户
- 为只读用户隐藏以下UI元素：
  - 头部的"批量操作"按钮
  - 表格的选择列
  - 表格的"操作"列（包含所有操作按钮）

#### 2.2 路由权限控制
- 文件：`frontend/src/router/index.js`
- 为IP管理页面添加 `allowReadonly: true` 元数据
- 在路由守卫中添加只读用户的访问控制逻辑
- 只读用户只能访问仪表盘和IP管理页面

### 3. 部署脚本
- 文件：`run-readonly-migration.bat`
- 一键运行数据库迁移和创建只读用户的批处理脚本

## 使用方法

### 1. 部署只读角色功能

运行以下命令来部署只读角色功能：

```bash
# Windows
run-readonly-migration.bat

# Linux/Mac
python backend/add_readonly_role_migration.py
python backend/create_readonly_user.py
```

### 2. 创建自定义只读用户

```bash
python backend/create_readonly_user.py --username 自定义用户名 --password 自定义密码 --email 邮箱地址
```

### 3. 只读用户登录

使用以下默认凭据登录：
- 用户名：`readonly`
- 密码：`readonly123`

## 功能限制

### 只读用户可以访问的功能：
- ✅ 仪表盘
- ✅ IP地址管理页面
- ✅ IP地址搜索和查询
- ✅ 查看IP地址详细信息
- ✅ 查看统计信息
- ✅ 查看IP地址历史记录

### 只读用户无法访问的功能：
- ❌ IP地址分配
- ❌ IP地址编辑
- ❌ IP地址保留
- ❌ IP地址释放
- ❌ IP地址删除
- ❌ 批量操作
- ❌ 用户管理
- ❌ 部门管理
- ❌ 子网管理
- ❌ 设备类型管理

## 安全特性

1. **后端API保护**：所有写操作API都通过 `require_write_permission` 依赖进行保护
2. **前端UI隐藏**：只读用户看不到任何操作按钮，避免误操作
3. **路由限制**：只读用户只能访问允许的页面
4. **权限层级**：只读角色为最低权限级别，无法执行任何写操作

## 测试建议

1. 使用只读用户登录系统
2. 验证只能看到搜索框，无法看到操作按钮
3. 尝试直接访问其他管理页面，应被重定向
4. 验证搜索功能正常工作
5. 确认统计信息正常显示

## 注意事项

1. 只读用户创建后，管理员可以在用户管理页面中修改其权限
2. 如需批量创建只读用户，可以修改创建脚本或在用户管理界面操作
3. 只读角色主要用于查询场景，如需要更细粒度的权限控制，可以扩展权限系统
4. 建议为只读用户设置强密码，并定期更换

## 扩展建议

如果需要更灵活的权限控制，可以考虑：

1. 实现基于资源的权限控制（RBAC）
2. 添加部门级别的权限控制
3. 实现IP地址范围的访问控制
4. 添加审计日志功能，记录只读用户的查询行为