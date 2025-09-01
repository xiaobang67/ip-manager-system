<template>
  <div class="user-list">
    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="用户信息">
          <el-input
            v-model="searchForm.search"
            placeholder="请输入用户名、姓名或邮箱"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="所属部门">
          <el-tree-select
            v-model="searchForm.department_id"
            :data="departmentTreeData"
            :props="treeSelectProps"
            placeholder="请选择部门"
            clearable
            check-strictly
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源">
          <el-select
            v-model="searchForm.auth_source"
            placeholder="认证来源"
            clearable
            style="width: 120px"
          >
            <el-option label="LDAP" value="ldap" />
            <el-option label="本地" value="local" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 操作栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增用户
          </el-button>
          <el-button type="success" @click="handleBatchTransfer" :disabled="selectedRows.length === 0">
            <el-icon><Switch /></el-icon>
            批量转移部门
          </el-button>
          <el-button type="warning" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-button @click="loadData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card">
      <el-table
        :data="tableData"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="50" />
        
        <el-table-column prop="username" label="用户名" width="120" />

        <el-table-column prop="real_name" label="真实姓名" width="120" />

        <el-table-column prop="email" label="邮箱" width="180">
          <template #default="{ row }">
            <span v-if="row.email">{{ row.email }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.auth_source === 'ldap' ? 'primary' : 'success'" size="small">
              {{ row.auth_source === 'ldap' ? 'LDAP' : '本地' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="所属部门" width="150">
          <template #default="{ row }">
            <span v-if="row.department">{{ row.department.name }}</span>
            <span v-else class="text-muted">未分配</span>
          </template>
        </el-table-column>

        <el-table-column prop="employee_id" label="员工编号" width="120">
          <template #default="{ row }">
            <span v-if="row.employee_id">{{ row.employee_id }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="position" label="职位" width="120">
          <template #default="{ row }">
            <span v-if="row.position">{{ row.position }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="info" size="small" @click="handleViewStats(row)">
              统计
            </el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">
              编辑
            </el-button>
            <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
              <el-button size="small">
                更多<el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :command="row.is_active ? 'disable' : 'enable'">
                    {{ row.is_active ? '禁用' : '启用' }}
                  </el-dropdown-item>
                  <el-dropdown-item command="transfer">转移部门</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑用户对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="form.username" placeholder="请输入用户名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="真实姓名" prop="real_name">
              <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="电话">
              <el-input v-model="form.phone" placeholder="请输入电话号码" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="员工编号">
              <el-input v-model="form.employee_id" placeholder="请输入员工编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="职位">
              <el-input v-model="form.position" placeholder="请输入职位" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="认证来源">
          <el-radio-group v-model="form.auth_source">
            <el-radio label="ldap">LDAP</el-radio>
            <el-radio label="local">本地</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="所属部门">
          <el-tree-select
            v-model="form.department_id"
            :data="departmentTreeData"
            :props="treeSelectProps"
            placeholder="请选择所属部门"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFormSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 批量转移部门对话框 -->
    <el-dialog
      v-model="transferDialogVisible"
      title="批量转移部门"
      width="400px"
    >
      <el-form label-width="100px">
        <el-form-item label="选中用户">
          <div class="selected-users">
            <el-tag
              v-for="user in selectedRows"
              :key="user.id"
              size="small"
              style="margin: 2px"
            >
              {{ user.real_name }}
            </el-tag>
          </div>
        </el-form-item>
        <el-form-item label="目标部门" required>
          <el-tree-select
            v-model="transferDepartmentId"
            :data="departmentTreeData"
            :props="treeSelectProps"
            placeholder="请选择目标部门"
            check-strictly
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="transferDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleTransferConfirm">确认转移</el-button>
      </template>
    </el-dialog>

    <!-- 用户统计对话框 -->
    <el-dialog
      v-model="statsDialogVisible"
      title="用户统计信息"
      width="500px"
    >
      <div v-if="currentUserStats" class="stats-container">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">分配IP数</div>
              <div class="stat-value">{{ currentUserStats.allocated_ips }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">负责网段</div>
              <div class="stat-value">{{ currentUserStats.responsible_segments }}</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-item">
              <div class="stat-label">地址保留</div>
              <div class="stat-value">{{ currentUserStats.active_reservations }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Switch,
  Download,
  ArrowDown
} from '@element-plus/icons-vue'
import { userApi } from '@/api/user'
import { departmentApi } from '@/api/department'
import type { User, UserCreate } from '@/types'

// 响应式数据
const loading = ref(false)
const tableData = ref<User[]>([])
const departmentTreeData = ref<any[]>([])
const selectedRows = ref<User[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  department_id: undefined as number | undefined,
  is_active: undefined as boolean | undefined,
  auth_source: undefined as 'ldap' | 'local' | undefined
})

// 分页数据
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单对话框
const formDialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref()
const form = reactive<UserCreate>({
  username: '',
  real_name: '',
  email: '',
  phone: '',
  department_id: undefined,
  employee_id: '',
  position: '',
  is_active: true,
  auth_source: 'local' // 默认为本地用户
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度应在3-50个字符之间', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '用户名只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 2, max: 100, message: '真实姓名长度应在2-100个字符之间', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  employee_id: [
    { max: 50, message: '员工编号最长50个字符', trigger: 'blur' }
  ],
  position: [
    { max: 100, message: '职位最长100个字符', trigger: 'blur' }
  ]
}

// 转移对话框
const transferDialogVisible = ref(false)
const transferDepartmentId = ref<number>()

// 统计对话框
const statsDialogVisible = ref(false)
const currentUserStats = ref<any>()
const currentEditRow = ref<User>()

// 树选择器配置
const treeSelectProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

// 方法
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.size,
      limit: pagination.size,
      ...searchForm
    }
    
    // 如果用户没有明确指定状态，默认只显示活跃用户
    if (params.is_active === undefined) {
      params.is_active = true
    }
    
    // 清空空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })

    const data = await userApi.getList(params)
    tableData.value = data
    
    // 打印info级别日志
    console.info('用户列表数据加载完成', { params, count: data.length })
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error('用户列表数据加载失败:', error)
    
    // 打印info级别日志
    console.info('用户列表数据加载失败', { error: error.message })
  } finally {
    loading.value = false
  }
}

const loadDepartments = async () => {
  try {
    const data = await departmentApi.getTree()
    departmentTreeData.value = data
    
    // 打印info级别日志
    console.info('部门树数据加载完成', { count: data.length })
  } catch (error) {
    console.error('加载部门数据失败:', error)
    
    // 打印info级别日志
    console.info('部门树数据加载失败', { error: error.message })
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
  
  // 打印info级别日志
  console.info('执行用户搜索', { searchForm: searchForm })
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    department_id: undefined,
    is_active: undefined,
    auth_source: undefined
  })
  handleSearch()
  
  // 打印info级别日志
  console.info('重置用户搜索条件')
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  formDialogVisible.value = true
  
  // 打印info级别日志
  console.info('打开新增用户对话框')
}

const handleEdit = (row: User) => {
  isEdit.value = true
  currentEditRow.value = row
  
  // 填充表单数据
  Object.assign(form, {
    username: row.username,
    real_name: row.real_name,
    email: row.email || '',
    phone: row.phone || '',
    department_id: row.department_id,
    employee_id: row.employee_id || '',
    position: row.position || '',
    is_active: row.is_active,
    auth_source: row.auth_source || 'local'
  })
  
  formDialogVisible.value = true
  
  // 打印info级别日志
  console.info('打开编辑用户对话框', { userId: row.id, username: row.username })
}

const handleFormSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 创建表单数据副本用于处理
    const formData = {...form}
    
    // 确保非必填字段在为空时设置为undefined而不是空字符串
    Object.keys(formData).forEach(key => {
      if (formData[key] === '') {
        formData[key] = undefined
      }
    })
    
    // 打印info级别日志
    console.info('用户表单数据处理完成', { formData })
    
    if (isEdit.value && currentEditRow.value) {
      await userApi.update(currentEditRow.value.id, formData)
      ElMessage.success('用户更新成功')
      
      // 打印info级别日志
      console.info('用户更新成功', { userId: currentEditRow.value.id, username: formData.username })
    } else {
      await userApi.create(formData)
      ElMessage.success('用户创建成功')
      
      // 打印info级别日志
      console.info('用户创建成功', { username: formData.username })
    }
    
    formDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('保存用户失败:', error)
    ElMessage.error('保存用户失败')
    
    // 打印info级别日志
    console.info('保存用户失败', { error: error.message, form: formData })
  }
}

