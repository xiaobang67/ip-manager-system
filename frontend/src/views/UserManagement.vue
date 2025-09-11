<template>
  <AppLayout>
    <div class="user-management">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>用户管理</h1>
        <p class="page-description">管理系统用户账号和权限</p>

      </div>
      <div class="header-right">
        <el-button 
          type="primary" 
          :icon="Plus" 
          @click="showCreateDialog = true"
          v-if="canManageUsers"
        >
          新建用户
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards" v-if="statistics">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.total_users }}</div>
              <div class="stat-label">总用户数</div>
            </div>
            <el-icon class="stat-icon"><User /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.active_users }}</div>
              <div class="stat-label">活跃用户</div>
            </div>
            <el-icon class="stat-icon active"><UserFilled /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.role_distribution?.admin || 0 }}</div>
              <div class="stat-label">管理员</div>
            </div>
            <el-icon class="stat-icon admin"><Star /></el-icon>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.inactive_users }}</div>
              <div class="stat-label">停用用户</div>
            </div>
            <el-icon class="stat-icon inactive"><Lock /></el-icon>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和过滤 -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名或邮箱"
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="roleFilter"
            placeholder="选择角色"
            clearable
            @change="loadUsers"
          >
            <el-option
              v-for="role in availableRoles"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="statusFilter"
            placeholder="选择状态"
            clearable
            @change="loadUsers"
          >
            <el-option label="全部用户" value="" />
            <el-option label="活跃用户" value="active" />
            <el-option label="停用用户" value="inactive" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button @click="resetFilters" :icon="Refresh">重置</el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 用户列表 -->
    <el-card class="table-card">
      <el-table
        :data="filteredUsers"
        v-loading="loading"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="username" label="用户名" min-width="120" sortable />
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getRoleTagType(row.role)"
              size="small"
            >
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="theme" label="主题" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.theme === 'dark' ? 'info' : 'success'"
              size="small"
            >
              {{ row.theme === 'dark' ? '暗黑' : '明亮' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="row.is_active ? 'success' : 'danger'"
              size="small"
            >
              {{ row.is_active ? '活跃' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              size="small"
              type="primary"
              @click="editUser(row)"
              v-if="canManageUsers"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'primary'"
              @click="handleToggleUserStatus(row)"
              v-if="canManageUsers && row.id !== currentUserId"
            >
              {{ row.is_active ? '停用' : '启用' }}
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="confirmDeleteUser(row)"
              v-if="canManageUsers && row.id !== currentUserId"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalUsers"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建用户对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建新用户"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="createForm.username"
            placeholder="请输入用户名"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            maxlength="128"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="createForm.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            show-password
            maxlength="128"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="createForm.email"
            placeholder="请输入邮箱地址"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in availableRoles"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="handleCreateUser" :loading="createLoading">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑用户"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="editForm.username"
            placeholder="请输入用户名"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input
            v-model="editForm.email"
            placeholder="请输入邮箱地址"
            maxlength="100"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="editForm.role" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="role in availableRoles"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="主题" prop="theme">
          <el-select v-model="editForm.theme" placeholder="请选择主题" style="width: 100%">
            <el-option
              v-for="theme in availableThemes"
              :key="theme.value"
              :label="theme.label"
              :value="theme.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch
            v-model="editForm.is_active"
            active-text="启用"
            inactive-text="停用"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="warning" @click="showResetPasswordDialog = true">
            重置密码
          </el-button>
          <el-button type="primary" @click="handleUpdateUser" :loading="updateLoading">
            更新
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog
      v-model="showResetPasswordDialog"
      title="重置密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="resetPasswordFormRef"
        :model="resetPasswordForm"
        :rules="resetPasswordRules"
        label-width="80px"
      >
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="resetPasswordForm.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
            maxlength="128"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="resetPasswordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
            maxlength="128"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showResetPasswordDialog = false">取消</el-button>
          <el-button type="primary" @click="handleResetPassword" :loading="resetPasswordLoading">
            重置
          </el-button>
        </span>
      </template>
    </el-dialog>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  User,
  UserFilled,
  Star,
  Lock
} from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import {
  getUsers,
  getUserStatistics,
  createUser,
  updateUser,
  deleteUser,
  resetUserPassword,
  toggleUserStatus,
  getAvailableRoles,
  getAvailableThemes
} from '@/api/users'

const store = useStore()

// 响应式数据
const loading = ref(false)
const users = ref([])
const statistics = ref(null)
const availableRoles = ref([])
const availableThemes = ref([])

// 搜索和过滤
const searchQuery = ref('')
const roleFilter = ref('')
const statusFilter = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalUsers = ref(0)

// 对话框状态
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showResetPasswordDialog = ref(false)

// 加载状态
const createLoading = ref(false)
const updateLoading = ref(false)
const resetPasswordLoading = ref(false)

// 表单引用
const createFormRef = ref()
const editFormRef = ref()
const resetPasswordFormRef = ref()

// 当前编辑的用户
const currentEditUser = ref(null)

// 创建用户表单
const createForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  role: 'user'
})

// 编辑用户表单
const editForm = reactive({
  username: '',
  email: '',
  role: '',
  theme: '',
  is_active: true
})

// 重置密码表单
const resetPasswordForm = reactive({
  new_password: '',
  confirmPassword: ''
})

// 计算属性
const currentUserId = computed(() => store.getters['auth/currentUser']?.id)
const userRole = computed(() => store.getters['auth/userRole'])
const canManageUsers = computed(() => {
  const role = userRole.value?.toLowerCase()
  return ['admin', 'manager'].includes(role)
})

// 过滤后的用户列表
const filteredUsers = computed(() => {
  let filtered = users.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(user => 
      user.username.toLowerCase().includes(query) ||
      (user.email && user.email.toLowerCase().includes(query))
    )
  }

  // 状态过滤
  if (statusFilter.value) {
    if (statusFilter.value === 'active') {
      filtered = filtered.filter(user => user.is_active)
    } else if (statusFilter.value === 'inactive') {
      filtered = filtered.filter(user => !user.is_active)
    }
  }

  return filtered
})

