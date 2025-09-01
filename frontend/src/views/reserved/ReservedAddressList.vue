<template>
  <div class="reserved-address-list">
    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="IP地址">
          <el-input
            v-model="searchForm.search"
            placeholder="请输入IP地址或保留用途"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="网段">
          <el-select
            v-model="searchForm.network_segment_id"
            placeholder="请选择网段"
            clearable
            style="width: 200px"
          >
            <el-option
              v-for="segment in networkSegments"
              :key="segment.id"
              :label="`${segment.name} (${segment.network})`"
              :value="segment.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select
            v-model="searchForm.is_active"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="生效" :value="true" />
            <el-option label="失效" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="保留人">
          <el-select
            v-model="searchForm.reserved_by_user_id"
            placeholder="请选择保留人"
            clearable
            filterable
            remote
            :remote-method="searchUsers"
            style="width: 150px"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.real_name"
              :value="user.id"
            />
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
            新增保留
          </el-button>
          <el-button type="warning" @click="handleCleanupExpired">
            <el-icon><Delete /></el-icon>
            清理过期
          </el-button>
          <el-button type="info" @click="handleViewExpiring">
            <el-icon><Clock /></el-icon>
            即将过期
          </el-button>
          <el-button type="success" @click="handleExport">
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
        
        <el-table-column prop="ip_address" label="IP地址" width="140">
          <template #default="{ row }">
            <el-tag>{{ row.ip_address }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="reserved_for" label="保留用途" min-width="150" show-overflow-tooltip />

        <el-table-column label="保留人" width="120">
          <template #default="{ row }">
            {{ row.reserved_by_user?.real_name }}
          </template>
        </el-table-column>

        <el-table-column label="保留部门" width="120">
          <template #default="{ row }">
            <span v-if="row.reserved_by_department">
              {{ row.reserved_by_department.name }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_date" label="开始日期" width="120" />

        <el-table-column prop="end_date" label="结束日期" width="120">
          <template #default="{ row }">
            <span v-if="row.is_permanent" class="permanent-tag">
              <el-tag type="success" size="small">永久</el-tag>
            </span>
            <span v-else-if="row.end_date">{{ row.end_date }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="剩余天数" width="100">
          <template #default="{ row }">
            <span v-if="row.is_permanent" class="text-success">永久</span>
            <span v-else-if="row.end_date">
              <span :class="getDaysLeftClass(getDaysLeft(row.end_date))">
                {{ getDaysLeft(row.end_date) }}天
              </span>
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="network_segment" label="所属网段" width="120">
          <template #default="{ row }">
            {{ row.network_segment?.name }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '生效' : '失效' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="notes" label="备注" min-width="120" show-overflow-tooltip />

        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_active"
              type="success"
              size="small"
              @click="handleActivate(row)"
            >
              激活
            </el-button>
            <el-button
              v-if="row.is_active"
              type="warning"
              size="small"
              @click="handleDeactivate(row)"
            >
              停用
            </el-button>
            <el-button
              v-if="!row.is_permanent && row.end_date"
              type="primary"
              size="small"
              @click="handleExtend(row)"
            >
              延期
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
              <el-button size="small">
                更多<el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
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

    <!-- 新增/编辑保留对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑地址保留' : '新增地址保留'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
        </el-form-item>

        <el-form-item label="所属网段" prop="network_segment_id">
          <el-select v-model="form.network_segment_id" placeholder="请选择网段" style="width: 100%">
            <el-option
              v-for="segment in networkSegments"
              :key="segment.id"
              :label="`${segment.name} (${segment.network})`"
              :value="segment.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="保留用途" prop="reserved_for">
          <el-input v-model="form.reserved_for" placeholder="请输入保留用途" />
        </el-form-item>

        <el-form-item label="保留人" prop="reserved_by_user_id">
          <el-select
            v-model="form.reserved_by_user_id"
            placeholder="请选择保留人"
            filterable
            remote
            :remote-method="searchUsers"
            style="width: 100%"
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="`${user.real_name} (${user.username})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="保留部门">
          <el-select v-model="form.reserved_by_department_id" placeholder="请选择保留部门" style="width: 100%">
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期" prop="start_date">
              <el-date-picker
                v-model="form.start_date"
                type="date"
                placeholder="选择开始日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="form.end_date"
                type="date"
                placeholder="选择结束日期"
                :disabled="form.is_permanent"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="优先级">
              <el-select v-model="form.priority" placeholder="请选择优先级" style="width: 100%">
                <el-option label="低" value="low" />
                <el-option label="中" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="紧急" value="critical" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="永久保留">
              <el-switch
                v-model="form.is_permanent"
                active-text="是"
                inactive-text="否"
                @change="handlePermanentChange"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注说明">
          <el-input
            v-model="form.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注说明"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="form.is_active"
            active-text="生效"
            inactive-text="失效"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFormSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 延期对话框 -->
    <el-dialog
      v-model="extendDialogVisible"
      title="延长保留期限"
      width="400px"
    >
      <el-form label-width="100px">
        <el-form-item label="当前IP">
          <el-input :model-value="currentExtendRow?.ip_address" disabled />
        </el-form-item>
        <el-form-item label="当前到期日">
          <el-input :model-value="currentExtendRow?.end_date" disabled />
        </el-form-item>
        <el-form-item label="新到期日" required>
          <el-date-picker
            v-model="newEndDate"
            type="date"
            placeholder="选择新的到期日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="extendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleExtendConfirm">确认延期</el-button>
      </template>
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
  Delete,
  Clock,
  Download,
  ArrowDown
} from '@element-plus/icons-vue'
import { reservedAddressApi } from '@/api/reservedAddress'
import { networkSegmentApi } from '@/api/networkSegment'
import { departmentApi } from '@/api/department'
import { userApi } from '@/api/user'
import type { ReservedAddress, ReservedAddressCreate, NetworkSegment, Department, User, Priority } from '@/types'

// 响应式数据
const loading = ref(false)
const tableData = ref<ReservedAddress[]>([])
const networkSegments = ref<NetworkSegment[]>([])
const departments = ref<Department[]>([])
const users = ref<User[]>([])
const selectedRows = ref<ReservedAddress[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  network_segment_id: undefined as number | undefined,
  is_active: undefined as boolean | undefined,
  reserved_by_user_id: undefined as number | undefined
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
const form = reactive<ReservedAddressCreate>({
  ip_address: '',
  network_segment_id: 0,
  reserved_for: '',
  reserved_by_user_id: 0,
  reserved_by_department_id: undefined,
  start_date: new Date().toISOString().split('T')[0],
  end_date: undefined,
  is_permanent: false,
  priority: 'medium',
  notes: '',
  is_active: true
})

const formRules = {
  ip_address: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  network_segment_id: [
    { required: true, message: '请选择网段', trigger: 'change' }
  ],
  reserved_for: [
    { required: true, message: '请输入保留用途', trigger: 'blur' },
    { max: 200, message: '保留用途最长200个字符', trigger: 'blur' }
  ],
  reserved_by_user_id: [
    { required: true, message: '请选择保留人', trigger: 'change' }
  ],
  start_date: [
    { required: true, message: '请选择开始日期', trigger: 'change' },
    { 
      validator: (rule, value, callback) => {
        if (value && form.end_date && !form.is_permanent && new Date(value) > new Date(form.end_date)) {
          callback(new Error('开始日期不能晚于结束日期'));
        } else {
          callback();
        }
      }, 
      trigger: 'change' 
    }
  ],
  end_date: [
    { 
      validator: (rule, value, callback) => {
        if (value && !form.is_permanent && new Date(value) < new Date()) {
          callback(new Error('结束日期不能早于当前日期'));
        } else {
          callback();
        }
      }, 
      trigger: 'change' 
    }
  ],
  notes: [
    { max: 500, message: '备注最长500个字符', trigger: 'blur' }
  ]
}

// 延期对话框
const extendDialogVisible = ref(false)
const currentExtendRow = ref<ReservedAddress>()
const newEndDate = ref('')
const currentEditRow = ref<ReservedAddress>()

// 方法
const getPriorityType = (priority: Priority) => {
  const priorityMap = {
    low: 'info',
    medium: 'success',
    high: 'warning',
    critical: 'danger'
  }
  return priorityMap[priority] || 'info'
}

const getPriorityText = (priority: Priority) => {
  const priorityMap = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '紧急'
  }
  return priorityMap[priority] || priority
}

const getDaysLeft = (endDate: string): number => {
  const today = new Date()
  const end = new Date(endDate)
  const diffTime = end.getTime() - today.getTime()
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

const getDaysLeftClass = (days: number): string => {
  if (days < 0) return 'text-danger'
  if (days <= 7) return 'text-warning'
  if (days <= 30) return 'text-info'
  return 'text-success'
}

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
    
    // 清空空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })

    const data = await reservedAddressApi.getList(params)
    tableData.value = data
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const loadNetworkSegments = async () => {
  try {
    const data = await networkSegmentApi.getList({ limit: 1000 })
    networkSegments.value = data.items || []
  } catch (error) {
    console.error('加载网段列表失败:', error)
  }
}

const loadDepartments = async () => {
  try {
    const data = await departmentApi.getList({ limit: 1000 })
    departments.value = data
  } catch (error) {
    console.error('加载部门列表失败:', error)
  }
}

const searchUsers = async (query: string) => {
  if (!query) {
    users.value = []
    return
  }
  
  try {
    const data = await userApi.search({ q: query, limit: 20 })
    users.value = data
  } catch (error) {
    console.error('搜索用户失败:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    search: '',
    network_segment_id: undefined,
    is_active: undefined,
    reserved_by_user_id: undefined
  })
  handleSearch()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  formDialogVisible.value = true
}

const handleEdit = (row: ReservedAddress) => {
  isEdit.value = true
  currentEditRow.value = row
  
  // 填充表单数据
  Object.assign(form, {
    ip_address: row.ip_address,
    network_segment_id: row.network_segment_id,
    reserved_for: row.reserved_for,
    reserved_by_user_id: row.reserved_by_user_id,
    reserved_by_department_id: row.reserved_by_department_id,
    start_date: row.start_date,
    end_date: row.end_date,
    is_permanent: row.is_permanent,
    priority: row.priority,
    notes: row.notes || '',
    is_active: row.is_active
  })
  
  // 加载保留人信息
  if (row.reserved_by_user) {
    users.value = [row.reserved_by_user]
  }
  
  formDialogVisible.value = true
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
    
    if (isEdit.value && currentEditRow.value) {
      await reservedAddressApi.update(currentEditRow.value.id, formData)
      ElMessage.success('地址保留更新成功')
    } else {
      await reservedAddressApi.create(formData)
      ElMessage.success('地址保留创建成功')
    }
    
    formDialogVisible.value = false
    loadData()
  } catch (error: any) {
    console.error('保存地址保留失败:', error)
    // 错误消息已由request拦截器处理，这里不需要再次显示
  }
}

const handleActivate = async (row: ReservedAddress) => {
  try {
    await reservedAddressApi.activate(row.id)
    ElMessage.success('激活成功')
    loadData()
  } catch (error) {
    console.error('激活失败:', error)
  }
}

const handleDeactivate = async (row: ReservedAddress) => {
  try {
    await ElMessageBox.confirm(
      `确定要停用地址保留 ${row.ip_address} 吗？`,
      '确认停用',
      { type: 'warning' }
    )
    
    await reservedAddressApi.deactivate(row.id)
    ElMessage.success('停用成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停用失败:', error)
    }
  }
}

const handleExtend = (row: ReservedAddress) => {
  currentExtendRow.value = row
  newEndDate.value = ''
  extendDialogVisible.value = true
}

const handleExtendConfirm = async () => {
  if (!newEndDate.value || !currentExtendRow.value) {
    ElMessage.warning('请选择新的到期日期')
    return
  }
  
  try {
    await reservedAddressApi.extend(currentExtendRow.value.id, newEndDate.value)
    ElMessage.success('延期成功')
    extendDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('延期失败:', error)
  }
}

const handleCleanupExpired = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清理所有过期的地址保留吗？',
      '确认清理',
      { type: 'warning' }
    )
    
    const result = await reservedAddressApi.cleanupExpired()
    ElMessage.success(result.message)
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清理过期保留失败:', error)
    }
  }
}

