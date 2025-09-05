<template>
  <AppLayout>
    <div class="department-management">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1>部门管理</h1>
          <p class="page-description">管理系统部门信息和组织架构</p>
        </div>
        <div class="header-right">
          <el-button 
            type="primary" 
            :icon="Plus" 
            @click="showCreateDialog = true"
            v-if="canManageDepartments"
          >
            新建部门
          </el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-cards" v-if="statistics">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.total_departments }}</div>
                <div class="stat-label">总部门数</div>
              </div>
              <el-icon class="stat-icon"><OfficeBuilding /></el-icon>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.active_departments }}</div>
                <div class="stat-label">活跃部门</div>
              </div>
              <el-icon class="stat-icon active"><Checked /></el-icon>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="stat-card">
              <div class="stat-content">
                <div class="stat-number">{{ statistics.inactive_departments }}</div>
                <div class="stat-label">停用部门</div>
              </div>
              <el-icon class="stat-icon inactive"><Close /></el-icon>
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
              placeholder="搜索部门名称、编码或负责人"
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
          </el-col>
          <el-col :span="6">
            <el-select
              v-model="statusFilter"
              placeholder="选择状态"
              clearable
              @change="loadDepartments"
            >
              <el-option label="全部部门" value="" />
              <el-option label="活跃部门" value="active" />
              <el-option label="停用部门" value="inactive" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button @click="resetFilters" :icon="Refresh">重置</el-button>
          </el-col>
        </el-row>
      </el-card>

      <!-- 部门列表 -->
      <el-card class="table-card">
        <el-table
          :data="departments"
          v-loading="loading"
          stripe
          style="width: 100%"
          @sort-change="handleSortChange"
        >
          <el-table-column prop="id" label="ID" width="80" sortable />
          <el-table-column prop="name" label="部门名称" min-width="150" sortable />
          <el-table-column prop="code" label="部门编码" width="120" />
          <el-table-column prop="manager" label="负责人" width="120" />
          <el-table-column prop="contact_email" label="联系邮箱" min-width="180" />
          <el-table-column prop="contact_phone" label="联系电话" width="130" />
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
                @click="editDepartment(row)"
                v-if="canManageDepartments"
              >
                编辑
              </el-button>
              <el-button
                size="small"
                :type="row.is_active ? 'warning' : 'success'"
                @click="handleToggleDepartmentStatus(row)"
                v-if="canManageDepartments"
              >
                {{ row.is_active ? '停用' : '启用' }}
              </el-button>
              <el-button
                size="small"
                type="danger"
                @click="confirmDeleteDepartment(row)"
                v-if="canManageDepartments"
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
            :total="totalDepartments"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>

      <!-- 创建部门对话框 -->
      <el-dialog
        v-model="showCreateDialog"
        title="创建新部门"
        width="600px"
        :close-on-click-modal="false"
      >
        <el-form
          ref="createFormRef"
          :model="createForm"
          :rules="createRules"
          label-width="100px"
        >
          <el-form-item label="部门名称" prop="name">
            <el-input
              v-model="createForm.name"
              placeholder="请输入部门名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="部门编码" prop="code">
            <el-input
              v-model="createForm.code"
              placeholder="请输入部门编码（可选）"
              maxlength="50"
            />
          </el-form-item>
          <el-form-item label="负责人" prop="manager">
            <el-input
              v-model="createForm.manager"
              placeholder="请输入负责人姓名"
              maxlength="100"
            />
          </el-form-item>
          <el-form-item label="联系邮箱" prop="contact_email">
            <el-input
              v-model="createForm.contact_email"
              placeholder="请输入联系邮箱"
              maxlength="100"
            />
          </el-form-item>
          <el-form-item label="联系电话" prop="contact_phone">
            <el-input
              v-model="createForm.contact_phone"
              placeholder="请输入联系电话"
              maxlength="50"
            />
          </el-form-item>
          <el-form-item label="部门描述" prop="description">
            <el-input
              v-model="createForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入部门描述"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="showCreateDialog = false">取消</el-button>
            <el-button type="primary" @click="handleCreateDepartment" :loading="createLoading">
              创建
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 编辑部门对话框 -->
      <el-dialog
        v-model="showEditDialog"
        title="编辑部门"
        width="600px"
        :close-on-click-modal="false"
      >
        <el-form
          ref="editFormRef"
          :model="editForm"
          :rules="editRules"
          label-width="100px"
        >
          <el-form-item label="部门名称" prop="name">
            <el-input
              v-model="editForm.name"
              placeholder="请输入部门名称"
              maxlength="100"
              show-word-limit
            />
          </el-form-item>
          <el-form-item label="部门编码" prop="code">
            <el-input
              v-model="editForm.code"
              placeholder="请输入部门编码（可选）"
              maxlength="50"
            />
          </el-form-item>
          <el-form-item label="负责人" prop="manager">
            <el-input
              v-model="editForm.manager"
              placeholder="请输入负责人姓名"
              maxlength="100"
            />
          </el-form-item>
          <el-form-item label="联系邮箱" prop="contact_email">
            <el-input
              v-model="editForm.contact_email"
              placeholder="请输入联系邮箱"
              maxlength="100"
            />
          </el-form-item>
          <el-form-item label="联系电话" prop="contact_phone">
            <el-input
              v-model="editForm.contact_phone"
              placeholder="请输入联系电话"
              maxlength="50"
            />
          </el-form-item>
          <el-form-item label="部门描述" prop="description">
            <el-input
              v-model="editForm.description"
              type="textarea"
              :rows="3"
              placeholder="请输入部门描述"
            />
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
            <el-button type="primary" @click="handleUpdateDepartment" :loading="updateLoading">
              更新
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
  OfficeBuilding,
  Checked,
  Close
} from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import {
  getDepartments,
  getDepartmentStatistics,
  createDepartment,
  updateDepartment,
  deleteDepartment
} from '@/api/departments'

