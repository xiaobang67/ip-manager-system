<template>
  <AppLayout>
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

    <!-- 简单筛选组件 -->
    <SimpleIPFilter
      @search="handleSimpleSearch"
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
      <!-- 搜索状态提示 -->
      <div v-if="currentSearchParams" class="search-status">
        <el-alert
          :title="`当前显示搜索结果：共 ${total} 条记录`"
          type="info"
          :closable="false"
          show-icon
        >
          <template #default>
            <span>当前显示搜索结果，点击"重置"按钮可查看所有数据</span>
          </template>
        </el-alert>
      </div>
      
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
        <el-table-column label="操作" width="260" fixed="right">
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
              v-if="row.status === 'available' || row.status === 'reserved'"
              type="danger"
              size="small"
              plain
              @click="deleteIP(row)"
            >
              删除
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
          <el-select 
            v-model="allocationForm.assigned_to" 
            placeholder="选择部门" 
            filterable
            allow-create
            style="width: 100%"
          >
            <el-option
              v-for="dept in departments"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
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
            <el-radio label="delete">批量删除</el-radio>
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

    <!-- IP删除对话框 -->
    <el-dialog
      v-model="showDeleteDialog"
      title="删除IP地址"
      width="500px"
      @close="resetDeleteForm"
    >
      <el-form
        ref="deleteFormRef"
        :model="deleteForm"
        :rules="deleteRules"
        label-width="100px"
      >
        <el-form-item label="IP地址">
          <el-input v-model="deleteForm.ip_address" disabled />
        </el-form-item>
        <el-form-item label="删除原因" prop="reason">
          <el-input
            v-model="deleteForm.reason"
            type="textarea"
            :rows="3"
            placeholder="请说明删除原因"
          />
        </el-form-item>
        <el-alert
          title="警告"
          type="warning"
          :closable="false"
          show-icon
        >
          <template #default>
            <p>删除IP地址将永久移除该记录，此操作不可恢复！</p>
            <p>请确认该IP地址未被使用且确实需要删除。</p>
          </template>
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="showDeleteDialog = false">取消</el-button>
        <el-button type="danger" @click="submitDelete" :loading="submitting">
          确认删除
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
  </AppLayout>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Operation, Refresh, Search } from '@element-plus/icons-vue'
import { ipAPI, subnetApi } from '@/api'
import { getDepartmentOptions } from '@/api/departments'
import AppLayout from '@/components/AppLayout.vue'
import SimpleIPFilter from '@/components/SimpleIPFilter.vue'

