<template>
  <div class="ip-management">
    <!-- 页面标题和操作栏 -->
    <div class="header-section">
      <h1>IP地址管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showAllocationDialog = true">
          <el-icon><Plus /></el-icon>
          分配IP地址
        </el-button>
        <el-button type="warning" @click="showBulkDialog = true">
          <el-icon><Operation /></el-icon>
          批量操作
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 高级搜索组件 -->
    <AdvancedSearch
      @search="handleAdvancedSearch"
      @reset="handleSearchReset"
    />

    <!-- 统计信息卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.total }}</div>
              <div class="stats-label">总IP数量</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.available }}</div>
              <div class="stats-label">可用IP</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.allocated }}</div>
              <div class="stats-label">已分配IP</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.utilization_rate }}%</div>
              <div class="stats-label">使用率</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- IP地址列表表格 -->
    <div class="table-section">
      <el-table
        :data="ipList"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="ip_address" label="IP地址" width="140" sortable />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hostname" label="主机名" width="150" />
        <el-table-column prop="mac_address" label="MAC地址" width="150" />
        <el-table-column prop="device_type" label="设备类型" width="120" />
        <el-table-column prop="assigned_to" label="分配给" width="120" />
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        <el-table-column prop="allocated_at" label="分配时间" width="160">
          <template #default="{ row }">
            {{ row.allocated_at ? formatDate(row.allocated_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'available'"
              type="primary"
              size="small"
              @click="allocateIP(row)"
            >
              分配
            </el-button>
            <el-button
              v-if="row.status === 'available'"
              type="warning"
              size="small"
              @click="reserveIP(row)"
            >
              保留
            </el-button>
            <el-button
              v-if="row.status === 'allocated' || row.status === 'reserved'"
              type="danger"
              size="small"
              @click="releaseIP(row)"
            >
              释放
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="viewHistory(row)"
            >
              历史
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[20, 50, 100, 200]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- IP分配对话框 -->
    <el-dialog
      v-model="showAllocationDialog"
      title="分配IP地址"
      width="600px"
      @close="resetAllocationForm"
    >
      <el-form
        ref="allocationFormRef"
        :model="allocationForm"
        :rules="allocationRules"
        label-width="100px"
      >
        <el-form-item label="网段" prop="subnet_id">
          <el-select v-model="allocationForm.subnet_id" placeholder="选择网段" style="width: 100%">
            <el-option
              v-for="subnet in subnets"
              :key="subnet.id"
              :label="subnet.network"
              :value="subnet.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="首选IP" prop="preferred_ip">
          <el-input v-model="allocationForm.preferred_ip" placeholder="留空自动分配" />
        </el-form-item>
        <el-form-item label="MAC地址" prop="mac_address">
          <el-input v-model="allocationForm.mac_address" placeholder="如：00:11:22:33:44:55" />
        </el-form-item>
        <el-form-item label="主机名" prop="hostname">
          <el-input v-model="allocationForm.hostname" placeholder="主机名" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type">
          <el-select v-model="allocationForm.device_type" placeholder="选择设备类型" style="width: 100%">
            <el-option label="服务器" value="server" />
            <el-option label="工作站" value="workstation" />
            <el-option label="网络设备" value="network" />
            <el-option label="打印机" value="printer" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="位置" prop="location">
          <el-input v-model="allocationForm.location" placeholder="设备位置" />
        </el-form-item>
        <el-form-item label="分配给" prop="assigned_to">
          <el-input v-model="allocationForm.assigned_to" placeholder="负责人或部门" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="allocationForm.description"
            type="textarea"
            :rows="3"
            placeholder="备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAllocationDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAllocation" :loading="submitting">
          确认分配
        </el-button>
      </template>
    </el-dialog>

    <!-- IP保留对话框 -->
    <el-dialog
      v-model="showReservationDialog"
      title="保留IP地址"
      width="500px"
      @close="resetReservationForm"
    >
      <el-form
        ref="reservationFormRef"
        :model="reservationForm"
        :rules="reservationRules"
        label-width="100px"
      >
        <el-form-item label="IP地址">
          <el-input v-model="reservationForm.ip_address" disabled />
        </el-form-item>
        <el-form-item label="保留原因" prop="reason">
          <el-input
            v-model="reservationForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明保留原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReservationDialog = false">取消</el-button>
        <el-button type="primary" @click="submitReservation" :loading="submitting">
          确认保留
        </el-button>
      </template>
    </el-dialog>

    <!-- IP释放对话框 -->
    <el-dialog
      v-model="showReleaseDialog"
      title="释放IP地址"
      width="500px"
      @close="resetReleaseForm"
    >
      <el-form
        ref="releaseFormRef"
        :model="releaseForm"
        :rules="releaseRules"
        label-width="100px"
      >
        <el-form-item label="IP地址">
          <el-input v-model="releaseForm.ip_address" disabled />
        </el-form-item>
        <el-form-item label="释放原因" prop="reason">
          <el-input
            v-model="releaseForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明释放原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showReleaseDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRelease" :loading="submitting">
          确认释放
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量操作对话框 -->
    <el-dialog
      v-model="showBulkDialog"
      title="批量操作"
      width="600px"
      @close="resetBulkForm"
    >
      <el-form
        ref="bulkFormRef"
        :model="bulkForm"
        :rules="bulkRules"
        label-width="100px"
      >
        <el-form-item label="操作类型" prop="operation">
          <el-radio-group v-model="bulkForm.operation">
            <el-radio label="reserve">批量保留</el-radio>
            <el-radio label="release">批量释放</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选中IP">
          <div class="selected-ips">
            <el-tag
              v-for="ip in selectedIPs"
              :key="ip.id"
              closable
              @close="removeSelectedIP(ip)"
            >
              {{ ip.ip_address }}
            </el-tag>
            <div v-if="selectedIPs.length === 0" class="no-selection">
              请在表格中选择要操作的IP地址
            </div>
          </div>
        </el-form-item>
        <el-form-item label="操作原因" prop="reason">
          <el-input
            v-model="bulkForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明操作原因"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showBulkDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="submitBulkOperation"
          :loading="submitting"
          :disabled="selectedIPs.length === 0"
        >
          执行操作
        </el-button>
      </template>
    </el-dialog>

    <!-- IP历史记录对话框 -->
    <el-dialog
      v-model="showHistoryDialog"
      title="IP地址历史记录"
      width="800px"
    >
      <el-table :data="historyData" v-loading="historyLoading">
        <el-table-column prop="action" label="操作" width="100" />
        <el-table-column prop="username" label="操作人" width="120" />
        <el-table-column prop="created_at" label="操作时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="old_values" label="变更前" min-width="200">
          <template #default="{ row }">
            <pre v-if="row.old_values">{{ JSON.stringify(row.old_values, null, 2) }}</pre>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="new_values" label="变更后" min-width="200">
          <template #default="{ row }">
            <pre v-if="row.new_values">{{ JSON.stringify(row.new_values, null, 2) }}</pre>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Operation, Refresh, Search } from '@element-plus/icons-vue'
import { ipAPI, subnetApi } from '@/api'
import AdvancedSearch from '@/components/AdvancedSearch.vue'

export default {
  name: 'IPManagement',
  components: {
    Plus,
    Operation,
    Refresh,
    Search,
    AdvancedSearch
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const submitting = ref(false)
    const historyLoading = ref(false)
    
    const ipList = ref([])
    const subnets = ref([])
    const selectedIPs = ref([])
    const historyData = ref([])
    
    const searchQuery = ref('')
    const statusFilter = ref('')
    const subnetFilter = ref('')
    
    const currentPage = ref(1)
    const pageSize = ref(50)
    const total = ref(0)
    
    const statistics = ref({
      total: 0,
      available: 0,
      allocated: 0,
      reserved: 0,
      utilization_rate: 0
    })
    
    // 对话框显示状态
    const showAllocationDialog = ref(false)
    const showReservationDialog = ref(false)
    const showReleaseDialog = ref(false)
    const showBulkDialog = ref(false)
    const showHistoryDialog = ref(false)
    
    // 表单数据
    const allocationForm = reactive({
      subnet_id: '',
      preferred_ip: '',
      mac_address: '',
      hostname: '',
      device_type: '',
      location: '',
      assigned_to: '',
      description: ''
    })
    
    const reservationForm = reactive({
      ip_address: '',
      reason: ''
    })
    
    const releaseForm = reactive({
      ip_address: '',
      reason: ''
    })
    
    const bulkForm = reactive({
      operation: 'reserve',
      reason: ''
    })
    
    // 表单验证规则
    const allocationRules = {
      subnet_id: [
        { required: true, message: '请选择网段', trigger: 'change' }
      ],
      mac_address: [
        { pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, message: 'MAC地址格式不正确', trigger: 'blur' }
      ]
    }
    
    const reservationRules = {
      reason: [
        { required: true, message: '请填写保留原因', trigger: 'blur' }
      ]
    }
    
    const releaseRules = {
      reason: [
        { required: true, message: '请填写释放原因', trigger: 'blur' }
      ]
    }
    
    const bulkRules = {
      operation: [
        { required: true, message: '请选择操作类型', trigger: 'change' }
      ],
      reason: [
        { required: true, message: '请填写操作原因', trigger: 'blur' }
      ]
    }
    
    // 方法
    const loadIPList = async () => {
      loading.value = true
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        
        if (searchQuery.value) {
          params.query = searchQuery.value
        }
        if (statusFilter.value) {
          params.status = statusFilter.value
        }
        if (subnetFilter.value) {
          params.subnet_id = subnetFilter.value
        }
        
        const response = await ipAPI.searchIPs(params)
        ipList.value = response.data || []
        // 注意：这里需要后端返回总数，暂时使用估算
        total.value = ipList.value.length >= pageSize.value ? 
          (currentPage.value * pageSize.value + 1) : 
          (currentPage.value - 1) * pageSize.value + ipList.value.length
      } catch (error) {
        ElMessage.error('加载IP地址列表失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    const loadSubnets = async () => {
      try {
        const response = await subnetApi.getSubnets()
        subnets.value = response.data || []
      } catch (error) {
        ElMessage.error('加载网段列表失败：' + error.message)
      }
    }
    
    const loadStatistics = async () => {
      try {
        const response = await ipAPI.getStatistics(subnetFilter.value || undefined)
        statistics.value = response.data || statistics.value
      } catch (error) {
        console.error('加载统计信息失败：', error)
      }
    }
    
    const refreshData = () => {
      loadIPList()
      loadStatistics()
    }
    
    const handleSearch = () => {
      currentPage.value = 1
      loadIPList()
    }
    
    const handleFilter = () => {
      currentPage.value = 1
      loadIPList()
      loadStatistics()
    }
    
    const handleAdvancedSearch = async (searchParams) => {
      loading.value = true
      try {
        // 存储当前搜索参数
        currentSearchParams.value = searchParams
        
        // 添加分页参数
        const params = {
          ...searchParams,
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        
        // 使用高级搜索API
        const response = await ipAPI.advancedSearchIPs(params)
        const result = response.data
        
        ipList.value = result.items || []
        total.value = result.total || 0
        
        // 更新统计信息
        loadStatistics()
      } catch (error) {
        ElMessage.error('搜索失败：' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    const handleSearchReset = () => {
      // 清除当前搜索参数
      currentSearchParams.value = null
      
      // 重置搜索条件并重新加载数据
      currentPage.value = 1
      loadIPList()
      loadStatistics()
    }
    
    // 存储当前搜索参数
    const currentSearchParams = ref(null)
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      
      // 如果有当前搜索参数，使用高级搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleAdvancedSearch(currentSearchParams.value)
      } else {
        loadIPList()
      }
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      
      // 如果有当前搜索参数，使用高级搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleAdvancedSearch(currentSearchParams.value)
      } else {
        loadIPList()
      }
    }
    
    const handleSelectionChange = (selection) => {
      selectedIPs.value = selection
    }
    
    const removeSelectedIP = (ip) => {
      const index = selectedIPs.value.findIndex(item => item.id === ip.id)
      if (index > -1) {
        selectedIPs.value.splice(index, 1)
      }
    }
    
    // IP操作方法
    const allocateIP = (row) => {
      if (row) {
        allocationForm.subnet_id = row.subnet_id
        allocationForm.preferred_ip = row.ip_address
      }
      showAllocationDialog.value = true
    }
    
    const reserveIP = (row) => {
      reservationForm.ip_address = row.ip_address
      showReservationDialog.value = true
    }
    
    const releaseIP = (row) => {
      releaseForm.ip_address = row.ip_address
      showReleaseDialog.value = true
    }
    
    const viewHistory = async (row) => {
      historyLoading.value = true
      showHistoryDialog.value = true
      try {
        const response = await ipAPI.getIPHistory(row.ip_address)
        historyData.value = response.data || []
      } catch (error) {
        ElMessage.error('加载历史记录失败：' + error.message)
      } finally {
        historyLoading.value = false
      }
    }
    
    // 表单提交方法
    const submitAllocation = async () => {
      submitting.value = true
      try {
        await ipAPI.allocateIP(allocationForm)
        ElMessage.success('IP地址分配成功')
        showAllocationDialog.value = false
        refreshData()
      } catch (error) {
        ElMessage.error('分配失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    const submitReservation = async () => {
      submitting.value = true
      try {
        await ipAPI.reserveIP(reservationForm)
        ElMessage.success('IP地址保留成功')
        showReservationDialog.value = false
        refreshData()
      } catch (error) {
        ElMessage.error('保留失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    const submitRelease = async () => {
      submitting.value = true
      try {
        await ipAPI.releaseIP(releaseForm)
        ElMessage.success('IP地址释放成功')
        showReleaseDialog.value = false
        refreshData()
      } catch (error) {
        ElMessage.error('释放失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    const submitBulkOperation = async () => {
      if (selectedIPs.value.length === 0) {
        ElMessage.warning('请选择要操作的IP地址')
        return
      }
      
      submitting.value = true
      try {
        const ipAddresses = selectedIPs.value.map(ip => ip.ip_address)
        const data = {
          ip_addresses: ipAddresses,
          operation: bulkForm.operation,
          reason: bulkForm.reason
        }
        
        const response = await ipAPI.bulkOperation(data)
        const result = response.data
        
        ElMessage.success(`批量操作完成：成功${result.success_count}个，失败${result.failed_count}个`)
        showBulkDialog.value = false
        selectedIPs.value = []
        refreshData()
      } catch (error) {
        ElMessage.error('批量操作失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    // 表单重置方法
    const resetAllocationForm = () => {
      Object.assign(allocationForm, {
        subnet_id: '',
        preferred_ip: '',
        mac_address: '',
        hostname: '',
        device_type: '',
        location: '',
        assigned_to: '',
        description: ''
      })
    }
    
    const resetReservationForm = () => {
      Object.assign(reservationForm, {
        ip_address: '',
        reason: ''
      })
    }
    
    const resetReleaseForm = () => {
      Object.assign(releaseForm, {
        ip_address: '',
        reason: ''
      })
    }
    
    const resetBulkForm = () => {
      Object.assign(bulkForm, {
        operation: 'reserve',
        reason: ''
      })
    }
    
    // 工具方法
    const getStatusTagType = (status) => {
      const typeMap = {
        available: 'success',
        allocated: 'primary',
        reserved: 'warning',
        conflict: 'danger'
      }
      return typeMap[status] || 'info'
    }
    
    const getStatusText = (status) => {
      const textMap = {
        available: '可用',
        allocated: '已分配',
        reserved: '保留',
        conflict: '冲突'
      }
      return textMap[status] || status
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    // 生命周期
    onMounted(() => {
      loadSubnets()
      loadIPList()
      loadStatistics()
    })
    
    return {
      // 响应式数据
      loading,
      submitting,
      historyLoading,
      ipList,
      subnets,
      selectedIPs,
      historyData,
      searchQuery,
      statusFilter,
      subnetFilter,
      currentPage,
      pageSize,
      total,
      statistics,
      currentSearchParams,
      
      // 对话框状态
      showAllocationDialog,
      showReservationDialog,
      showReleaseDialog,
      showBulkDialog,
      showHistoryDialog,
      
      // 表单数据
      allocationForm,
      reservationForm,
      releaseForm,
      bulkForm,
      
      // 验证规则
      allocationRules,
      reservationRules,
      releaseRules,
      bulkRules,
      
      // 方法
      refreshData,
      handleSearch,
      handleFilter,
      handleAdvancedSearch,
      handleSearchReset,
      handleSizeChange,
      handleCurrentChange,
      handleSelectionChange,
      removeSelectedIP,
      allocateIP,
      reserveIP,
      releaseIP,
      viewHistory,
      submitAllocation,
      submitReservation,
      submitRelease,
      submitBulkOperation,
      resetAllocationForm,
      resetReservationForm,
      resetReleaseForm,
      resetBulkForm,
      getStatusTagType,
      getStatusText,
      formatDate
    }
  }
}
</script>

<style scoped>
.ip-management {
  padding: 20px;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.stats-section {
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;
}

.stats-item {
  padding: 10px;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stats-label {
  font-size: 14px;
  color: #666;
}

.table-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.pagination-section {
  margin-top: 20px;
  text-align: right;
}

.selected-ips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 32px;
  align-items: center;
}

.no-selection {
  color: #999;
  font-style: italic;
}

pre {
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>