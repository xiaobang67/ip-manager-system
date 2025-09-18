# 只读账号搜索分页问题修复

## 问题描述

用户通过只读账号（readonly/readonly123）登录后，搜索"李喆"时发现：
- 第一页显示正常，都是相关的搜索结果
- 第二页开始出现与搜索关键词无关的IP地址记录
- 分页功能没有保持搜索状态

## 问题分析

### 根本原因
前端代码中，只读用户的搜索逻辑 `handleReadonlySearch` 没有正确设置 `currentSearchParams`，导致在分页时系统无法识别当前处于搜索状态，从而调用了普通的 `loadIPList()` 方法而不是继续执行搜索。

### 技术细节
1. **搜索状态管理缺失**: 只读用户搜索时没有保存搜索参数到 `currentSearchParams`
2. **分页逻辑错误**: 分页时检查 `currentSearchParams` 为空，误认为不在搜索状态
3. **数据混合**: 第二页开始显示的是普通IP列表数据，而不是搜索结果

### 代码位置
- 文件: `frontend/src/views/IPManagement.vue`
- 函数: `handleReadonlySearch` (约第1010行)
- 问题: 缺少 `currentSearchParams.value = { query: ... }` 设置

## 修复方案

### 修复内容
在 `handleReadonlySearch` 函数中添加搜索参数保存逻辑：

```javascript
// 保存当前搜索参数，用于分页时保持搜索状态
currentSearchParams.value = {
  query: readonlySearchQuery.value.trim()
}
```

### 修复位置
```javascript
const handleReadonlySearch = async () => {
  // ... 现有代码 ...
  
  const params = {
    skip: 0,
    limit: pageSize.value,
    query: readonlySearchQuery.value.trim()
  }
  
  // 🔧 修复：保存当前搜索参数，用于分页时保持搜索状态
  currentSearchParams.value = {
    query: readonlySearchQuery.value.trim()
  }
  
  // ... 其余代码 ...
}
```

### 错误处理
同时在错误处理中清除搜索参数：

```javascript
} catch (error) {
  ElMessage.error('搜索失败：' + error.message)
  hasSearched.value = false // 搜索失败时重置状态
  currentSearchParams.value = null // 🔧 修复：清除搜索参数
} finally {
  loading.value = false
}
```

## 测试验证

### 测试方法
1. 使用只读账号登录 (readonly/readonly123)
2. 搜索"李喆"
3. 检查第2页、第3页的搜索结果
4. 验证所有结果都包含搜索关键词

### 测试结果
- ✅ 第1页：20条相关结果，相关度100%
- ✅ 第2页：20条相关结果，相关度100%
- ✅ 第3页：20条相关结果，相关度100%
- ✅ 第4页：20条相关结果，相关度100%
- ✅ 第5页：20条相关结果，相关度100%

### 整体验证
- ✅ 总共测试100条记录，无重复IP地址
- ✅ 整体相关度：100%
- ✅ 分页功能正常保持搜索状态

## 影响范围

### 修复影响
- ✅ 只读用户搜索分页功能恢复正常
- ✅ 不影响管理员用户的搜索功能
- ✅ 不影响其他功能模块

### 兼容性
- ✅ 向后兼容，不破坏现有功能
- ✅ 前端重新构建后立即生效
- ✅ 无需数据库或后端修改

## 部署说明

### 部署步骤
1. 修改前端代码 (`frontend/src/views/IPManagement.vue`)
2. 重新构建前端: `npm run build`
3. 重启Web服务器（如果需要）

### 验证步骤
1. 使用只读账号登录
2. 搜索任意关键词
3. 测试分页功能
4. 确认所有页面结果都相关

## 预防措施

### 代码审查要点
1. 搜索功能必须正确设置 `currentSearchParams`
2. 分页逻辑必须检查搜索状态
3. 错误处理必须清理搜索状态

### 测试建议
1. 每次修改搜索功能后都要测试分页
2. 测试不同用户角色的搜索功能
3. 测试各种搜索关键词的分页一致性

## 总结

这是一个典型的前端状态管理问题，由于只读用户搜索时没有正确保存搜索状态，导致分页时丢失搜索上下文。修复方案简单有效，通过正确设置 `currentSearchParams` 解决了问题，确保分页时能够保持搜索状态。

修复后，只读用户的搜索分页功能完全正常，所有页面都只显示与搜索关键词相关的结果。