const handleViewStats = async (row: User) => {
  try {
    const stats = await userApi.getStatistics(row.id)
    currentUserStats.value = stats
    statsDialogVisible.value = true
    
    // 打印info级别日志
    console.info('用户统计信息查看', { userId: row.id, username: row.username })
  } catch (error) {
    ElMessage.error('获取统计信息失败')
    console.error('获取用户统计信息失败:', error)
    
    // 打印info级别日志
    console.info('获取用户统计信息失败', { userId: row.id, username: row.username, error: error.message })
  }
}

const handleBatchTransfer = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要转移的用户')
    return
  }
  transferDepartmentId.value = undefined
  transferDialogVisible.value = true
  
  // 打印info级别日志
  console.info('打开批量转移部门对话框', { selectedCount: selectedRows.value.length })
}

const handleTransferConfirm = async () => {
  if (!transferDepartmentId.value) {
    ElMessage.warning('请选择目标部门')
    return
  }
  
  try {
    const userIds = selectedRows.value.map(user => user.id)
    await userApi.transferToDepartment({
      user_ids: userIds,
      new_department_id: transferDepartmentId.value
    })
    
    ElMessage.success('用户转移成功')
    
    // 打印info级别日志
    console.info('用户批量转移部门成功', { userIds, departmentId: transferDepartmentId.value })
    
    transferDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('转移用户失败:', error)
    ElMessage.error('转移用户失败')
    
    // 打印info级别日志
    console.info('用户批量转移部门失败', { error: error.message })
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中...')
  
  // 打印info级别日志
  console.info('用户尝试导出数据')
}

const handleSelectionChange = (selection: User[]) => {
  selectedRows.value = selection
  
  // 打印info级别日志
  console.info('用户选择变更', { selectedCount: selection.length })
}

const handleDropdownCommand = async (command: string, row: User) => {
  // 打印info级别日志
  console.info('执行用户操作', { command: command, userId: row.id, username: row.username })
  
  switch (command) {
    case 'enable':
    case 'disable':
      await handleToggleStatus(row)
      break
    case 'transfer':
      selectedRows.value = [row]
      handleBatchTransfer()
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

const handleToggleStatus = async (row: User) => {
  try {
    const action = row.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}用户 ${row.real_name} 吗？`,
      `确认${action}`,
      { type: 'warning' }
    )
    
    await userApi.update(row.id, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    
    // 打印info级别日志
    console.info(`用户${action}成功`, { userId: row.id, username: row.username })
    
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换用户状态失败:', error)
      ElMessage.error(`${action}失败`)
      
      // 打印info级别日志
      console.info(`用户${action}失败`, { userId: row.id, username: row.username, error: error.message })
    }
  }
}

const handleDelete = async (row: User) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 ${row.real_name} 吗？此操作不可恢复！`,
      '确认删除',
      { type: 'warning' }
    )
    
    await userApi.delete(row.id)
    ElMessage.success('删除成功')
    
    // 打印info级别日志
    console.info('用户删除成功', { userId: row.id, username: row.username })
    
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      ElMessage.error('删除用户失败')
      
      // 打印info级别日志
      console.info('用户删除失败', { userId: row.id, username: row.username, error: error.message })
    }
  }
}

const resetForm = () => {
  Object.assign(form, {
    username: '',
    real_name: '',
    email: '',
    phone: '',
    department_id: undefined,
    employee_id: '',
    position: '',
    is_active: true,
    auth_source: 'local'
  })
  
  // 打印info级别日志
  console.info('重置用户表单')
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadData()
  
  // 打印info级别日志
  console.info('分页大小变更', { size: size })
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadData()
  
  // 打印info级别日志
  console.info('分页页码变更', { page: page })
}

// 生命周期
onMounted(() => {
  loadData()
  loadDepartments()
  
  // 打印info级别日志
  console.info('用户列表页面初始化完成')
})
</script>

<style scoped>
.user-list {
  padding: 0;
}

.search-card,
.toolbar-card,
.table-card {
  margin-bottom: 20px;
}

.search-form {
  margin: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-muted {
  color: #909399;
}

.selected-users {
  max-height: 100px;
  overflow-y: auto;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  background-color: #f5f7fa;
}

.stats-container {
  padding: 20px 0;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.3s;
}

.stat-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .search-form .el-form-item {
    margin-bottom: 10px;
  }
  
  .toolbar {
    flex-direction: column;
    gap: 10px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>