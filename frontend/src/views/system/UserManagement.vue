<template>
  <div class="user-management">
    <div class="page-header">
      <div class="header-content">
        <h1>系统用户管理</h1>
        <p>管理系统用户账户和权限</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增系统用户
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索用户名、姓名、邮箱"
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

    <!-- 用户列表 -->
    <div class="table-section">
      <el-table
        v-loading="loading"
        :data="userList"
        style="width: 100%"
        row-key="id"
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="真实姓名" width="120" />
        <el-table-column prop="display_name" label="显示名称" width="120" />
        <el-table-column prop="email" label="邮箱" width="180" />
        <el-table-column prop="employee_id" label="员工编号" width="120" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="danger">超级管理员</el-tag>
            <el-tag v-else-if="row.is_admin" type="warning">管理员</el-tag>
            <el-tag v-else type="info">普通用户</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="last_login" label="最后登录" width="160">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '从未登录' }}
          </template>
        </el-table-column>
        <el-table-column prop="login_count" label="登录次数" width="100" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showEditDialog(row)">编辑</el-button>
            <el-button 
              size="small" 
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="deleteUser(row)"
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

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑用户' : '新增用户'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="userForm.username" 
            :disabled="isEditing"
            placeholder="请输入用户名"
          />
        </el-form-item>
        
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="userForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="userForm.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="员工编号" prop="employee_id">
          <el-input v-model="userForm.employee_id" placeholder="请输入员工编号" />
        </el-form-item>
        
        <el-form-item label="部门" prop="department">
          <el-input v-model="userForm.department" placeholder="请输入部门" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="userForm.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="权限设置">
          <el-checkbox v-model="userForm.is_admin">管理员</el-checkbox>
          <el-checkbox v-model="userForm.is_superuser">超级管理员</el-checkbox>
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
import type { AuthUserData, CreateUserRequest, UpdateUserRequest } from '@/api/auth'

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const userList = ref<AuthUserData[]>([])
const dialogVisible = ref(false)
const isEditing = ref(false)
const currentUserId = ref<number | null>(null)

// 表单引用
const userFormRef = ref<InstanceType<typeof ElForm>>()

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

// 用户表单
const userForm = reactive<CreateUserRequest & { id?: number }>({
  username: '',
  real_name: '',
  display_name: '',
  email: '',
  employee_id: '',
  department: '',
  password: '',
  is_admin: false,
  is_superuser: false
})

// 表单验证规则
const userRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { 
      validator: (rule: any, value: string, callback: Function) => {
        if (!value && !isEditing.value) {
          callback(new Error('请输入密码'))
        } else if (value && value.length < 6) {
          callback(new Error('密码长度不能少于6个字符'))
        } else {
          callback()
        }
      }, 
      trigger: 'blur' 
    }
  ]
}

// 方法
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadUsers = async () => {
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

    const data = await authApi.getUsers(params)
    userList.value = data
    // 注意：需要根据实际API返回结构调整总数获取
    // pagination.total = data.total
  } catch (error) {
    ElMessage.error('加载用户列表失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
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

const showEditDialog = (user: AuthUserData) => {
  isEditing.value = true
  currentUserId.value = user.id
  dialogVisible.value = true
  
  // 填充表单数据
  Object.assign(userForm, {
    username: user.username,
    real_name: user.real_name,
    display_name: user.display_name,
    email: user.email,
    employee_id: user.employee_id,
    department: user.department,
    password: '',
    is_admin: user.is_admin,
    is_superuser: user.is_superuser
  })
}

const resetForm = () => {
  Object.assign(userForm, {
    username: '',
    real_name: '',
    display_name: '',
    email: '',
    employee_id: '',
    department: '',
    password: '',
    is_admin: false,
    is_superuser: false
  })
  userFormRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    
    submitLoading.value = true
    
    if (isEditing.value && currentUserId.value) {
      // 编辑用户
      const updateData: UpdateUserRequest = {
        real_name: userForm.real_name,
        display_name: userForm.display_name,
        email: userForm.email,
        employee_id: userForm.employee_id,
        department: userForm.department,
        is_admin: userForm.is_admin,
        is_superuser: userForm.is_superuser
      }
      
      if (userForm.password) {
        updateData.password = userForm.password
      }
      
      await authApi.updateUser(currentUserId.value, updateData)
      ElMessage.success('用户更新成功')
    } else {
      // 创建用户
      await authApi.createUser(userForm)
      ElMessage.success('用户创建成功')
    }
    
    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    console.error('提交用户数据失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const toggleUserStatus = async (user: AuthUserData) => {
  try {
    await ElMessageBox.confirm(
      `确定要${user.is_active ? '禁用' : '启用'}用户 ${user.username} 吗？`,
      '确认操作',
      { type: 'warning' }
    )
    
    await authApi.updateUser(user.id, { is_active: !user.is_active })
    ElMessage.success(`用户${user.is_active ? '禁用' : '启用'}成功`)
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换用户状态失败:', error)
    }
  }
}

const deleteUser = async (user: AuthUserData) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${user.username} 吗？此操作不可恢复！`,
      '确认删除',
      { type: 'error' }
    )
    
    await authApi.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
    }
  }
}

// 生命周期
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management {
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
</style>