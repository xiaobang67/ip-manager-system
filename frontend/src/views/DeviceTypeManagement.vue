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
          <el-button @click="refreshData">
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
            <el-button type="primary" plain @click="handleReset">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 统计信息卡片 -->
      <div class="stats-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.total }}</div>
                <div class="stats-label">设备类型总数</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.active }}</div>
                <div class="stats-label">启用状态</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card class="stats-card">
              <div class="stats-item">
                <div class="stats-value">{{ statistics.inactive }}</div>
                <div class="stats-label">禁用状态</div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="6">
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
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="设备类型名称" width="150" sortable align="center" />
          <el-table-column prop="code" label="类型代码" width="120" align="center" />
          <el-table-column prop="category" label="设备分类" width="120" align="center">
            <template #default="{ row }">
              <el-tag :type="getCategoryTagType(row.category)" size="small">
                {{ getCategoryText(row.category) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="80" align="center">
            <template #default="{ row }">
              <el-tag :type="row.status === 'active' ? 'success' : 'danger'" size="small">
                {{ row.status === 'active' ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="usage_count" label="使用数量" width="100" align="center" />
          <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip align="center">
            <template #default="{ row }">
              <span>{{ row.description || '-' }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="150" align="center">
            <template #default="{ row }">
              <span>{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right" align="center">
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
                  type="primary"
                  plain
                  size="small"
                  @click="toggleStatus(row)"
                >
                  {{ row.status === 'active' ? '禁用' : '启用' }}
                </el-button>
                <el-button
                  v-if="row.usage_count === 0"
                  type="primary"
                  plain
                  size="small"
                  @click="deleteDeviceTypeHandler(row)"
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
          <el-form-item label="状态" prop="status">
            <el-radio-group v-model="deviceTypeForm.status">
              <el-radio label="active">启用</el-radio>
              <el-radio label="inactive">禁用</el-radio>
            </el-radio-group>
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
    const isAdmin = computed(() => userRole.value === 'ADMIN')
    
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
      getCategoryText
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
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.header-section h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
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
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stats-section {
  margin-bottom: 24px;
}

.stats-card {
  text-align: center;
  transition: all 0.3s ease;
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.15);
}

.stats-item {
  padding: 8px 0;
}

.stats-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
  margin-bottom: 8px;
}

.stats-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.table-section {
  background: #ffffff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .stats-section .el-col {
    margin-bottom: 16px;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 4px;
  }
}

@media (max-width: 480px) {
  .device-type-management {
    padding: 0;
  }
  
  .header-section,
  .search-section,
  .table-section {
    margin: 0 -12px 16px -12px;
    border-radius: 0;
  }
  
  .stats-section {
    margin: 0 -12px 16px -12px;
  }
  
  .stats-section .el-col {
    padding: 0 6px;
  }
}
</style>