export default {
  name: 'IPManagement',
  components: {
    AppLayout,
    Plus,
    Operation,
    Refresh,
    Search,
    SimpleIPFilter
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const submitting = ref(false)
    const historyLoading = ref(false)
    
    const ipList = ref([])
    const subnets = ref([])
    const departments = ref([])
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
    const showDeleteDialog = ref(false)
    
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
    
    const deleteForm = reactive({
      ip_address: '',
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
    
    const deleteRules = {
      reason: [
        { required: true, message: '请填写删除原因', trigger: 'blur' }
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
        // 处理不同的响应格式
        ipList.value = response.data || response || []
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
        // 处理不同的响应格式
        subnets.value = response.subnets || response.data || []
      } catch (error) {
        ElMessage.error('加载网段列表失败：' + error.message)
      }
    }
    
    const loadDepartments = async () => {
      try {
        // 从部门管理API获取部门列表
        const response = await getDepartmentOptions()
        
        if (response && response.departments) {
          departments.value = response.departments.map(dept => dept.name).sort()
        } else {
          // 如果获取失败，使用静态列表作为备选
          departments.value = [
            '技术部',
            '运维部', 
            '产品部',
            '市场部',
            '人事部',
            '财务部',
            '客服部'
          ]
        }
        
      } catch (error) {
        console.error('加载部门列表失败：', error)
        // 如果获取失败，使用静态列表
        departments.value = [
          '技术部',
          '运维部', 
          '产品部',
          '市场部',
          '人事部',
          '财务部',
          '客服部'
        ]
      }
    }
    
    const loadStatistics = async () => {
      try {
        const response = await ipAPI.getStatistics(subnetFilter.value || undefined)
        // 处理不同的响应格式
        const stats = response.data || response || {}
        statistics.value = {
          total: stats.total_ips || 0,
          available: stats.available_ips || 0,
          allocated: stats.allocated_ips || 0,
          reserved: stats.reserved_ips || 0,
          utilization_rate: stats.utilization_rate || 0
        }
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
    
    const handleSimpleSearch = async (searchParams) => {
      loading.value = true
      try {
        // 存储当前搜索参数
        currentSearchParams.value = searchParams
        
        // 更新内部筛选状态
        searchQuery.value = searchParams.query || ''
        statusFilter.value = searchParams.status || ''
        subnetFilter.value = searchParams.subnet_id || ''
        
        // 重置分页到第一页
        currentPage.value = 1
        
        // 添加分页参数
        const params = {
          ...searchParams,
          skip: 0, // 搜索时总是从第一页开始
          limit: pageSize.value
        }
        
        console.log('搜索参数:', params) // 调试信息
        
        // 使用简单搜索API
        const response = await ipAPI.searchIPs(params)
        const results = response.data || response || []
        
        console.log('搜索结果:', results) // 调试信息
        
        ipList.value = results
        
        // 更准确的总数计算
        total.value = results.length
        
        // 显示搜索结果提示
        if (Object.keys(searchParams).length > 0) {
          const hasQuery = searchParams.query
          const hasFilters = searchParams.subnet_id || searchParams.status || searchParams.assigned_to
          
          if (results.length === 0) {
            ElMessage.warning('未找到匹配的IP地址')
          } else {
            let message = ''
            if (hasQuery && hasFilters) {
              message = `找到 ${results.length} 个匹配条件的IP地址`
            } else if (hasQuery) {
              message = `找到 ${results.length} 个匹配 "${searchParams.query}" 的IP地址`
            } else {
              message = `筛选结果：${results.length} 个IP地址`
            }
            
            // 使用info类型的消息，避免过于频繁的成功提示
            ElMessage({
              message: message,
              type: 'info',
              duration: 2000
            })
          }
        }
        
        // 更新统计信息
        loadStatistics()
      } catch (error) {
        console.error('搜索错误:', error) // 调试信息
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
      
      // 如果有当前搜索参数，使用简单搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleSimpleSearch(currentSearchParams.value)
      } else {
        loadIPList()
      }
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      
      // 如果有当前搜索参数，使用简单搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleSimpleSearch(currentSearchParams.value)
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
    
    const deleteIP = (row) => {
      deleteForm.ip_address = row.ip_address
      showDeleteDialog.value = true
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
        const result = response.data || response
        
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
      loadDepartments()
      loadIPList()
      loadStatistics()
    })
    
    // 删除IP地址的提交方法
    const submitDelete = async () => {
      submitting.value = true
      try {
        await ipAPI.deleteIP(deleteForm)
        ElMessage.success('IP地址删除成功')
        showDeleteDialog.value = false
        refreshData()
      } catch (error) {
        ElMessage.error('删除失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    // 删除表单重置方法
    const resetDeleteForm = () => {
      Object.assign(deleteForm, {
        ip_address: '',
        reason: ''
      })
    }

    return {
      // 响应式数据
      loading,
      submitting,
      historyLoading,
      ipList,
      subnets,
      departments,
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
      showDeleteDialog,
      
      // 表单数据
      allocationForm,
      reservationForm,
      releaseForm,
      bulkForm,
      deleteForm,
      
      // 验证规则
      allocationRules,
      reservationRules,
      releaseRules,
      bulkRules,
      deleteRules,
      
      // 方法
      refreshData,
      handleSearch,
      handleFilter,
      handleSimpleSearch,
      handleSearchReset,
      handleSizeChange,
      handleCurrentChange,
      handleSelectionChange,
      removeSelectedIP,
      allocateIP,
      reserveIP,
      releaseIP,
      deleteIP,
      viewHistory,
      submitAllocation,
      submitReservation,
      submitRelease,
      submitBulkOperation,
      submitDelete,
      resetAllocationForm,
      resetReservationForm,
      resetReleaseForm,
      resetBulkForm,
      resetDeleteForm,
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
  background-color: var(--bg-color-page);
  color: var(--text-color-primary);
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-section h1 {
  color: var(--text-color-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: var(--fill-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-color-primary);
}

.stats-section {
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;
  background: var(--bg-color) !important;
  border: 1px solid var(--border-color) !important;
  transition: all 0.3s ease !important;
}

.stats-card:hover {
  border-color: var(--primary-color) !important;
  box-shadow: var(--box-shadow-light) !important;
}

.stats-item {
  padding: 10px;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--primary-color) !important;
  margin-bottom: 5px;
}

.stats-label {
  font-size: 14px;
  color: var(--text-color-secondary) !important;
}

.table-section {
  background: var(--bg-color) !important;
  border: 1px solid var(--border-color) !important;
  border-radius: 8px;
  padding: 20px;
  color: var(--text-color-primary) !important;
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