// 表单验证规则
const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于 8 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== createForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择用户角色', trigger: 'change' }
  ]
}

const editRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择用户角色', trigger: 'change' }
  ]
}

const resetPasswordRules = {
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于 8 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== resetPasswordForm.new_password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 方法
const loadUsers = async () => {
  try {
    loading.value = true
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      active_only: false
    }

    if (roleFilter.value) {
      params.role_filter = roleFilter.value
    }

    const response = await getUsers(params)
    
    // 增加严格的数据验证和多格式支持
    if (!response) {

      users.value = []
      totalUsers.value = 0
      return
    }

    // 处理多种可能的响应格式
    let usersData = []
    let totalCount = 0

    if (response.users && Array.isArray(response.users)) {
      // 格式1: { users: [], total: number }
      usersData = response.users
      totalCount = response.total || 0
    } else if (response.data?.users && Array.isArray(response.data.users)) {
      // 格式2: { data: { users: [], total: number } }
      usersData = response.data.users
      totalCount = response.data.total || 0
    } else if (Array.isArray(response)) {
      // 格式3: 直接返回数组
      usersData = response
      totalCount = response.length
    } else if (response.data && Array.isArray(response.data)) {
      // 格式4: { data: [] }
      usersData = response.data
      totalCount = response.data.length
    } else {

      usersData = []
      totalCount = 0
    }

    users.value = usersData
    totalUsers.value = totalCount


  } catch (error) {
    console.error('加载用户列表失败:', error)
    users.value = []
    totalUsers.value = 0
    ElMessage.error('加载用户列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    if (userRole.value?.toLowerCase() === 'admin') {
      statistics.value = await getUserStatistics()
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const loadAvailableRoles = async () => {
  try {
    const response = await getAvailableRoles()
    
    // 处理多种可能的响应格式
    if (Array.isArray(response)) {
      // 格式1: 直接返回数组
      availableRoles.value = response
    } else if (response.roles && Array.isArray(response.roles)) {
      // 格式2: { roles: [] }
      availableRoles.value = response.roles
    } else if (response.data && Array.isArray(response.data)) {
      // 格式3: { data: [] }
      availableRoles.value = response.data
    } else {

      availableRoles.value = []
    }
  } catch (error) {
    console.error('加载角色列表失败:', error)
    availableRoles.value = []
  }
}

const loadAvailableThemes = async () => {
  try {
    const response = await getAvailableThemes()
    
    // 处理多种可能的响应格式
    if (Array.isArray(response)) {
      // 格式1: 直接返回数组
      availableThemes.value = response
    } else if (response.themes && Array.isArray(response.themes)) {
      // 格式2: { themes: [] }
      availableThemes.value = response.themes
    } else if (response.data && Array.isArray(response.data)) {
      // 格式3: { data: [] }
      availableThemes.value = response.data
    } else {

      availableThemes.value = []
    }
  } catch (error) {
    console.error('加载主题列表失败:', error)
    availableThemes.value = []
  }
}

const handleSearch = () => {
  // 搜索是通过计算属性实现的，这里可以添加防抖逻辑
  currentPage.value = 1
}

const resetFilters = () => {
  searchQuery.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  loadUsers()
}

const handleSortChange = ({ prop, order }) => {
  // 这里可以实现服务端排序
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadUsers()
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
  loadUsers()
}

const editUser = (user) => {
  currentEditUser.value = user
  editForm.username = user.username
  editForm.email = user.email || ''
  editForm.role = user.role
  editForm.theme = user.theme
  editForm.is_active = user.is_active
  showEditDialog.value = true
}

const handleCreateUser = async () => {
  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return

    createLoading.value = true
    await createUser({
      username: createForm.username,
      password: createForm.password,
      email: createForm.email || undefined,
      role: createForm.role
    })

    ElMessage.success('用户创建成功')
    showCreateDialog.value = false
    resetCreateForm()
    loadUsers()
    loadStatistics()
  } catch (error) {
    console.error('创建用户失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建用户失败')
  } finally {
    createLoading.value = false
  }
}

const handleUpdateUser = async () => {
  try {
    const valid = await editFormRef.value.validate()
    if (!valid) return

    updateLoading.value = true
    await updateUser(currentEditUser.value.id, {
      username: editForm.username,
      email: editForm.email || undefined,
      role: editForm.role,
      theme: editForm.theme,
      is_active: editForm.is_active
    })

    ElMessage.success('用户更新成功')
    showEditDialog.value = false
    loadUsers()
    loadStatistics()
  } catch (error) {
    console.error('更新用户失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新用户失败')
  } finally {
    updateLoading.value = false
  }
}

const handleResetPassword = async () => {
  try {
    const valid = await resetPasswordFormRef.value.validate()
    if (!valid) return

    resetPasswordLoading.value = true
    await resetUserPassword(currentEditUser.value.id, {
      new_password: resetPasswordForm.new_password
    })

    ElMessage.success('密码重置成功')
    showResetPasswordDialog.value = false
    resetPasswordForm.new_password = ''
    resetPasswordForm.confirmPassword = ''
  } catch (error) {
    console.error('重置密码失败:', error)
    ElMessage.error(error.response?.data?.detail || '重置密码失败')
  } finally {
    resetPasswordLoading.value = false
  }
}

const handleToggleUserStatus = async (user) => {
  try {
    const action = user.is_active ? '停用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户 "${user.username}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await toggleUserStatus(user.id)
    ElMessage.success(`用户${action}成功`)
    loadUsers()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换用户状态失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

const confirmDeleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await deleteUser(user.id)
    ElMessage.success('用户删除成功')
    loadUsers()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除用户失败')
    }
  }
}

const resetCreateForm = () => {
  createForm.username = ''
  createForm.password = ''
  createForm.confirmPassword = ''
  createForm.email = ''
  createForm.role = 'user'
  createFormRef.value?.resetFields()
}

const getRoleTagType = (role) => {
  const types = {
    admin: 'danger',
    manager: 'warning',
    user: 'info'
  }
  return types[role] || 'info'
}

const getRoleLabel = (role) => {
  const labels = {
    admin: '管理员',
    manager: '经理',
    user: '普通用户'
  }
  return labels[role] || role
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 监听器
watch([roleFilter, statusFilter], () => {
  currentPage.value = 1
})

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadUsers(),
    loadStatistics(),
    loadAvailableRoles(),
    loadAvailableThemes()
  ])
})

