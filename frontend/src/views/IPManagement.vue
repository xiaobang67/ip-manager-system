<template>
  <AppLayout>
    <div class="ip-management">
    <!-- 页面标题和操作栏 -->
    <div class="header-section">
      <h1>IP地址管理</h1>
      <div class="header-actions">
        <el-button v-if="!isReadonly" type="primary" @click="showBulkDialog = true">
          <el-icon><Operation /></el-icon>
          批量操作
        </el-button>
          <el-button type="primary" @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
      </div>
    </div>

    <!-- 简单筛选组件 - 只读用户不显示 -->
    <SimpleIPFilter
      v-if="!isReadonly"
      @search="handleSimpleSearch"
      @reset="handleSearchReset"
    />

    <!-- 统计信息卡片 - 只读用户不显示 -->
    <div v-if="!isReadonly" class="stats-section">
      <el-row :gutter="20" class="stats-row">
        <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.total }}</div>
              <div class="stats-label">总IP数量</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.available }}</div>
              <div class="stats-label">可用IP</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.allocated }}</div>
              <div class="stats-label">使用中</div>
            </div>
          </el-card>
        </el-col>
        <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
          <el-card class="stats-card">
            <div class="stats-item">
              <div class="stats-value">{{ statistics.utilization_rate }}%</div>
              <div class="stats-label">使用率</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 只读用户的简化搜索框 -->
    <div v-if="isReadonly" class="readonly-search-section">
      <div class="readonly-search-container">
        <el-input
          v-model="readonlySearchQuery"
          placeholder="搜索IP地址、使用人、MAC地址..."
          @keyup.enter="handleReadonlySearch"
          clearable
          size="large"
          class="readonly-search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
          <template #append>
            <el-button type="primary" @click="handleReadonlySearch" :loading="loading">
              搜索
            </el-button>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 只读用户的搜索提示 -->
    <div v-if="isReadonly && !hasSearched" class="readonly-search-hint">
      <div class="search-hint-content">
        <el-icon class="search-hint-icon"><Search /></el-icon>
        <h3>请输入搜索关键词查询IP地址</h3>
        <p>支持搜索IP地址、使用人、MAC地址等信息</p>
      </div>
    </div>

    <!-- IP地址列表表格 -->
    <div v-if="!isReadonly || hasSearched" class="table-section">
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
      
      <!-- 只读用户的搜索结果提示 -->
      <div v-if="isReadonly && hasSearched" class="readonly-search-result">
        <el-alert
          :title="`搜索结果：共找到 ${total} 条记录`"
          type="success"
          :closable="false"
          show-icon
        >
          <template #default>
            <span v-if="readonlySearchQuery">关键词："{{ readonlySearchQuery }}"</span>
            <span v-else>显示所有IP地址</span>
          </template>
        </el-alert>
      </div>
      
      <el-table
        :data="ipList"
        v-loading="loading"
        stripe
        @selection-change="handleSelectionChange"
        class="responsive-table"
        :class="{ 'readonly-table': isReadonly }"
        style="width: 100%"
      >
        <el-table-column v-if="!isReadonly" type="selection" width="50" />
        <el-table-column prop="ip_address" label="IP地址" sortable align="center" />
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
        <el-table-column prop="user_name" label="使用人" align="center">
          <template #default="{ row }">
            <span>{{ row.user_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="mac_address" label="MAC地址" align="center">
          <template #default="{ row }">
            <span>{{ row.mac_address || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="device_type" label="设备类型" align="center">
          <template #default="{ row }">
            <span>{{ getDeviceTypeName(row.device_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_to" label="所属部门" align="center">
          <template #default="{ row }">
            <span>{{ row.assigned_to || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip align="center">
          <template #default="{ row }">
            <span>{{ row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="allocated_at" label="分配时间" align="center">
          <template #default="{ row }">
            <span>{{ row.allocated_at ? formatDate(row.allocated_at) : '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="!isReadonly" label="操作" width="300" fixed="right" align="center">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-button
                v-if="row.status === 'available'"
                type="primary"
                size="small"
                @click="allocateIP(row)"
                class="btn-allocation"
              >
                分配
              </el-button>
              <el-button
                type="info"
                size="small"
                @click="editIP(row)"
                class="btn-edit"
              >
                编辑
              </el-button>
              <el-button
                v-if="row.status === 'available'"
                type="warning"
                size="small"
                @click="reserveIP(row)"
                class="btn-reservation"
              >
                保留
              </el-button>
              <el-button
                v-if="row.status === 'allocated' || row.status === 'reserved'"
                type="danger"
                size="small"
                @click="releaseIP(row)"
                class="btn-release"
              >
                释放
              </el-button>
              <el-button
                v-if="(row.status === 'available' || row.status === 'reserved') && isAdmin"
                type="danger"
                size="small"
                plain
                @click="deleteIP(row)"
                class="btn-delete"
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
      title="分配地址"
      width="600px"
      @close="resetAllocationForm"
    >
      <el-form
        ref="allocationFormRef"
        :model="allocationForm"
        :rules="allocationRules"
        label-width="100px"
      >
        <el-form-item label="网段" prop="subnet_id" required>
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
        <el-form-item label="使用人" prop="user_name" required>
          <el-input v-model="allocationForm.user_name" placeholder="使用人" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type" required>
          <el-select v-model="allocationForm.device_type" placeholder="选择设备类型" style="width: 100%">
            <el-option
              v-for="deviceType in deviceTypes"
              :key="deviceType.code"
              :label="deviceType.name"
              :value="deviceType.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用部门" prop="assigned_to" required>
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
        <el-form-item label="分配时间" prop="allocated_at" required>
          <el-date-picker
            v-model="allocationForm.allocated_at"
            type="datetime"
            placeholder="选择分配时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
          <div class="form-tip">默认为当前时间，可手动修改</div>
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
        <el-button type="primary" @click="submitAllocation" :loading="submitting" class="btn-allocation">
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
        <el-button type="warning" @click="submitReservation" :loading="submitting" class="btn-reservation">
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
        <el-button type="danger" @click="submitRelease" :loading="submitting" class="btn-release">
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
            <el-radio v-if="isAdmin" label="delete">批量删除</el-radio>
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
          :type="getBulkOperationButtonType()"
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
        <el-button type="danger" @click="submitDelete" :loading="submitting" class="btn-delete">
          确认删除
        </el-button>
      </template>
    </el-dialog>

    <!-- IP编辑对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑IP地址"
      width="600px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="IP地址">
          <el-input v-model="editForm.ip_address" disabled />
        </el-form-item>
        <el-form-item label="MAC地址" prop="mac_address">
          <el-input v-model="editForm.mac_address" placeholder="如：00:11:22:33:44:55" />
        </el-form-item>
        <el-form-item label="使用人" prop="user_name" required>
          <el-input v-model="editForm.user_name" placeholder="使用人" />
        </el-form-item>
        <el-form-item label="设备类型" prop="device_type" required>
          <el-select v-model="editForm.device_type" placeholder="选择设备类型" style="width: 100%">
            <el-option
              v-for="deviceType in deviceTypes"
              :key="deviceType.code"
              :label="deviceType.name"
              :value="deviceType.code"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="使用部门" prop="assigned_to" required>
          <el-select 
            v-model="editForm.assigned_to" 
            placeholder="选择部门" 
            filterable
            allow-create
            style="width: 100%"
            popper-class="ip-management-select-dropdown"
            @visible-change="handleSelectVisibleChange"
          >
            <el-option
              v-for="dept in departments"
              :key="dept"
              :label="dept"
              :value="dept"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="分配时间" prop="allocated_at">
          <el-date-picker
            v-model="editForm.allocated_at"
            type="datetime"
            placeholder="选择分配时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="info" @click="submitEdit" :loading="submitting" class="btn-edit">
          确认修改
        </el-button>
      </template>
    </el-dialog>


    </div>
  </AppLayout>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Operation, Refresh, Search } from '@element-plus/icons-vue'
import { ipAPI, subnetApi } from '@/api'
import { getDepartmentOptions } from '@/api/departments'
import { getDeviceTypeOptions } from '@/api/deviceTypes'
import AppLayout from '@/components/AppLayout.vue'
import SimpleIPFilter from '@/components/SimpleIPFilter.vue'
import { useStore } from 'vuex'

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
    // Vuex store
    const store = useStore()
    
    // 用户权限相关
    const currentUser = computed(() => store.getters['auth/currentUser'])
    const userRole = computed(() => store.getters['auth/userRole'])
    const isAdmin = computed(() => userRole.value?.toLowerCase() === 'admin')
    const isReadonly = computed(() => userRole.value?.toLowerCase() === 'readonly')
    
    // 响应式数据
    const loading = ref(false)
    const submitting = ref(false)
    
    const ipList = ref([])
    const subnets = ref([])
    const departments = ref([])
    const deviceTypes = ref([])
    const selectedIPs = ref([])
    
    const searchQuery = ref('')
    const statusFilter = ref('')
    const subnetFilter = ref('')
    
    // 只读用户的搜索
    const readonlySearchQuery = ref('')
    const hasSearched = ref(false)
    
    const currentPage = ref(1)
    const pageSize = ref(20)
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
    const showDeleteDialog = ref(false)
    const showEditDialog = ref(false)
    
    // 表单数据
    const allocationForm = reactive({
      subnet_id: '',
      preferred_ip: '',
      mac_address: '',
      user_name: '',
      device_type: '',
      location: '',
      assigned_to: '',
      description: '',
      allocated_at: null
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
    
    const editForm = reactive({
      ip_address: '',
      mac_address: '',
      user_name: '',
      device_type: '',
      assigned_to: '',
      description: '',
      allocated_at: null
    })
    
    // 表单验证规则
    const allocationRules = {
      subnet_id: [
        { required: true, message: '请选择网段', trigger: 'change' }
      ],
      user_name: [
        { required: true, message: '请填写使用人', trigger: 'blur' }
      ],
      device_type: [
        { required: true, message: '请选择设备类型', trigger: 'change' }
      ],
      assigned_to: [
        { required: true, message: '请选择使用部门', trigger: 'change' }
      ],
      allocated_at: [
        { required: true, message: '请选择分配时间', trigger: 'change' }
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
    
    const editRules = {
      user_name: [
        { required: true, message: '请填写使用人', trigger: 'blur' }
      ],
      device_type: [
        { required: true, message: '请选择设备类型', trigger: 'change' }
      ],
      assigned_to: [
        { required: true, message: '请选择使用部门', trigger: 'change' }
      ],
      mac_address: [
        { pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, message: 'MAC地址格式不正确', trigger: 'blur' }
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
        const response = await getDepartmentOptions()
        
        if (response && response.data && response.data.departments) {
          // 处理API响应格式：response.data.departments
          const apiDepartments = response.data.departments.map(dept => dept.name).sort()
          departments.value = apiDepartments
        } else if (response && response.departments) {
          // 处理直接响应格式：response.departments
          const apiDepartments = response.departments.map(dept => dept.name).sort()
          departments.value = apiDepartments
        } else {
          console.warn('部门API返回格式不正确:', response)
          departments.value = []
        }
      } catch (error) {
        console.error('从API加载部门列表失败：', error)
        departments.value = []
      }
    }
    
    const loadDeviceTypes = async () => {
      try {
        // 从设备类型管理API获取设备类型列表
        const response = await getDeviceTypeOptions()
        
        if (response && response.data && Array.isArray(response.data)) {
          // 处理API响应格式：response.data
          deviceTypes.value = response.data.filter(type => type.status === 'active')
        } else if (response && Array.isArray(response)) {
          // 处理直接响应格式：response
          deviceTypes.value = response.filter(type => type.status === 'active')
        } else {
          // 如果获取失败，使用静态列表作为备选
          deviceTypes.value = [
            { code: 'server', name: '服务器' },
            { code: 'desktop', name: '台式机' },
            { code: 'laptop', name: '笔记本电脑' },
            { code: 'switch', name: '网络交换机' },
            { code: 'router', name: '路由器' },
            { code: 'printer', name: '打印机' },
            { code: 'firewall', name: '防火墙' },
            { code: 'other', name: '其他' }
          ]
        }
      } catch (error) {
        console.error('加载设备类型列表失败：', error)
        // 如果获取失败，使用静态列表
        deviceTypes.value = [
          { code: 'server', name: '服务器' },
          { code: 'desktop', name: '台式机' },
          { code: 'laptop', name: '笔记本电脑' },
          { code: 'switch', name: '网络交换机' },
          { code: 'router', name: '路由器' },
          { code: 'printer', name: '打印机' },
          { code: 'firewall', name: '防火墙' },
          { code: 'other', name: '其他' }
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
      console.log('=== 刷新按钮被点击 ===')
      ElMessage.info('正在刷新数据...')
      
      console.log('当前用户角色:', userRole.value)
      console.log('当前用户名:', currentUser.value?.username)
      console.log('当前路由:', window.location.pathname)
      console.log('认证状态:', store.getters['auth/isAuthenticated'])
      
      // 检查用户信息是否正确
      if (!currentUser.value) {
        console.error('用户信息丢失，可能需要重新登录')
        ElMessage.error('用户信息丢失，请重新登录')
        store.dispatch('auth/logout')
        return
      }
      
      // 重置到第一页
      currentPage.value = 1
      
      // 清除搜索参数
      currentSearchParams.value = null
      
      // 重新加载数据
      loadIPList()
      loadStatistics()
      
      console.log('=== 刷新数据完成 ===')
      ElMessage.success('数据刷新完成')
    }
    
    // 刷新当前页面数据，保持分页状态
    const refreshCurrentPageData = () => {
      console.log('=== 刷新当前页面数据 ===')
      console.log('保持当前页面:', currentPage.value)
      
      // 如果有当前搜索参数，使用简单搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleSimpleSearch(currentSearchParams.value, false) // 不重置页码
      } else {
        loadIPList()
      }
      loadStatistics()
      
      console.log('=== 当前页面数据刷新完成 ===')
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
    
    const handleSimpleSearch = async (searchParams, resetPage = true) => {
      loading.value = true
      try {
        // 存储当前搜索参数
        currentSearchParams.value = searchParams
        
        // 更新内部筛选状态
        searchQuery.value = searchParams.query || ''
        statusFilter.value = searchParams.status || ''
        subnetFilter.value = searchParams.subnet_id || ''
        
        // 只在新搜索时重置分页到第一页
        if (resetPage) {
          currentPage.value = 1
        }
        
        // 添加分页参数
        const params = {
          ...searchParams,
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        

        
        // 使用简单搜索API
        const response = await ipAPI.searchIPs(params)

        
        // 处理新的响应格式
        if (response.data && Array.isArray(response.data)) {
          // 新格式：{data: [...], total: number}
          ipList.value = response.data
          total.value = response.total || response.data.length
        } else if (Array.isArray(response.data)) {
          // 备用格式：response.data是数组
          ipList.value = response.data
          total.value = response.data.length
        } else if (Array.isArray(response)) {
          // 旧格式：response直接是数组
          ipList.value = response
          total.value = response.length
        } else {
          // 未知格式

          ipList.value = []
          total.value = 0
        }
        

        
        // 显示搜索结果提示
        if (Object.keys(searchParams).length > 0) {
          const hasQuery = searchParams.query
          const hasFilters = searchParams.subnet_id || searchParams.status || searchParams.assigned_to
          
          // 搜索结果提示已禁用
        }
        
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
    
    // 只读用户的搜索处理
    const handleReadonlySearch = async () => {
      // 检查是否有搜索内容
      if (!readonlySearchQuery.value || !readonlySearchQuery.value.trim()) {
        ElMessage.warning('请输入搜索关键词')
        return
      }
      
      loading.value = true
      try {
        currentPage.value = 1
        hasSearched.value = true // 标记已经搜索过
        
        const params = {
          skip: 0,
          limit: pageSize.value,
          query: readonlySearchQuery.value.trim()
        }
        
        // 保存当前搜索参数，用于分页时保持搜索状态
        currentSearchParams.value = {
          query: readonlySearchQuery.value.trim()
        }
        
        const response = await ipAPI.searchIPs(params)
        
        // 处理响应格式
        if (response.data && Array.isArray(response.data)) {
          ipList.value = response.data
          total.value = response.total || response.data.length
        } else if (Array.isArray(response)) {
          ipList.value = response
          total.value = response.length
        } else {
          ipList.value = []
          total.value = 0
        }
        
        // 显示搜索结果提示
        if (ipList.value.length === 0) {
          ElMessage.info('未找到匹配的IP地址')
        } else {
          ElMessage.success(`找到 ${total.value} 条匹配记录`)
        }
        
      } catch (error) {
        ElMessage.error('搜索失败：' + error.message)
        hasSearched.value = false // 搜索失败时重置状态
        currentSearchParams.value = null // 清除搜索参数
      } finally {
        loading.value = false
      }
    }
    
    // 存储当前搜索参数
    const currentSearchParams = ref(null)
    
    // 表单引用
    const allocationFormRef = ref(null)
    const editFormRef = ref(null)
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      
      // 如果有当前搜索参数，使用简单搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleSimpleSearch(currentSearchParams.value, false) // 不重置页码
      } else {
        loadIPList()
      }
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      
      // 如果有当前搜索参数，使用简单搜索，否则使用普通加载
      if (currentSearchParams.value) {
        handleSimpleSearch(currentSearchParams.value, false) // 不重置页码
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
      // 默认设置当前时间为分配时间，格式化为字符串以匹配日期选择器的格式
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      const hours = String(now.getHours()).padStart(2, '0')
      const minutes = String(now.getMinutes()).padStart(2, '0')
      const seconds = String(now.getSeconds()).padStart(2, '0')
      allocationForm.allocated_at = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
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
    
    const editIP = (row) => {
      // 填充编辑表单数据
      editForm.ip_address = row.ip_address
      editForm.mac_address = row.mac_address || ''
      editForm.user_name = row.user_name || ''
      editForm.device_type = row.device_type || ''
      editForm.assigned_to = row.assigned_to || ''
      editForm.description = row.description || ''
      editForm.allocated_at = row.allocated_at || null
      showEditDialog.value = true
      
      // 延迟修复下拉框样式
      setTimeout(() => {
        fixDropdownStyles()
      }, 100)
    }
    
    // 处理下拉框可见性变化
    const handleSelectVisibleChange = (visible) => {
      if (visible) {
        // 下拉框打开时，延迟应用样式修复
        setTimeout(() => {
          fixDropdownStyles()
        }, 50)
      }
    }
    
    // 修复下拉框样式的函数
    const fixDropdownStyles = () => {
      // 检查多种暗黑模式标识
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark' ||
                     document.body.classList.contains('dark') ||
                     document.documentElement.classList.contains('dark')
      
      // 延迟执行以确保DOM已渲染
      setTimeout(() => {
        // 查找IP管理页面的下拉框
        const dropdowns = document.querySelectorAll('.ip-management-select-dropdown, .el-select-dropdown')
        
        dropdowns.forEach(dropdown => {
          if (isDark) {
            // 应用暗黑模式样式
            dropdown.style.setProperty('background-color', '#1d1e1f', 'important')
            dropdown.style.setProperty('border-color', '#414243', 'important')
            dropdown.style.setProperty('color', '#e5eaf3', 'important')
            
            // 修复选项样式
            const items = dropdown.querySelectorAll('.el-select-dropdown__item')
            items.forEach(item => {
              item.style.setProperty('color', '#e5eaf3', 'important')
              item.style.setProperty('background-color', 'transparent', 'important')
              
              // 移除旧的事件监听器（如果存在）
              item.removeEventListener('mouseenter', item._darkModeEnterHandler)
              item.removeEventListener('mouseleave', item._darkModeLeaveHandler)
              
              // 添加新的悬停事件处理器
              item._darkModeEnterHandler = () => {
                if (isDark && !item.classList.contains('selected')) {
                  item.style.setProperty('background-color', '#262727', 'important')
                  item.style.setProperty('color', '#e5eaf3', 'important')
                }
              }
              
              item._darkModeLeaveHandler = () => {
                if (isDark && !item.classList.contains('selected')) {
                  item.style.setProperty('background-color', 'transparent', 'important')
                  item.style.setProperty('color', '#e5eaf3', 'important')
                }
              }
              
              item.addEventListener('mouseenter', item._darkModeEnterHandler)
              item.addEventListener('mouseleave', item._darkModeLeaveHandler)
              
              // 处理选中状态
              if (item.classList.contains('selected')) {
                item.style.setProperty('background-color', '#409eff', 'important')
                item.style.setProperty('color', '#ffffff', 'important')
              }
            })
          }
        })
      }, 10)
    }
    

    
    // 表单提交方法
    const submitAllocation = async () => {
      // 先进行表单验证
      if (!allocationFormRef.value) return
      
      try {
        await allocationFormRef.value.validate()
      } catch (error) {
        ElMessage.warning('请填写完整的必填信息')
        return
      }
      
      submitting.value = true
      try {
        // 准备提交数据，确保时间格式正确
        const submitData = { ...allocationForm }
        if (submitData.allocated_at) {
          // 确保时间格式为ISO格式
          const date = new Date(submitData.allocated_at)
          submitData.allocated_at = date.toISOString()
        }
        
        console.log('提交分配数据:', submitData) // 调试日志
        
        await ipAPI.allocateIP(submitData)
        ElMessage.success('IP地址分配成功')
        showAllocationDialog.value = false
        refreshCurrentPageData()
      } catch (error) {
        console.error('分配失败:', error) // 调试日志
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
        refreshCurrentPageData()
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
        refreshCurrentPageData()
      } catch (error) {
        ElMessage.error('释放失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    const getBulkOperationButtonType = () => {
      switch (bulkForm.operation) {
        case 'reserve':
          return 'warning'  // 🟠 保留操作使用橙色
        case 'release':
          return 'danger'   // 🔴 释放操作使用红色
        case 'delete':
          return 'danger'   // 🔴 删除操作使用红色
        default:
          return 'primary'  // 默认使用蓝色
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
        refreshCurrentPageData()
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
        user_name: '',
        device_type: '',
        location: '',
        assigned_to: '',
        description: '',
        allocated_at: null
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
    
    const getStatusStyle = (status) => {
      const styleMap = {
        available: {
          backgroundColor: '#f0f9ff',
          borderColor: '#67c23a',
          color: '#67c23a'
        },
        allocated: {
          backgroundColor: '#ecf5ff',
          borderColor: '#409eff',
          color: '#409eff'
        },
        reserved: {
          backgroundColor: '#fdf6ec',
          borderColor: '#e6a23c',
          color: '#e6a23c'
        },
        conflict: {
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
        available: '可用',
        allocated: '使用中',
        reserved: '保留',
        conflict: '冲突'
      }
      return textMap[status] || status
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return '-'
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    const getDeviceTypeName = (deviceTypeCode) => {
      if (!deviceTypeCode) return '-'
      
      // 优先从动态加载的设备类型列表中查找（这样可以获取最新的自定义名称）
      if (deviceTypes.value && deviceTypes.value.length > 0) {
        const deviceType = deviceTypes.value.find(type => type.code === deviceTypeCode)
        if (deviceType && deviceType.name) {
          return deviceType.name
        }
      }
      
      // 如果动态列表中找不到，使用默认映射作为备选方案
      const defaultMapping = {
        'server': '服务器',
        'desktop': '台式机',
        'laptop': '笔记本电脑',
        'switch': '网络交换机',
        'router': '路由器',
        'printer': '打印机',
        'firewall': '防火墙',
        'access_point': '无线接入点',
        'scanner': '扫描仪',
        'other': '其他',
        'tablet': '平板电脑',
        'phone': '手机',
        'camera': '摄像头',
        'storage': '存储设备',
        'monitor': '显示器',
        'projector': '投影仪'
      }
      
      if (defaultMapping[deviceTypeCode]) {
        return defaultMapping[deviceTypeCode]
      }
      
      // 如果都找不到，返回代码本身
      return deviceTypeCode
    }
    
    // 生命周期
    onMounted(async () => {
      // 先加载基础数据
      await Promise.all([
        loadSubnets(),
        loadDepartments(),
        loadDeviceTypes()
      ])
      
      // 然后加载IP列表和统计信息
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
        refreshCurrentPageData()
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
    
    // 编辑IP地址的提交方法
    const submitEdit = async () => {
      console.log('submitEdit 方法被调用')
      console.log('editFormRef.value:', editFormRef.value)
      console.log('editForm 数据:', editForm)
      
      // 先进行表单验证
      if (!editFormRef.value) {
        console.log('editFormRef.value 为空，返回')
        return
      }
      
      try {
        console.log('开始表单验证')
        await editFormRef.value.validate()
        console.log('表单验证通过')
      } catch (error) {
        console.log('表单验证失败:', error)
        ElMessage.warning('请填写完整的必填信息')
        return
      }
      
      submitting.value = true
      try {
        // 准备提交数据
        const submitData = { ...editForm }
        if (submitData.allocated_at) {
          // 确保时间格式为MySQL兼容格式 YYYY-MM-DD HH:mm:ss
          const date = new Date(submitData.allocated_at)
          const year = date.getFullYear()
          const month = String(date.getMonth() + 1).padStart(2, '0')
          const day = String(date.getDate()).padStart(2, '0')
          const hours = String(date.getHours()).padStart(2, '0')
          const minutes = String(date.getMinutes()).padStart(2, '0')
          const seconds = String(date.getSeconds()).padStart(2, '0')
          submitData.allocated_at = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
        }
        
        await ipAPI.updateIP(editForm.ip_address, submitData)
        ElMessage.success('IP地址修改成功')
        showEditDialog.value = false
        refreshCurrentPageData()
      } catch (error) {
        ElMessage.error('修改失败：' + error.message)
      } finally {
        submitting.value = false
      }
    }
    
    // 编辑表单重置方法
    const resetEditForm = () => {
      Object.assign(editForm, {
        ip_address: '',
        mac_address: '',
        user_name: '',
        device_type: '',
        assigned_to: '',
        description: '',
        allocated_at: null
      })
    }

    return {
      // 用户权限
      currentUser,
      userRole,
      isAdmin,
      isReadonly,
      
      // 响应式数据
      loading,
      submitting,
      ipList,
      subnets,
      departments,
      deviceTypes,
      selectedIPs,
      searchQuery,
      statusFilter,
      subnetFilter,
      currentPage,
      pageSize,
      total,
      statistics,
      currentSearchParams,
      
      // 只读用户搜索
      readonlySearchQuery,
      hasSearched,
      
      // 对话框状态
      showAllocationDialog,
      showReservationDialog,
      showReleaseDialog,
      showBulkDialog,
      showDeleteDialog,
      showEditDialog,
      
      // 表单数据
      allocationForm,
      reservationForm,
      releaseForm,
      bulkForm,
      deleteForm,
      editForm,
      
      // 验证规则
      allocationRules,
      reservationRules,
      releaseRules,
      bulkRules,
      deleteRules,
      editRules,
      
      // 表单引用
      allocationFormRef,
      editFormRef,
      
      // 方法
      refreshData,
      refreshCurrentPageData,
      handleSearch,
      handleFilter,
      handleSimpleSearch,
      handleSearchReset,
      handleReadonlySearch,
      handleSizeChange,
      handleCurrentChange,
      handleSelectionChange,
      removeSelectedIP,
      allocateIP,
      reserveIP,
      releaseIP,
      deleteIP,
      editIP,
      fixDropdownStyles,
      handleSelectVisibleChange,
      submitAllocation,
      submitReservation,
      submitRelease,
      submitBulkOperation,
      submitDelete,
      submitEdit,
      resetAllocationForm,
      resetReservationForm,
      resetReleaseForm,
      resetBulkForm,
      resetDeleteForm,
      resetEditForm,
      getBulkOperationButtonType,
      getStatusTagType,
      getStatusStyle,
      getStatusText,
      formatDate,
      getDeviceTypeName
    }
  }
}
</script>

<style scoped>
.ip-management {
  padding: 20px;
  background-color: var(--bg-primary-page);
  color: var(--text-primary);
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-section h1 {
  color: var(--text-primary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-section {
  margin-bottom: 20px;
  padding: 20px;
  background: var(--fill-primary);
  border: 1px solid var(--border-primary);
  border-radius: 8px;
  color: var(--text-primary);
}

.stats-section {
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;
  background: var(--bg-primary) !important;
  border: 1px solid var(--border-primary) !important;
  transition: all 0.3s ease !important;
}

.stats-card:hover {
  border-color: var(--primary) !important;
  box-shadow: var(--shadow-light-light) !important;
}

.stats-item {
  padding: 10px;
}

.stats-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--primary) !important;
  margin-bottom: 5px;
}

.stats-label {
  font-size: 14px;
  color: var(--text-tertiary) !important;
}

.table-section {
  background: var(--bg-primary) !important;
  border: 1px solid var(--border-primary) !important;
  border-radius: 8px;
  padding: 20px;
  color: var(--text-primary) !important;
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
  color: var(--text-quaternary);
  font-style: italic;
}

pre {
  font-size: 12px;
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
<style sc
oped>
/* 表单提示样式 */
.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 4px;
  line-height: 1.4;
}

/* 页面布局样式 */
.ip-management {
  padding: 0;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: var(--bg-primary);
  border-radius: 8px;
  box-shadow: var(--shadow-light-base);
}

.header-section h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stats-section {
  margin-bottom: 20px;
}

.stats-card {
  text-align: center;
  border-radius: 8px;
  box-shadow: var(--shadow-light-base);
}

.stats-item {
  padding: 20px;
}

.stats-value {
  font-size: 32px;
  font-weight: bold;
  color: var(--primary);
  margin-bottom: 8px;
}

.stats-label {
  font-size: 14px;
  color: var(--text-tertiary);
}

.table-section {
  background: var(--bg-primary);
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--shadow-light-base);
}

.search-status {
  margin-bottom: 16px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.selected-ips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 32px;
  align-items: center;
}

.no-selection {
  color: var(--text-quaternary);
  font-size: 14px;
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
  align-items: center;
  min-width: 280px;
}

.action-buttons .el-button {
  margin: 0;
  min-width: 50px;
  height: 28px;
  font-size: 12px;
  padding: 4px 8px;
}

/* 强制修复按钮颜色 - 覆盖全局样式 */
.ip-management .action-buttons .el-button--primary {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
}

/* 修复暗黑模式下下拉框选项显示问题 */
:deep(.el-select-dropdown) {
  background-color: var(--bg-primary) !important;
  border: 1px solid var(--border-primary) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item) {
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item:hover) {
  background-color: var(--fill-secondary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item.selected) {
  background-color: var(--primary) !important;
  color: #ffffff !important;
}

/* 修复下拉框输入框在暗黑模式下的显示 */
:deep(.el-select .el-input__inner) {
  background-color: var(--fill-primary) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-select .el-input__inner:focus) {
  border-color: var(--primary) !important;
}

/* 修复下拉箭头颜色 */
:deep(.el-select .el-input__suffix .el-input__suffix-inner .el-select__caret) {
  color: var(--text-primary) !important;
}

.ip-management .action-buttons .el-button--primary:hover {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
  color: #ffffff !important;
}

.ip-management .action-buttons .el-button--warning {
  background-color: #e6a23c !important;
  border-color: #e6a23c !important;
  color: #ffffff !important;
}

.ip-management .action-buttons .el-button--warning:hover {
  background-color: #ebb563 !important;
  border-color: #ebb563 !important;
  color: #ffffff !important;
}

.ip-management .action-buttons .el-button--danger {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: #ffffff !important;
}

.ip-management .action-buttons .el-button--danger:hover {
  background-color: #f78989 !important;
  border-color: #f78989 !important;
  color: #ffffff !important;
}

.ip-management .action-buttons .el-button--danger.is-plain {
  background-color: transparent !important;
  border-color: #f56c6c !important;
  color: #f56c6c !important;
}

.ip-management .action-buttons .el-button--danger.is-plain:hover {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: #ffffff !important;
}
.ip-management .action-buttons .el-button--info {
  background-color: #909399 !important;
  border-color: #909399 !important;
  color: #ffffff !important;
}

.ip-management .action-buttons .el-button--info:hover {
  background-color: #a6a9ad !important;
  border-color: #a6a9ad !important;
  color: #ffffff !important;
}

/* 表格单元格对齐 */
.el-table .cell {
  text-align: center;
}

/* 状态标签样式 */
.el-tag {
  font-weight: 500;
}

/* 确保状态标签颜色正确显示 */
.ip-management .el-tag.el-tag--success,
.ip-management .status-available {
  background-color: #f0f9ff !important;
  border-color: #67c23a !important;
  color: #67c23a !important;
}

.ip-management .el-tag.el-tag--primary,
.ip-management .status-allocated {
  background-color: #ecf5ff !important;
  border-color: #409eff !important;
  color: #409eff !important;
}

.ip-management .el-tag.el-tag--warning,
.ip-management .status-reserved {
  background-color: #fdf6ec !important;
  border-color: #e6a23c !important;
  color: #e6a23c !important;
}

.ip-management .el-tag.el-tag--danger,
.ip-management .status-conflict {
  background-color: #fef0f0 !important;
  border-color: #f56c6c !important;
  color: #f56c6c !important;
}

.ip-management .el-tag.el-tag--info {
  background-color: #f4f4f5 !important;
  border-color: #909399 !important;
  color: #909399 !important;
}

/* 基础样式 */
.ip-management {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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

.stats-section {
  margin-bottom: 24px;
}

.stats-card {
  text-align: center;
  transition: all 0.3s ease;
}

.stats-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stats-item {
  padding: 20px;
}

.stats-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stats-label {
  font-size: 14px;
  color: #909399;
}

.table-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.search-status {
  margin-bottom: 16px;
}

.pagination-section {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.selected-ips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  min-height: 32px;
  align-items: center;
}

.no-selection {
  color: #c0c4cc;
  font-style: italic;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 表格响应式样式 */
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
  min-width: 1200px;
}

/* 强制表格自适应宽度 */
.ip-management :deep(.el-table) {
  width: 100% !important;
  table-layout: auto !important;
}

.ip-management :deep(.el-table__body-wrapper),
.ip-management :deep(.el-table__header-wrapper),
.ip-management :deep(.el-table__footer-wrapper) {
  width: 100% !important;
  overflow-x: auto !important;
}

.ip-management :deep(.el-table__body),
.ip-management :deep(.el-table__header),
.ip-management :deep(.el-table__footer) {
  width: 100% !important;
  table-layout: auto !important;
}

/* 表格列宽度分配 - 有选择列的情况 */
.ip-management :deep(.el-table th:nth-child(1)) { /* 选择列 */
  width: 50px !important;
}

.ip-management :deep(.el-table th:nth-child(2)) { /* IP地址 */
  width: 12% !important;
}

.ip-management :deep(.el-table th:nth-child(3)) { /* 状态 */
  width: 8% !important;
}

.ip-management :deep(.el-table th:nth-child(4)) { /* 使用人 */
  width: 10% !important;
}

.ip-management :deep(.el-table th:nth-child(5)) { /* MAC地址 */
  width: 15% !important;
}

.ip-management :deep(.el-table th:nth-child(6)) { /* 设备类型 */
  width: 10% !important;
}

.ip-management :deep(.el-table th:nth-child(7)) { /* 所属部门 */
  width: 10% !important;
}

.ip-management :deep(.el-table th:nth-child(8)) { /* 描述 */
  width: 15% !important;
}

.ip-management :deep(.el-table th:nth-child(9)) { /* 分配时间 */
  width: 15% !important;
}

.ip-management :deep(.el-table th:nth-child(10)) { /* 操作 */
  width: 240px !important;
}

/* 只读模式下没有选择列的宽度分配 */
.readonly-table :deep(.el-table th:nth-child(1)) { /* IP地址 */
  width: 13% !important;
}

.readonly-table :deep(.el-table th:nth-child(2)) { /* 状态 */
  width: 9% !important;
}

.readonly-table :deep(.el-table th:nth-child(3)) { /* 使用人 */
  width: 11% !important;
}

.readonly-table :deep(.el-table th:nth-child(4)) { /* MAC地址 */
  width: 16% !important;
}

.readonly-table :deep(.el-table th:nth-child(5)) { /* 设备类型 */
  width: 11% !important;
}

.readonly-table :deep(.el-table th:nth-child(6)) { /* 所属部门 */
  width: 11% !important;
}

.readonly-table :deep(.el-table th:nth-child(7)) { /* 描述 */
  width: 16% !important;
}

.readonly-table :deep(.el-table th:nth-child(8)) { /* 分配时间 */
  width: 13% !important;
}

/* 对应的td列也设置相同宽度 */
.ip-management :deep(.el-table td:nth-child(1)) { width: 50px !important; }
.ip-management :deep(.el-table td:nth-child(2)) { width: 12% !important; }
.ip-management :deep(.el-table td:nth-child(3)) { width: 8% !important; }
.ip-management :deep(.el-table td:nth-child(4)) { width: 10% !important; }
.ip-management :deep(.el-table td:nth-child(5)) { width: 15% !important; }
.ip-management :deep(.el-table td:nth-child(6)) { width: 10% !important; }
.ip-management :deep(.el-table td:nth-child(7)) { width: 10% !important; }
.ip-management :deep(.el-table td:nth-child(8)) { width: 15% !important; }
.ip-management :deep(.el-table td:nth-child(9)) { width: 15% !important; }
.ip-management :deep(.el-table td:nth-child(10)) { width: 240px !important; }

/* 只读模式td宽度 */
.readonly-table :deep(.el-table td:nth-child(1)) { width: 13% !important; }
.readonly-table :deep(.el-table td:nth-child(2)) { width: 9% !important; }
.readonly-table :deep(.el-table td:nth-child(3)) { width: 11% !important; }
.readonly-table :deep(.el-table td:nth-child(4)) { width: 16% !important; }
.readonly-table :deep(.el-table td:nth-child(5)) { width: 11% !important; }
.readonly-table :deep(.el-table td:nth-child(6)) { width: 11% !important; }
.readonly-table :deep(.el-table td:nth-child(7)) { width: 16% !important; }
.readonly-table :deep(.el-table td:nth-child(8)) { width: 13% !important; }

/* 确保表格内容不会溢出 */
.ip-management :deep(.el-table .cell) {
  word-break: break-word;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 8px 12px;
}

/* 描述列允许换行 */
.ip-management :deep(.el-table td:nth-child(8) .cell) {
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
}

.readonly-table :deep(.el-table td:nth-child(7) .cell) {
  white-space: normal;
  word-break: break-word;
  line-height: 1.4;
}

/* 最简单有效的表格居中样式 */
.ip-management :deep(.el-table td),
.ip-management :deep(.el-table th) {
  text-align: center !important;
}

.ip-management :deep(.el-table .cell) {
  text-align: center !important;
  justify-content: center !important;
  display: flex !important;
  align-items: center !important;
}

/* 额外的强制居中样式 - 覆盖所有可能的冲突 */
.ip-management :deep(.el-table td > *),
.ip-management :deep(.el-table th > *) {
  text-align: center !important;
  justify-content: center !important;
}

.ip-management :deep(.el-table .el-tag) {
  margin: 0 auto !important;
}

.ip-management :deep(.el-table .action-buttons) {
  justify-content: center !important;
  display: flex !important;
}

/* 修复cell内容居中问题 */
.ip-management :deep(.el-table .cell) {
  width: auto !important;
}

/* 排序图标居中对齐 */
.ip-management :deep(.el-table .caret-wrapper) {
  display: flex !important;
  flex-direction: column !important;
  align-items: center !important;
  justify-content: center !important;
  margin-left: 4px !important;
}

.ip-management :deep(.el-table .sort-caret) {
  margin: 0 !important;
}

.ip-management :deep(.el-table th .cell) {
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
  .ip-management {
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
  .ip-management {
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
  .ip-management {
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

/* 只读用户搜索框样式 */
.readonly-search-section {
  margin-bottom: 20px;
  padding: 20px;
  background-color: var(--bg-primary, #ffffff);
  border: 1px solid var(--border-primary, #e4e7ed);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.readonly-search-container {
  display: flex;
  justify-content: center;
  align-items: center;
}

.readonly-search-input {
  max-width: 600px;
  width: 100%;
}

.readonly-search-input .el-input__inner {
  font-size: 16px;
  padding: 12px 15px;
}

@media (max-width: 768px) {
  .readonly-search-section {
    padding: 16px;
  }
  
  .readonly-search-input {
    max-width: 100%;
  }
}

/* 只读用户搜索提示样式 */
.readonly-search-hint {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 40px 20px;
  background-color: var(--bg-primary, #ffffff);
  border: 1px solid var(--border-primary, #e4e7ed);
  border-radius: 8px;
  margin-bottom: 20px;
}

.search-hint-content {
  text-align: center;
  color: var(--text-secondary, #606266);
}

.search-hint-icon {
  font-size: 48px;
  color: var(--color-primary, #409eff);
  margin-bottom: 16px;
}

.search-hint-content h3 {
  font-size: 18px;
  font-weight: 500;
  margin: 16px 0 8px 0;
  color: var(--text-primary, #303133);
}

.search-hint-content p {
  font-size: 14px;
  margin: 0;
  color: var(--text-tertiary, #909399);
}

/* 只读用户搜索结果提示样式 */
.readonly-search-result {
  margin-bottom: 16px;
}

@media (max-width: 768px) {
  .readonly-search-hint {
    min-height: 200px;
    padding: 30px 16px;
  }
  
  .search-hint-icon {
    font-size: 36px;
  }
  
  .search-hint-content h3 {
    font-size: 16px;
  }
  
  .search-hint-content p {
    font-size: 13px;
  }
}
</style>
