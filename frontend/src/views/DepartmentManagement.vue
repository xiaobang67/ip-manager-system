<template>
  <AppLayout>
    <div class="department-management">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-left">
          <h1>组织管理</h1>
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

      <!-- 搜索 -->
      <el-card class="filter-card">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-input
              v-model="searchQuery"
              placeholder="搜索部门名称或编码"
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
            />
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
          class="responsive-table"
        >
          <el-table-column prop="id" label="ID" sortable align="center" />
          <el-table-column prop="name" label="部门名称" sortable align="center" />
          <el-table-column prop="code" label="部门编码" align="center" />
          <el-table-column prop="created_at" label="创建时间" sortable align="center">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  size="small"
                  type="primary"
                  @click="editDepartment(row)"
                  v-if="canManageDepartments"
                >
                  编辑
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  plain
                  @click="confirmDeleteDepartment(row)"
                  v-if="canManageDepartments"
                >
                  删除
                </el-button>
              </div>
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
  createDepartment,
  updateDepartment,
  deleteDepartment
} from '@/api/departments'

const store = useStore()

// 响应式数据
const loading = ref(false)
const departments = ref([])
const statistics = ref(null)

// 搜索
const searchQuery = ref('')

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
  code: ''
})

// 编辑部门表单
const editForm = reactive({
  name: '',
  code: ''
})

// 计算属性
const userRole = computed(() => store.getters['auth/userRole'])
const canManageDepartments = computed(() => {
  const role = userRole.value?.toLowerCase()
  return ['admin', 'manager'].includes(role)
})

// 表单验证规则
const createRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 1, max: 100, message: '部门名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  code: [
    { max: 50, message: '部门编码长度不能超过 50 个字符', trigger: 'blur' }
  ]
}

const editRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 1, max: 100, message: '部门名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  code: [
    { max: 50, message: '部门编码长度不能超过 50 个字符', trigger: 'blur' }
  ]
}

// 方法
const loadDepartments = async () => {
  try {
    loading.value = true
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchQuery.value || undefined
    }


    const response = await getDepartments(params)

    
    if (response && response.departments) {
      departments.value = response.departments
      totalDepartments.value = response.total || 0
    } else if (Array.isArray(response)) {
      // 处理直接返回数组的情况
      departments.value = response
      totalDepartments.value = response.length
    } else {
      departments.value = []
      totalDepartments.value = 0
    }


  } catch (error) {
    console.error('加载部门列表失败:', error)
    departments.value = []
    totalDepartments.value = 0
    
    // 更详细的错误信息
    let errorMessage = '加载部门列表失败'
    if (error.response) {
      if (error.response.status === 404) {
        errorMessage = 'API端点不存在，请检查后端服务'
      } else if (error.response.status === 401) {
        errorMessage = '认证失败，请重新登录'
      } else if (error.response.status === 403) {
        errorMessage = '权限不足，无法访问组织管理'
      } else if (error.response.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response.data?.error?.message) {
        errorMessage = error.response.data.error.message
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    loading.value = false
  }
}

// 移除统计功能

const handleSearch = () => {
  currentPage.value = 1
  loadDepartments()
}

const resetFilters = () => {
  searchQuery.value = ''
  currentPage.value = 1
  loadDepartments()
}

const handleSortChange = ({ prop, order }) => {

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
  showEditDialog.value = true
}

const handleCreateDepartment = async () => {
  try {
    const valid = await createFormRef.value.validate()
    if (!valid) return

    createLoading.value = true
    await createDepartment({
      name: createForm.name,
      code: createForm.code || undefined
    })

    ElMessage.success('部门创建成功')
    showCreateDialog.value = false
    resetCreateForm()
    loadDepartments()
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
      code: editForm.code || undefined
    })

    ElMessage.success('部门更新成功')
    showEditDialog.value = false
    loadDepartments()
  } catch (error) {
    console.error('更新部门失败:', error)
    ElMessage.error(error.response?.data?.detail || '更新部门失败')
  } finally {
    updateLoading.value = false
  }
}

// 移除状态切换功能

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
  createFormRef.value?.resetFields()
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

// 监听器
watch([searchQuery], () => {
  currentPage.value = 1
  loadDepartments()
})