const store = useStore()

// 响应式数据
const loading = ref(false)
const departments = ref([])
const statistics = ref(null)

// 搜索和过滤
const searchQuery = ref('')
const statusFilter = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalDepartments = ref(0)

// 对话框状态
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

// 加载状态
const createLoading = ref(false)
const updateLoading = ref(false)

// 表单引用
const createFormRef = ref()
const editFormRef = ref()

// 当前编辑的部门
const currentEditDepartment = ref(null)

// 创建部门表单
const createForm = reactive({
  name: '',
  code: '',
  manager: '',
  contact_email: '',
  contact_phone: '',
  description: ''
})

// 编辑部门表单
const editForm = reactive({
  name: '',
  code: '',
  manager: '',
  contact_email: '',
  contact_phone: '',
  description: '',
  is_active: true
})

// 计算属性
const userRole = computed(() => store.getters['auth/userRole'])
const canManageDepartments = computed(() => ['admin', 'manager'].includes(userRole.value))

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 1, max: 100, message: '部门名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  code: [
    { max: 50, message: '部门编码长度不能超过 50 个字符', trigger: 'blur' }
  ],
  manager: [
    { max: 100, message: '负责人姓名长度不能超过 100 个字符', trigger: 'blur' }
  ],
  contact_email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  contact_phone: [
    { max: 50, message: '联系电话长度不能超过 50 个字符', trigger: 'blur' }
  ]
}

const editRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 1, max: 100, message: '部门名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  code: [
    { max: 50, message: '部门编码长度不能超过 50 个字符', trigger: 'blur' }
  ],
  manager: [
    { max: 100, message: '负责人姓名长度不能超过 100 个字符', trigger: 'blur' }
  ],
  contact_email: [
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  contact_phone: [
    { max: 50, message: '联系电话长度不能超过 50 个字符', trigger: 'blur' }
  ]
}