// 监听对话框关闭，重置表单
watch(showCreateDialog, (newVal) => {
  if (!newVal) {
    resetCreateForm()
  }
})

watch(showResetPasswordDialog, (newVal) => {
  if (!newVal) {
    resetPasswordForm.new_password = ''
    resetPasswordForm.confirmPassword = ''
    resetPasswordFormRef.value?.resetFields()
  }
})
</script>

<style scoped>
.user-management {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  position: relative;
  overflow: hidden;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary);
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin: 0;
}

.stat-icon {
  font-size: 32px;
  opacity: 0.3;
  color: var(--el-color-primary);
}

.stat-icon.active {
  color: var(--el-color-success);
}

.stat-icon.admin {
  color: var(--el-color-warning);
}

.stat-icon.inactive {
  color: var(--el-color-danger);
}

.filter-card {
  margin-bottom: 20px;
}

.filter-card :deep(.el-card__body) {
  padding: 20px;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.pagination-wrapper {
  padding: 20px;
  display: flex;
  justify-content: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .user-management {
    padding: 10px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 15px;
  }
  
  .stats-cards .el-col {
    margin-bottom: 15px;
  }
  
  .filter-card .el-row .el-col {
    margin-bottom: 10px;
  }
}

/* 按钮颜色统一样式 */
.btn-allocation, .btn-edit {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: white !important;
}

.btn-allocation:hover, .btn-edit:hover {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
}

.btn-reservation, .btn-sync {
  background-color: #e6a23c !important;
  border-color: #e6a23c !important;
  color: white !important;
}

.btn-reservation:hover, .btn-sync:hover {
  background-color: #ebb563 !important;
  border-color: #ebb563 !important;
}

.btn-release, .btn-delete {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: white !important;
}

.btn-release:hover, .btn-delete:hover {
  background-color: #f78989 !important;
  border-color: #f78989 !important;
}

.btn-history, .btn-view {
  background-color: #909399 !important;
  border-color: #909399 !important;
  color: white !important;
}

.btn-history:hover, .btn-view:hover {
  background-color: #a6a9ad !important;
  border-color: #a6a9ad !important;
}

/* 暗黑主题适配 */
.dark .stat-number {
  color: var(--el-color-primary-light-3);
}

.dark .stat-icon {
  opacity: 0.5;
}
</style>