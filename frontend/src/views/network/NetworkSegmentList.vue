<template>
  <div class="network-segment-list">
    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="网段名称">
          <el-input
            v-model="searchForm.search"
            placeholder="请输入网段名称或网络地址"
            clearable
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
            新增网段
          </el-button>
          <el-button type="success" @click="handleBatchOperation">
            <el-icon><Setting /></el-icon>
            批量操作
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
        
        <el-table-column prop="name" label="网段名称" width="150" />

        <el-table-column prop="network" label="网络地址" width="140">
          <template #default="{ row }">
            <el-tag type="info">{{ row.network }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="IP范围" width="200">
          <template #default="{ row }">
            <div>{{ row.start_ip }} - {{ row.end_ip }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="subnet_mask" label="子网掩码" width="140" />
        
        <el-table-column prop="gateway" label="网关" width="140">
          <template #default="{ row }">
            <span v-if="row.gateway">{{ row.gateway }}</span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="vlan_id" label="VLAN ID" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.vlan_id" size="small">{{ row.vlan_id }}</el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column label="负责人" width="120">
          <template #default="{ row }">
            <div v-if="row.responsible_user">
              {{ row.responsible_user.real_name }}
            </div>
            <span v-else class="text-muted">未指定</span>
          </template>
        </el-table-column>

        <el-table-column label="负责部门" width="120">
          <template #default="{ row }">
            <div v-if="row.responsible_department">
              {{ row.responsible_department.name }}
            </div>
            <span v-else class="text-muted">未指定</span>
          </template>
        </el-table-column>

        <el-table-column prop="purpose" label="用途" min-width="120" show-overflow-tooltip />

        <el-table-column prop="location" label="位置" min-width="100" show-overflow-tooltip />

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

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleViewIPs(row)"
            >
              查看IP
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="handleViewStats(row)"
            >
              统计
            </el-button>
            <el-button
              type="warning"
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
                  <el-dropdown-item :command="row.is_active ? 'disable' : 'enable'">
                    {{ row.is_active ? '禁用' : '启用' }}
                  </el-dropdown-item>
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

    <!-- 新增/编辑网段对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑网段' : '新增网段'"
      width="800px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="网段名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入网段名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="网络地址" prop="network">
              <el-input v-model="form.network" placeholder="如: 192.168.1.0/24" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="起始IP" prop="start_ip">
              <el-input v-model="form.start_ip" placeholder="如: 192.168.1.1" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束IP" prop="end_ip">
              <el-input v-model="form.end_ip" placeholder="如: 192.168.1.254" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="子网掩码" prop="subnet_mask">
              <el-input v-model="form.subnet_mask" placeholder="如: 255.255.255.0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="网关地址">
              <el-input v-model="form.gateway" placeholder="如: 192.168.1.1" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="VLAN ID">
              <el-input-number v-model="form.vlan_id" :min="1" :max="4094" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负责部门">
              <el-select v-model="form.responsible_department_id" placeholder="请选择负责部门" style="width: 100%">
                <el-option
                  v-for="dept in departments"
                  :key="dept.id"
                  :label="dept.name"
                  :value="dept.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="负责人">
              <el-select
                v-model="form.responsible_user_id"
                placeholder="请选择负责人"
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
          </el-col>
          <el-col :span="12">
            <el-form-item label="物理位置">
              <el-input v-model="form.location" placeholder="请输入物理位置" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="DNS服务器">
          <el-select
            v-model="form.dns_servers"
            multiple
            filterable
            allow-create
            placeholder="请输入DNS服务器地址"
            style="width: 100%"
          >
            <el-option value="8.8.8.8" />
            <el-option value="8.8.4.4" />
            <el-option value="114.114.114.114" />
            <el-option value="223.5.5.5" />
          </el-select>
        </el-form-item>

        <el-form-item label="用途说明">
          <el-input
            v-model="form.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入用途说明"
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

    <!-- 网段统计对话框 -->
    <el-dialog
      v-model="statsDialogVisible"
      title="网段统计信息"
      width="600px"
    >
      <div v-if="currentSegmentStats" class="stats-container">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">IP地址总数</div>
              <div class="stat-value">{{ currentSegmentStats.total_ips }}</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">利用率</div>
              <div class="stat-value">{{ currentSegmentStats.utilization_rate }}%</div>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="6">
            <div class="stat-item success">
              <div class="stat-label">可用</div>
              <div class="stat-value">{{ currentSegmentStats.available_ips }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item warning">
              <div class="stat-label">已分配</div>
              <div class="stat-value">{{ currentSegmentStats.allocated_ips }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item danger">
              <div class="stat-label">保留</div>
              <div class="stat-value">{{ currentSegmentStats.reserved_ips }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item info">
              <div class="stat-label">黑名单</div>
              <div class="stat-value">{{ currentSegmentStats.blacklisted_ips }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Setting,
  Download,
  ArrowDown
} from '@element-plus/icons-vue'
import { networkSegmentApi } from '@/api/networkSegment'
import { departmentApi } from '@/api/department'
import { userApi } from '@/api/user'
import type { NetworkSegment, NetworkSegmentCreate, NetworkSegmentUpdate, NetworkSegmentStats, Department, User } from '@/types'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const tableData = ref<NetworkSegment[]>([])
const departments = ref<Department[]>([])
const users = ref<User[]>([])
const selectedRows = ref<NetworkSegment[]>([])

// 搜索表单
const searchForm = reactive({
  search: '',
  is_active: undefined as boolean | undefined
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
const form = reactive<NetworkSegmentCreate>({
  name: '',
  network: '',
  start_ip: '',
  end_ip: '',
  subnet_mask: '',
  gateway: '',
  dns_servers: [],
  vlan_id: undefined,
  purpose: '',
  location: '',
  responsible_department_id: undefined,
  responsible_user_id: undefined,
  is_active: true
})

const formRules = {
  name: [
    { required: true, message: '请输入网段名称', trigger: 'blur' },
    { min: 2, max: 100, message: '网段名称长度应在2-100个字符之间', trigger: 'blur' }
  ],
  network: [
    { required: true, message: '请输入网络地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/, message: '网络地址格式不正确，应为如：192.168.1.0/24', trigger: 'blur' }
  ],
  start_ip: [
    { required: true, message: '请输入起始IP', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  end_ip: [
    { required: true, message: '请输入结束IP', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  subnet_mask: [
    { required: true, message: '请输入子网掩码', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '子网掩码格式不正确', trigger: 'blur' }
  ],
  gateway: [
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: '网关地址格式不正确', trigger: 'blur' }
  ],
  vlan_id: [
    { type: 'number', min: 1, max: 4094, message: 'VLAN ID必须在1-4094之间', trigger: 'blur' }
  ]
}

// 统计对话框
const statsDialogVisible = ref(false)
const currentSegmentStats = ref<NetworkSegmentStats>()
const currentEditRow = ref<NetworkSegment>()

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
    
    // 清空空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === undefined) {
        delete params[key]
      }
    })

    const response = await networkSegmentApi.getList(params)
    // 处理分页响应
    if (response.items && Array.isArray(response.items)) {
      tableData.value = response.items
      pagination.total = response.total || 0
    } else {
      // 兼容旧的响应格式（如果后端返回的是数组）
      tableData.value = Array.isArray(response) ? response : []
      pagination.total = 0
    }
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
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
    is_active: undefined
  })
  handleSearch()
}

const handleAdd = () => {
  isEdit.value = false
  resetForm()
  formDialogVisible.value = true
}

const handleEdit = (row: NetworkSegment) => {
  isEdit.value = true
  currentEditRow.value = row
  
  // 填充表单数据
  Object.assign(form, {
    name: row.name,
    network: row.network,
    start_ip: row.start_ip,
    end_ip: row.end_ip,
    subnet_mask: row.subnet_mask,
    gateway: row.gateway || '',
    dns_servers: row.dns_servers || [],
    vlan_id: row.vlan_id,
    purpose: row.purpose || '',
    location: row.location || '',
    responsible_department_id: row.responsible_department_id,
    responsible_user_id: row.responsible_user_id,
    is_active: row.is_active
  })
  
  // 加载负责人信息
  if (row.responsible_user) {
    users.value = [row.responsible_user]
  }
  
  formDialogVisible.value = true
}

const handleFormSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 处理DNS服务器字段，确保它是一个数组或undefined
    const formData = { ...form }
    if (formData.dns_servers && Array.isArray(formData.dns_servers) && formData.dns_servers.length === 0) {
      // 如果DNS服务器数组为空，将其设置为undefined，这样后端就不会验证它
      formData.dns_servers = undefined
    }
    
    if (isEdit.value && currentEditRow.value) {
      await networkSegmentApi.update(currentEditRow.value.id, formData)
      ElMessage.success('网段更新成功')
    } else {
      await networkSegmentApi.create(formData)
      ElMessage.success('网段创建成功')
    }
    
    formDialogVisible.value = false
    loadData()
  } catch (error: any) {
    console.error('保存网段失败:', error)
    // 错误消息已由request拦截器处理，这里不需要再次显示
  }
}

const handleViewIPs = (row: NetworkSegment) => {
  router.push({
    path: '/ip-management/addresses',
    query: { network_segment_id: row.id }
  })
}

const handleViewStats = async (row: NetworkSegment) => {
  try {
    const stats = await networkSegmentApi.getStatistics(row.id)
    currentSegmentStats.value = stats
    statsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取统计信息失败')
    console.error(error)
  }
}

const handleBatchOperation = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要操作的网段')
    return
  }
  ElMessage.info('批量操作功能开发中...')
}

const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

const handleSelectionChange = (selection: NetworkSegment[]) => {
  selectedRows.value = selection
}

const handleDropdownCommand = async (command: string, row: NetworkSegment) => {
  switch (command) {
    case 'enable':
    case 'disable':
      await handleToggleStatus(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

const handleToggleStatus = async (row: NetworkSegment) => {
  try {
    const action = row.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}网段 ${row.name} 吗？`,
      `确认${action}`,
      { type: 'warning' }
    )
    
    await networkSegmentApi.update(row.id, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换网段状态失败:', error)
    }
  }
}

const handleDelete = async (row: NetworkSegment) => {
  try {
    // 先检查网段中是否有IP地址
    const stats = await networkSegmentApi.getStatistics(row.id)
    
    if (stats.total_ips > 0) {
      ElMessageBox.alert(
        `无法删除网段 ${row.name}，因为该网段中存在 ${stats.total_ips} 个IP地址。请先删除所有IP地址后再尝试删除网段。`,
        '无法删除网段',
        { type: 'error' }
      )
      return
    }
    
    // 如果没有IP地址，则可以继续删除流程
    await ElMessageBox.confirm(
      `确定要删除网段 ${row.name} 吗？此操作不可恢复！`,
      '确认删除',
      { type: 'warning' }
    )
    
    await networkSegmentApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除网段失败:', error)
    }
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    network: '',
    start_ip: '',
    end_ip: '',
    subnet_mask: '',
    gateway: '',
    dns_servers: [],
    vlan_id: undefined,
    purpose: '',
    location: '',
    responsible_department_id: undefined,
    responsible_user_id: undefined,
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
  loadDepartments()
})
</script>

<style scoped>
.network-segment-list {
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

.stat-item.success {
  border-color: #67c23a;
  background-color: #f0f9ff;
}

.stat-item.warning {
  border-color: #e6a23c;
  background-color: #fdf6ec;
}

.stat-item.danger {
  border-color: #f56c6c;
  background-color: #fef0f0;
}

.stat-item.info {
  border-color: #909399;
  background-color: #f4f4f5;
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
  }
}
</style>