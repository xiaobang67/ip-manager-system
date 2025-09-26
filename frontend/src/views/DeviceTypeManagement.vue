<template>
  <AppLayout>
    <div class="device-type-management">
      <!-- 页面标题和操作栏 -->
      <div class="header-section">
        <h1>设备类型管理</h1>
        <div class="header-actions">
          <el-button type="primary" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加设备类型
          </el-button>
          <el-button type="primary" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 搜索栏 -->
      <div class="search-section">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-input
              v-model="searchQuery"
              placeholder="搜索设备类型名称或描述"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleSearch">搜索</el-button>
            <el-button @click="resetForm">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 统计信息卡片 -->
      <div class="stats-section">
        <el-row :gutter="20" class="stats-row">
          <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.total }}</div>
                <div class="stats-label">设备类型总数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.active }}</div>
                <div class="stats-label">启用状态</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.inactive }}</div>
                <div class="stats-label">禁用状态</div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.usage_count }}</div>
                <div class="stats-label">使用中设备</div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 设备类型列表表格 -->
      <div class="table-section">
        <el-table
          :data="deviceTypeList"
          v-loading="loading"
          stripe
          @selection-change="handleSelectionChange"
          class="responsive-table"
          style="width: 100%"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="name" label="设备类型名称" sortable align="center" />
          <el-table-column prop="code" label="类型代码" align="center" />
          <el-table-column prop="category" label="设备分类" align="center">
            <template #default="{ row }">
              <el-tag :type="getCategoryTagType(row.category)" size="small">
                {{ getCategoryText(row.category) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" align="center">
            <template #default="{ row }">
              <el-tag 
                :type="getStatusTagType(row.status)" 
                size="small"
                :style="getStatusStyle(row.status)"
              >
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="usage_count" label="使用数量" align="center" />
          <el-table-column prop="description" label="描述" show-overflow-tooltip align="center">
            <template #default="{ row }">
              <span>{{ row.description || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" align="center">
            <template #default="{ row }">
              <span>{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180" fixed="right" align="center">
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="primary"
                  size="small"
                  @click="editDeviceType(row)"
                >
                  编辑
                </el-button>
                <el-button
                  v-if="isAdmin"
                  type="danger"
                  plain
                  size="small"
                  :disabled="row.usage_count > 0"
                  @click="deleteDeviceTypeHandler(row)"
                  :title="row.usage_count > 0 ? `该设备类型正在被 ${row.usage_count} 个设备使用，无法删除` : '删除设备类型'"
                  :class="{ 'delete-disabled': row.usage_count > 0 }"
                >
                  删除
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-section">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[20, 50, 100]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>

      <!-- 添加/编辑设备类型对话框 -->
      <el-dialog
        v-model="showAddDialog"
        :title="editingDeviceType ? '编辑设备类型' : '添加设备类型'"
        width="600px"
        @close="resetForm"
      >
        <el-form
          ref="deviceTypeFormRef"
          :model="deviceTypeForm"
          :rules="deviceTypeRules"
          label-width="120px"
        >
          <el-form-item label="设备类型名称" prop="name">
            <el-input v-model="deviceTypeForm.name" placeholder="如：服务器、工作站等" />
          </el-form-item>
          <el-form-item label="类型代码" prop="code">
            <el-input v-model="deviceTypeForm.code" placeholder="如：server、workstation等" />
            <div class="form-tip">类型代码用于系统内部标识，建议使用英文</div>
          </el-form-item>
          <el-form-item label="设备分类" prop="category">
            <el-select v-model="deviceTypeForm.category" placeholder="选择设备分类" style="width: 100%">
              <el-option label="计算设备" value="computing" />
              <el-option label="网络设备" value="network" />
              <el-option label="存储设备" value="storage" />
              <el-option label="安全设备" value="security" />
              <el-option label="办公设备" value="office" />
              <el-option label="其他设备" value="other" />
              
            </el-select>
          </el-form-item>
          <el-form-item label="描述" prop="description">
            <el-input
              v-model="deviceTypeForm.description"
              type="textarea"
              :rows="3"
              placeholder="设备类型的详细描述"
            />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ editingDeviceType ? '更新' : '添加' }}
          </el-button>
        </template>
      </el-dialog>
    </div>
  </AppLayout>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import AppLayout from '@/components/AppLayout.vue'
import { useStore } from 'vuex'
import { getDeviceTypes, createDeviceType, updateDeviceType, deleteDeviceType, toggleDeviceTypeStatus, getDeviceTypeStatistics } from '@/api/deviceTypes'

export default {
  name: 'DeviceTypeManagement',
  components: {
    AppLayout,
    Plus,
    Refresh,
    Search
  },
  setup() {
    // Vuex store
    const store = useStore()
    
    // 用户权限相关
    const currentUser = computed(() => store.getters['auth/currentUser'])
    const userRole = computed(() => store.getters['auth/userRole'])
    const isAdmin = computed(() => userRole.value?.toLowerCase() === 'admin')
    
    // 响应式数据
    const loading = ref(false)
    const submitting = ref(false)
    
    const deviceTypeList = ref([])
    const selectedDeviceTypes = ref([])
    
    const searchQuery = ref('')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    
    const statistics = ref({
      total: 0,
      active: 0,
      inactive: 0,
      usage_count: 0
    })
    
    // 对话框显示状态
    const showAddDialog = ref(false)
    const editingDeviceType = ref(null)
    
    // 表单数据
    const deviceTypeForm = reactive({
      name: '',
      code: '',
      category: '',
      status: 'active',
      description: ''
    })
    
    // 表单验证规则
    const deviceTypeRules = {
      name: [
        { required: true, message: '请输入设备类型名称', trigger: 'blur' },
        { min: 2, max: 50, message: '名称长度在 2 到 50 个字符', trigger: 'blur' }
      ],
      code: [
        { required: true, message: '请输入类型代码', trigger: 'blur' },
        { pattern: /^[a-zA-Z][a-zA-Z0-9_-]*$/, message: '代码必须以字母开头，只能包含字母、数字、下划线和连字符', trigger: 'blur' }
      ],
      category: [
        { required: true, message: '请选择设备分类', trigger: 'change' }
      ],
      status: [
        { required: true, message: '请选择状态', trigger: 'change' }
      ]
    }
    

    
    // 方法
    const loadDeviceTypes = async () => {
      loading.value = true
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        
        if (searchQuery.value) {
          params.search = searchQuery.value
        }
        
        const response = await getDeviceTypes(params)
        
        if (response && response.data) {
          deviceTypeList.value = response.data
          total.value = response.total || response.data.length
        } else {
          deviceTypeList.value = []
          total.value = 0
        }
        
        // 加载统计信息
        await loadStatistics()
      } catch (error) {
        console.error('加载设备类型列表失败：', error)
        ElMessage.error('加载设备类型列表失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    const loadStatistics = async () => {
      try {
        const response = await getDeviceTypeStatistics()
        
        if (response && response.data) {
          statistics.value = response.data
        } else if (response) {
          statistics.value = response
        }
      } catch (error) {
        console.error('加载统计信息失败：', error)
        // 如果统计信息加载失败，不显示错误消息，只在控制台记录
      }
    }
    
    const refreshData = () => {
      loadDeviceTypes()
    }
    
    const handleSearch = () => {
      currentPage.value = 1
      loadDeviceTypes()
    }
    
    const handleReset = () => {
      searchQuery.value = ''
      currentPage.value = 1
      loadDeviceTypes()
    }
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      loadDeviceTypes()
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadDeviceTypes()
    }
    
    const handleSelectionChange = (selection) => {
      selectedDeviceTypes.value = selection
    }
    
    // 设备类型操作方法
    const editDeviceType = (row) => {
      editingDeviceType.value = row
      Object.assign(deviceTypeForm, {
        name: row.name,
        code: row.code,
        category: row.category,
        status: row.status,
        description: row.description
      })
      showAddDialog.value = true
    }
    
    const toggleStatus = async (row) => {
      try {
        const newStatus = row.status === 'active' ? 'inactive' : 'active'
        const action = newStatus === 'active' ? '启用' : '禁用'
        
        await ElMessageBox.confirm(
          `确定要${action}设备类型"${row.name}"吗？`,
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        // 调用API切换状态
        await toggleDeviceTypeStatus(row.id, { status: newStatus })
        
        ElMessage.success(`${action}成功`)
        refreshData()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败：' + error.message)
        }
      }
    }
    
    const deleteDeviceTypeHandler = async (row) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除设备类型"${row.name}"吗？此操作不可恢复！`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        // 调用API删除设备类型
        await deleteDeviceType(row.id)
        
        ElMessage.success('删除成功')
        refreshData()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败：' + error.message)
        }
      }
    }
    
    // 表单提交方法
    const submitForm = async () => {
      submitting.value = true
      try {
        if (editingDeviceType.value) {
          // 更新现有设备类型
          await updateDeviceType(editingDeviceType.value.id, deviceTypeForm)
          ElMessage.success('设备类型更新成功')
        } else {
          // 添加新设备类型
          await createDeviceType(deviceTypeForm)
          ElMessage.success('设备类型添加成功')
        }
        
        showAddDialog.value = false
        refreshData()
      } catch (error) {
        ElMessage.error('操作失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    // 表单重置方法
    const resetForm = () => {
      Object.assign(deviceTypeForm, {
        name: '',
        code: '',
        category: '',
        status: 'active',
        description: ''
      })
      editingDeviceType.value = null
    }
    
    // 工具方法
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN')
    }
    
    const getCategoryTagType = (category) => {
      const typeMap = {
        computing: 'primary',
        network: 'success',
        storage: 'warning',
        security: 'danger',
        office: 'info',
        other: ''
      }
      return typeMap[category] || ''
    }
    
    const getCategoryText = (category) => {
      const textMap = {
        computing: '计算设备',
        network: '网络设备',
        storage: '存储设备',
        security: '安全设备',
        office: '办公设备',
        other: '其他设备'
      }
      return textMap[category] || category
    }
    
    // 状态相关工具方法
    const getStatusTagType = (status) => {
      const typeMap = {
        active: 'success',
        inactive: 'danger'
      }
      return typeMap[status] || 'info'
    }
    
    const getStatusStyle = (status) => {
      const styleMap = {
        active: {
          backgroundColor: '#f0f9ff',
          borderColor: '#67c23a',
          color: '#67c23a'
        },
        inactive: {
          backgroundColor: '#fef0f0',
          borderColor: '#f56c6c',
          color: '#f56c6c'
        }
      }
      return styleMap[status] || {
        backgroundColor: '#f4f4f5',
        borderColor: '#909399',
        color: '#909399'
      }
    }
    
    const getStatusText = (status) => {
      const textMap = {
        active: '启用',
        inactive: '禁用'
      }
      return textMap[status] || status
    }
    
    // 组件挂载时加载数据
    onMounted(() => {
      loadDeviceTypes()
    })
    
    return {
      // 响应式数据
      loading,
      submitting,
      deviceTypeList,
      selectedDeviceTypes,
      searchQuery,
      currentPage,
      pageSize,
      total,
      statistics,
      showAddDialog,
      editingDeviceType,
      deviceTypeForm,
      deviceTypeRules,
      
      // 计算属性
      currentUser,
      userRole,
      isAdmin,
      
      // 方法
      loadDeviceTypes,
      refreshData,
      handleSearch,
      handleReset,
      handleSizeChange,
      handleCurrentChange,
      handleSelectionChange,
      editDeviceType,
      toggleStatus,
      deleteDeviceTypeHandler,
      submitForm,
      resetForm,
      formatDate,
      getCategoryTagType,
      getCategoryText,
      getStatusTagType,
      getStatusStyle,
      getStatusText
    }
  }
}
</script>

<style scoped>
.device-type-management {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04);
}

.header-section h1 {
  margin: 0;
  color: #303133;
  font-size: 28px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04);
  font-size: 15px;
}

.stats-section {
  margin-bottom: 24px;
}

.stats-card {
  text-align: center;
  transition: all 0.3s ease;
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04);
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.stats-item {
  padding: 8px 0;
}

.stats-value {
  font-size: 36px;
  font-weight: 700;
  color: #409eff !important;
  margin-bottom: 8px;
}

.stats-label {
  font-size: 16px;
  color: #909399;
  font-weight: 500;
}

.table-section {
  background: #ffffff;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04);
  font-size: 15px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  align-items: center;
  min-height: 32px;
}

.action-buttons .el-button {
  margin: 0;
  min-width: 60px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  font-size: 15px;
}

.form-tip {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

/* 自定义按钮颜色 - 强制优先级 */
:deep(.el-button--primary) {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
}

:deep(.el-button--primary:hover) {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
  color: #ffffff !important;
}

:deep(.el-button--primary:active) {
  background-color: #337ecc !important;
  border-color: #337ecc !important;
  color: #ffffff !important;
}

:deep(.el-button--primary.is-plain) {
  background-color: #ffffff !important;
  border-color: #409eff !important;
  color: #409eff !important;
}

:deep(.el-button--primary.is-plain:hover) {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
}

:deep(.el-button--primary.is-plain:active) {
  background-color: #337ecc !important;
  border-color: #337ecc !important;
  color: #ffffff !important;
}

/* 确保状态标签颜色正确显示 */
.device-type-management .el-tag.el-tag--success,
.device-type-management .status-active {
  background-color: #f0f9ff !important;
  border-color: #67c23a !important;
  color: #67c23a !important;
}

.device-type-management .el-tag.el-tag--danger,
.device-type-management .status-inactive {
  background-color: #fef0f0 !important;
  border-color: #f56c6c !important;
  color: #f56c6c !important;
}

.device-type-management .el-tag.el-tag--info {
  background-color: #f4f4f5 !important;
  border-color: #909399 !important;
  color: #909399 !important;
}

/* 额外的按钮样式强制覆盖 */
.device-type-management :deep(.el-button) {
  font-size: 15px !important;
}

.device-type-management :deep(.el-button--primary) {
  background: #409eff !important;
  border: 1px solid #409eff !important;
}

.device-type-management :deep(.el-button--primary:hover) {
  background: #66b1ff !important;
  border: 1px solid #66b1ff !important;
}

/* 删除按钮颜色优化 */
.device-type-management :deep(.el-button--danger) {
  background: #f56c6c !important;
  border: 1px solid #f56c6c !important;
  color: #ffffff !important;
}

.device-type-management :deep(.el-button--danger:hover) {
  background: #f78989 !important;
  border: 1px solid #f78989 !important;
  color: #ffffff !important;
}

/* 禁用状态的删除按钮 - 浅色显示 */
.device-type-management :deep(.el-button--danger.delete-disabled) {
  background: #fbc4c4 !important;
  border: 1px solid #fbc4c4 !important;
  color: #c0c4cc !important;
  cursor: not-allowed !important;
}

.device-type-management :deep(.el-button--danger.delete-disabled:hover) {
  background: #fbc4c4 !important;
  border: 1px solid #fbc4c4 !important;
  color: #c0c4ant;
}

/* 表格响应式样式 */
.responsive-table {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 确保表格容器占满宽度 */
.table-section {
  width: 100%;
  overflow-x: auto;
}

.table-section .el-table {
  width: 100% !important;
  min-width: 1000px;
}

/* 强制表格自适应宽度 */
.device-type-management :deep(.el-table) {
  width: 100% !important;
  table-layout: fixed !important;
}

.device-type-management :deep(.el-table__body-wrapper),
.device-type-management :deep(.el-table__header-wrapper),
.device-type-management :deep(.el-table__footer-wrapper) {
  width: 100% !important;
  overflow: visible !important;
}

.device-type-management :deep(.el-table__body),
.device-type-management :deep(.el-table__header),
.device-type-management :deep(.el-table__footer) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 表格列宽度分配 */
.device-type-management :deep(.el-table th:nth-child(1)) { /* 选择列 */
  width: 50px !important;
}

.device-type-management :deep(.el-table th:nth-child(2)) { /* 设备类型名称 */
  width: 15% !important;
}

.device-type-management :deep(.el-table th:nth-child(3)) { /* 类型代码 */
  width: 12% !important;
}

.device-type-management :deep(.el-table th:nth-child(4)) { /* 设备分类 */
  width: 12% !important;
}

.device-type-management :deep(.el-table th:nth-child(5)) { /* 状态 */
  width: 8% !important;
}

.device-type-management :deep(.el-table th:nth-child(6)) { /* 使用数量 */
  width: 8% !important;
}

.device-type-management :deep(.el-table th:nth-child(7)) { /* 描述 */
  width: 25% !important;
}

.device-type-management :deep(.el-table th:nth-child(8)) { /* 创建时间 */
  width: 15% !important;
}

.device-type-management :deep(.el-table th:nth-child(9)) { /* 操作 */
  width: 140px !important;
}

/* 对应的td列也设置相同宽度 */
.device-type-management :deep(.el-table td:nth-child(1)) { width: 50px !important; }
.device-type-management :deep(.el-table td:nth-child(2)) { width: 15% !important; }
.device-type-management :deep(.el-table td:nth-child(3)) { width: 12% !important; }
.device-type-management :deep(.el-table td:nth-child(4)) { width: 12% !important; }
.device-type-management :deep(.el-table td:nth-child(5)) { width: 8% !important; }
.device-type-management :deep(.el-table td:nth-child(6)) { width: 8% !important; }
.device-type-management :deep(.el-table td:nth-child(7)) { width: 25% !important; }
.device-type-management :deep(.el-table td:nth-child(8)) { width: 15% !important; }
.device-type-management :deep(.el-table td:nth-child(9)) { width: 140px !important; }

/* 确保表格内容不会溢出 */
.device-type-management :deep(.el-table .cell) {
  word-break: break-word;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 8px 12px;
}

/* 描述列允许换行 */
.device-type-management :deep(.el-table td:nth-child(7) .cell) {
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
}

/* 强制所有表格内容居中对齐 - 使用最高优先级 */
.device-type-management :deep(.el-table .el-table__body td),
.device-type-management :deep(.el-table .el-table__header th) {
  text-align: center !important;
}

.device-type-management :deep(.el-table .el-table__body td .cell),
.device-type-management :deep(.el-table .el-table__header th .cell) {
  text-align: center !important;
  justify-content: center !important;
  display: flex !important;
  align-items: center !important;
}

.device-type-management :deep(.el-table .cell) {
  text-align: center !important;
  justify-content: center !important;
  display: flex !important;
  align-items: center !important;
}

/* 特别针对文本内容的居中样式 */
.device-type-management :deep(.el-table .cell span) {
  text-align: center !important;
  display: block !important;
}

/* 额外的强制居中样式 - 覆盖所有可能的冲突 */
.device-type-management :deep(.el-table td),
.device-type-management :deep(.el-table th) {
  text-align: center !important;
}

.device-type-management :deep(.el-table td > *),
.device-type-management :deep(.el-table th > *) {
  text-align: center !important;
  justify-content: center !important;
}

.device-type-management :deep(.el-table .el-tag) {
  margin: 0 auto !important;
}

.device-type-management :deep(.el-table .action-buttons) {
  justify-content: center !important;
  display: flex !important;
}

/* 修复cell内容居中问题 */
.device-type-management :deep(.el-table .cell) {
  width: auto !important;
}

/* 排序图标居中对齐 */
.device-type-management :deep(.el-table .caret-wrapper) {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  margin-left: 4px !important;
}

.device-type-management :deep(.el-table .sort-caret) {
  margin: 0 !important;
}

.device-type-management :deep(.el-table th .cell) {
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
  .device-type-management {
    padding: 20px;
  }
  
  .stats-section .el-col {
    margin-bottom: 12px;
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
  .device-type-management {
    padding: 16px;
  }
  
  .header-section {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
    padding: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  
  .stats-section .el-col {
    margin-bottom: 16px;
  }
  
  .table-section {
    padding: 16px;
    overflow-x: auto;
  }
  
  .responsive-table {
    min-width: 800px;
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
  .device-type-management {
    padding: 12px;
  }
  
  .header-section {
    padding: 12px;
  }
  
  .header-section h1 {
    font-size: 18px;
  }
  
  .stats-value {
    font-size: 20px;
  }
  
  .table-section {
    padding: 8px;
  }
  
  .responsive-table {
    min-width: 600px;
  }
  
  .pagination-section {
    margin-top: 16px;
  }
  
  .pagination-section .el-pagination {
    justify-content: center;
  }
}
</style>