// 生命周期
onMounted(async () => {
  await loadDepartments()
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

/* 表格响应式样式 */
.responsive-table {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 确保表格容器占满宽度 */
.table-card {
  width: 100%;
  overflow-x: auto;
}

.table-card .el-table {
  width: 100% !important;
  min-width: 800px;
}

/* 强制表格自适应宽度 */
.department-management :deep(.el-table) {
  width: 100% !important;
  table-layout: fixed !important;
}

.department-management :deep(.el-table__body-wrapper),
.department-management :deep(.el-table__header-wrapper),
.department-management :deep(.el-table__footer-wrapper) {
  width: 100% !important;
  overflow: visible !important;
}

.department-management :deep(.el-table__body),
.department-management :deep(.el-table__header),
.department-management :deep(.el-table__footer) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 表格列宽度分配 */
.department-management :deep(.el-table th:nth-child(1)) { /* ID */
  width: 10% !important;
}

.department-management :deep(.el-table th:nth-child(2)) { /* 部门名称 */
  width: 35% !important;
}

.department-management :deep(.el-table th:nth-child(3)) { /* 部门编码 */
  width: 25% !important;
}

.department-management :deep(.el-table th:nth-child(4)) { /* 创建时间 */
  width: 20% !important;
}

.department-management :deep(.el-table th:nth-child(5)) { /* 操作 */
  width: 120px !important;
}

/* 对应的td列也设置相同宽度 */
.department-management :deep(.el-table td:nth-child(1)) { width: 10% !important; }
.department-management :deep(.el-table td:nth-child(2)) { width: 35% !important; }
.department-management :deep(.el-table td:nth-child(3)) { width: 25% !important; }
.department-management :deep(.el-table td:nth-child(4)) { width: 20% !important; }
.department-management :deep(.el-table td:nth-child(5)) { width: 120px !important; }

/* 确保表格内容不会溢出 */
.department-management :deep(.el-table .cell) {
  word-break: break-word;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 8px 12px;
  width: auto !important;
}

/* 部门名称列允许换行 */
.department-management :deep(.el-table td:nth-child(2) .cell) {
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
}

/* 强制所有表格内容居中对齐 */
.department-management :deep(.el-table .el-table__body td),
.department-management :deep(.el-table .el-table__header th) {
  text-align: center !important;
}

.department-management :deep(.el-table .el-table__body td .cell),
.department-management :deep(.el-table .el-table__header th .cell) {
  text-align: center !important;
  justify-content: center !important;
  display: flex !important;
  align-items: center !important;
}

.department-management :deep(.el-table .cell) {
  text-align: center !important;
  justify-content: center !important;
  display: flex !important;
  align-items: center !important;
}

/* 额外的强制居中样式 - 覆盖所有可能的冲突 */
.department-management :deep(.el-table td),
.department-management :deep(.el-table th) {
  text-align: center !important;
}

.department-management :deep(.el-table td > *),
.department-management :deep(.el-table th > *) {
  text-align: center !important;
  justify-content: center !important;
}

.department-management :deep(.el-table .el-tag) {
  margin: 0 auto !important;
}

.department-management :deep(.el-table .action-buttons) {
  justify-content: center !important;
  display: flex !important;
}



/* 排序图标居中对齐 */
.department-management :deep(.el-table .caret-wrapper) {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  margin-left: 4px !important;
}

.department-management :deep(.el-table .sort-caret) {
  margin: 0 !important;
}

.department-management :deep(.el-table th .cell) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 4px !important;
}

/* 操作按钮响应式 */
.action-buttons {
  display: flex;
  gap: 4px;
  flex-wrap: nowrap;
  justify-content: center;
  white-space: nowrap;
}

.action-buttons .el-button {
  margin: 0;
  min-width: 50px;
  flex-shrink: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .department-management {
    padding: 20px;
  }
  
  .action-buttons {
    gap: 2px;
  }
  
  .action-buttons .el-button {
    font-size: 12px;
    padding: 5px 8px;
    min-width: 50px;
  }
}

@media (max-width: 768px) {
  .department-management {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .stats-cards .el-col {
    margin-bottom: 15px;
  }
  
  .filter-card .el-row .el-col {
    margin-bottom: 10px;
  }
  
  .table-card {
    overflow-x: auto;
  }
  
  .responsive-table {
    min-width: 600px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
    align-items: stretch;
  }
  
  .action-buttons .el-button {
    width: 100%;
    margin: 1px 0;
  }
}

@media (max-width: 480px) {
  .department-management {
    padding: 12px;
  }
  
  .page-header h1 {
    font-size: 18px;
  }
  
  .responsive-table {
    min-width: 500px;
  }
  
  .pagination-wrapper {
    padding: 16px;
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