// 方法
const loadDepartments = async () => {
  try {
    loading.value = true
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      active_only: statusFilter.value === 'active',
      search: searchQuery.value || undefined
    }

    if (statusFilter.value === 'inactive') {
      params.active_only = false
    }

    const response = await getDepartments(params)
    
    if (response && response.departments) {
      departments.value = response.departments
      totalDepartments.value = response.total || 0
    } else {
      departments.value = []
      totalDepartments.value = 0
    }

    console.log('获取到部门数据:', { count: departments.value.length, total: totalDepartments.value })
  } catch (error) {
    console.error('加载部门列表失败:', error)
    departments.value = []
    totalDepartments.value = 0
    ElMessage.error('加载部门列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  try {
    if (['admin', 'manager'].includes(userRole.value)) {
      statistics.value = await getDepartmentStatistics()
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadDepartments()
}

const resetFilters = () => {
  searchQuery.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  loadDepartments()
}

const handleSortChange = ({ prop, order }) => {
  console.log('排序变化:', prop, order)
}

const handleSizeChange = (newSize) => {
  pageSize.value = newSize
  currentPage.value = 1
  loadDepartments()
}

const handleCurrentChange = (newPage) => {
  currentPage.value = newPage
  loadDepartments()
}

const editDepartment = (department) => {
  currentEditDepartment.value = department
  editForm.name = department.name
  editForm.code = department.code || ''
  editForm.manager = department.manager || ''
  editForm.contact_email = department.contact_email || ''
  editForm.contact_phone = department.contact_phone || ''
  editForm.description = department.description || ''
  editForm.is_active = department.is_active
  showEditDialog.value = true
}

const handleCreateDepartment = async () => {
  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return

    createLoading.value = true
    await createDepartment({
      name: createForm.name,
      code: createForm.code || undefined,
      manager: createForm.manager || undefined,
      contact_email: createForm.contact_email || undefined,
      contact_phone: createForm.contact_phone || undefined,
      description: createForm.description || undefined
    })

    ElMessage.success('部门创建成功')
    showCreateDialog.value = false
    resetCreateForm()
    loadDepartments()
    loadStatistics()
  } catch (error) {
    console.error('创建部门失败:', error)
    ElMessage.error(error.response?.data?.detail || '创建部门失败')
  } finally {
    createLoading.value = false
  }
}

const handleUpdateDepartment = async () => {
  try {
    const valid = await editFormRef.value.validate()
    if (!valid) return

    updateLoading.value = true
    await updateDepartment(currentEditDepartment.value.id, {
      name: editForm.name,
      code: editForm.code || undefined,
      manager: editForm.manager || undefined,
      contact_email: editForm.contact_email || undefined,
      contact_phone: editForm.contact_phone || undefined,
      description: editForm.description || undefined,
      is_active: editForm.is_active
    })

    ElMessage.success('部门更新成功')
    showEditDialog.value = false
    loadDepartments()
    loadStatistics()
  } catch (error) {
    console.error('更新部门失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新部门失败')
  } finally {
    updateLoading.value = false
  }
}

const handleToggleDepartmentStatus = async (department) => {
  try {
    const action = department.is_active ? '停用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}部门 "${department.name}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await updateDepartment(department.id, {
      is_active: !department.is_active
    })
    
    ElMessage.success(`部门${action}成功`)
    loadDepartments()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换部门状态失败:', error)
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

const confirmDeleteDepartment = async (department) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部门 "${department.name}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'error'
      }
    )

    await deleteDepartment(department.id)
    ElMessage.success('部门删除成功')
    loadDepartments()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除部门失败:', error)
      ElMessage.error(error.response?.data?.detail || '删除部门失败')
    }
  }
}

const resetCreateForm = () => {
  createForm.name = ''
  createForm.code = ''
  createForm.manager = ''
  createForm.contact_email = ''
  createForm.contact_phone = ''
  createForm.description = ''
  createFormRef.value?.resetFields()
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 监听器
watch([statusFilter], () => {
  currentPage.value = 1
  loadDepartments()
})

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadDepartments(),
    loadStatistics()
  ])
})

// 监听对话框关闭，重置表单
watch(showCreateDialog, (newVal) => {
  if (!newVal) {
    resetCreateForm()
  }
})

watch(showEditDialog, (newVal) => {
  if (!newVal) {
    editFormRef.value?.resetFields()
  }
})
</script>

<style scoped>
.department-management {
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
  .department-management {
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

/* 暗黑主题适配 */
.dark .stat-number {
  color: var(--el-color-primary-light-3);
}

.dark .stat-icon {
  opacity: 0.5;
}
</style>