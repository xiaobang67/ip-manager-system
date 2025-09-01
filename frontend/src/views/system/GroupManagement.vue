<template>
  <div class="group-management">
    <div class="page-header">
      <div class="header-content">
        <h1>用户组管理</h1>
        <p>管理用户组和权限配置</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增组
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索组名、显示名称"
            clearable
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="4">
          <el-select v-model="searchForm.is_active" placeholder="状态筛选" clearable>
            <el-option label="全部" :value="null" />
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 组列表 -->
    <div class="table-section">
      <el-table
        v-loading="loading"
        :data="groupList"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="name" label="组名" width="150" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="user_count" label="用户数量" width="100">
          <template #default="{ row }">
            <el-tag type="info">{{ row.user_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="权限" width="200">
          <template #default="{ row }">
            <el-tag 
              v-for="permission in row.permissions.slice(0, 3)" 
              :key="permission"
              size="small"
              style="margin-right: 5px;"
            >
              {{ getPermissionLabel(permission) }}
            </el-tag>
            <el-tag v-if="row.permissions.length > 3" size="small" type="info">
              +{{ row.permissions.length - 3 }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleGroupStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteGroup(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </div>

    <!-- 创建/编辑组对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑组' : '新增组'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="groupFormRef"
        :model="groupForm"
        :rules="groupRules"
        label-width="100px"
      >
        <el-form-item label="组名" prop="name">
          <el-input 
            v-model="groupForm.name" 
            :disabled="isEditing"
            placeholder="请输入组名"
          />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="groupForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="groupForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入组描述"
          />
        </el-form-item>
        
        <el-form-item label="权限配置">
          <el-checkbox-group v-model="groupForm.permissions">
            <div class="permission-section">
              <h4>基础权限</h4>
              <el-checkbox label="user">普通用户</el-checkbox>
              <el-checkbox label="admin">管理员</el-checkbox>
              <el-checkbox label="superuser">超级管理员</el-checkbox>
            </div>
            <div class="permission-section">
              <h4>功能权限</h4>
              <el-checkbox label="ip_management">IP管理</el-checkbox>
              <el-checkbox label="network_management">网段管理</el-checkbox>
              <el-checkbox label="user_management">用户管理</el-checkbox>
              <el-checkbox label="system_settings">系统设置</el-checkbox>
            </div>
            <div class="permission-section">
              <h4>数据权限</h4>
              <el-checkbox label="data_export">数据导出</el-checkbox>
              <el-checkbox label="data_import">数据导入</el-checkbox>
              <el-checkbox label="data_delete">数据删除</el-checkbox>
            </div>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ isEditing ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, ElForm } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import type { AuthGroupData, CreateGroupRequest, UpdateGroupRequest } from '@/api/auth'

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const groupList = ref<AuthGroupData[]>([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const currentGroupId = ref<number | null>(null)

// 表单引用
const groupFormRef = ref<InstanceType<typeof ElForm>>()

// 搜索表单
const searchForm = reactive({
  search: '',
  is_active: null as boolean | null
})

// 分页数据
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 组表单
const groupForm = reactive<CreateGroupRequest & { id?: number }>({
  name: '',
  display_name: '',
  description: '',
  permissions: []
})

// 表单验证规则
const groupRules = {
  name: [
    { required: true, message: '请输入组名', trigger: 'blur' },
    { min: 2, max: 50, message: '组名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' }
  ]
}

// 权限标签映射
const permissionLabels: Record<string, string> = {
  user: '普通用户',
  admin: '管理员',
  superuser: '超级管理员',
  ip_management: 'IP管理',
  network_management: '网段管理',
  user_management: '用户管理',
  system_settings: '系统设置',
  data_export: '数据导出',
  data_import: '数据导入',
  data_delete: '数据删除'
}

// 方法
const getPermissionLabel = (permission: string) => {
  return permissionLabels[permission] || permission
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadGroups = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      ...searchForm
    }
    
    // 清空空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null) {
        delete params[key]
      }
    })

    const data = await authApi.getGroups(params)
    groupList.value = data
    // 注意：需要根据实际API返回结构调整总数获取
    // pagination.total = data.total
  } catch (error) {
    ElMessage.error('加载组列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadGroups()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    is_active: null
  })
  handleSearch()
}

const showCreateDialog = () => {
  isEditing.value = false
  dialogVisible.value = true
  resetForm()
}

const showEditDialog = (group: AuthGroupData) => {
  isEditing.value = true
  currentGroupId.value = group.id
  dialogVisible.value = true
  
  // 填充表单数据
  Object.assign(groupForm, {
    name: group.name,
    display_name: group.display_name,
    description: group.description,
    permissions: [...group.permissions]
  })
}

const resetForm = () => {
  Object.assign(groupForm, {
    name: '',
    display_name: '',
    description: '',
    permissions: []
  })
  groupFormRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!groupFormRef.value) return
  
  try {
    await groupFormRef.value.validate()
    
    submitLoading.value = true
    
    if (isEditing.value && currentGroupId.value) {
      // 编辑组
      const updateData: UpdateGroupRequest = {
        display_name: groupForm.display_name,
        description: groupForm.description,
        permissions: groupForm.permissions
      }
      
      await authApi.updateGroup(currentGroupId.value, updateData)
      ElMessage.success('组更新成功')
    } else {
      // 创建组
      await authApi.createGroup(groupForm)
      ElMessage.success('组创建成功')
    }
    
    dialogVisible.value = false
    loadGroups()
  } catch (error) {
    console.error('提交组数据失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const toggleGroupStatus = async (group: AuthGroupData) => {
  try {
    await ElMessageBox.confirm(
      `确定要${group.is_active ? '禁用' : '启用'}组 ${group.name} 吗？`,
      '确认操作',
      { type: 'warning' }
    )
    
    await authApi.updateGroup(group.id, { is_active: !group.is_active })
    ElMessage.success(`组${group.is_active ? '禁用' : '启用'}成功`)
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换组状态失败:', error)
    }
  }
}

const deleteGroup = async (group: AuthGroupData) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除组 ${group.name} 吗？此操作不可恢复！`,
      '确认删除',
      { type: 'error' }
    )
    
    await authApi.deleteGroup(group.id)
    ElMessage.success('组删除成功')
    loadGroups()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除组失败:', error)
    }
  }
}

// 生命周期
onMounted(() => {
  loadGroups()
})
</script>

<style scoped>
.group-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.header-content h1 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.header-content p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f9f9f9;
  border-radius: 8px;
}

.table-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.pagination-section {
  padding: 20px;
  text-align: right;
  border-top: 1px solid #eee;
}

.permission-section {
  margin-bottom: 15px;
}

.permission-section h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}

.permission-section .el-checkbox {
  margin-right: 20px;
  margin-bottom: 10px;
}

/* Element Plus 样式覆盖 */
:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

:deep(.el-dialog__header) {
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}

:deep(.el-dialog__body) {
  padding-top: 20px;
}

:deep(.el-checkbox-group) {
  max-height: 300px;
  overflow-y: auto;
}
</style>