const handleViewExpiring = async () => {
  try {
    const data = await reservedAddressApi.getUpcomingExpiration(7)
    if (data.length === 0) {
      ElMessage.info('没有即将过期的地址保留')
    } else {
      ElMessage.info(`有 ${data.length} 个地址保留即将在7天内过期`)
      // 这里可以显示详细列表或筛选表格
      searchForm.search = ''
      // 可以添加额外的筛选逻辑来显示即将过期的记录
      loadData()
    }
  } catch (error) {
    console.error('获取即将过期的保留失败:', error)
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

const handleSelectionChange = (selection: ReservedAddress[]) => {
  selectedRows.value = selection
}

const handleDropdownCommand = async (command: string, row: ReservedAddress) => {
  switch (command) {
    case 'delete':
      await handleDelete(row)
      break
  }
}

const handleDelete = async (row: ReservedAddress) => {
  try {
    // 检查是否为永久保留
    if (row.is_permanent) {
      await ElMessageBox.confirm(
        `地址 ${row.ip_address} 设置为永久保留，确定要删除吗？`,
        '确认删除永久保留地址',
        { type: 'warning' }
      )
    } else {
      await ElMessageBox.confirm(
        `确定要删除地址保留 ${row.ip_address} 吗？此操作不可恢复！`,
        '确认删除',
        { type: 'warning' }
      )
    }
    
    await reservedAddressApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除地址保留失败:', error)
    }
  }
}

const handlePermanentChange = (value: boolean) => {
  if (value) {
    form.end_date = undefined
  }
}

const resetForm = () => {
  Object.assign(form, {
    ip_address: '',
    network_segment_id: 0,
    reserved_for: '',
    reserved_by_user_id: 0,
    reserved_by_department_id: undefined,
    start_date: new Date().toISOString().split('T')[0],
    end_date: undefined,
    is_permanent: false,
    priority: 'medium',
    notes: '',
    is_active: true
  })
  users.value = []
}

const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadData()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadData()
}

// 生命周期
onMounted(() => {
  loadData()
  loadNetworkSegments()
  loadDepartments()
})
</script>

<style scoped>
.reserved-address-list {
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

.text-success {
  color: #67c23a;
}

.text-info {
  color: #409eff;
}

.text-warning {
  color: #e6a23c;
}

.text-danger {
  color: #f56c6c;
}

.permanent-tag {
  display: inline-block;
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