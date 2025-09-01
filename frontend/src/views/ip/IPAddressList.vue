<template>
  <div class="ip-address-list">
    <!-- 搜索表单 -->
    <el-card class="search-card">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="IP地址">
          <el-input
            v-model="searchForm.search"
            placeholder="请输入IP地址、设备名或主机名"
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
            v-model="searchForm.status"
            placeholder="请选择状态"
            clearable
            style="width: 120px"
          >
            <el-option label="可用" value="available" />
            <el-option label="已分配" value="allocated" />
            <el-option label="保留" value="reserved" />
            <el-option label="黑名单" value="blacklisted" />
          </el-select>
        </el-form-item>
        <el-form-item label="分配用户">
          <el-select
            v-model="searchForm.assigned_user_id"
            placeholder="请选择用户"
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
          <!-- 屏蔽添加IP地址和批量分配功能 -->
          <!--
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            添加IP地址
          </el-button>
          <el-button type="success" @click="handleBatchAllocate">
            <el-icon><Connection /></el-icon>
            批量分配
          </el-button>
          -->
          <el-dropdown @command="handleBatchCommand" :disabled="selectedRows.length === 0">
            <el-button type="warning">
              批量操作<el-icon><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="selectAll">全选</el-dropdown-item>
                <el-dropdown-item command="unselectAll">取消选择</el-dropdown-item>
                <el-dropdown-item command="batchDelete" divided>批量删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
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
        
        <el-table-column prop="ip_address" label="IP地址" width="140">
          <template #default="{ row }">
            <el-tag>{{ row.ip_address }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="device_name" label="设备名称" width="120" />
        
        <el-table-column prop="hostname" label="主机名" width="120" />
        
        <el-table-column prop="mac_address" label="MAC地址" width="140">
          <template #default="{ row }">
            <code v-if="row.mac_address">{{ row.mac_address }}</code>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column label="分配信息" min-width="150">
          <template #default="{ row }">
            <div v-if="row.assigned_user">
              <div>{{ row.assigned_user.real_name }}</div>
              <div class="text-muted small">{{ row.assigned_department?.name }}</div>
            </div>
            <span v-else class="text-muted">未分配</span>
          </template>
        </el-table-column>

        <el-table-column prop="network_segment" label="所属网段" min-width="120">
          <template #default="{ row }">
            {{ row.network_segment?.name }}
          </template>
        </el-table-column>

        <el-table-column prop="purpose" label="用途" min-width="120" show-overflow-tooltip />

        <el-table-column prop="allocated_at" label="分配时间" width="150">
          <template #default="{ row }">
            <span v-if="row.allocated_at">
              {{ formatDate(row.allocated_at) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'available'"
              type="primary"
              size="small"
              @click="handleAllocate(row)"
            >
              分配
            </el-button>
            <el-button
              v-if="row.status === 'allocated'"
              type="warning"
              size="small"
              @click="handleRelease(row)"
            >
              释放
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <!-- 更多按钮（使用历史、删除）已屏蔽 -->
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
          :pager-count="7"
          layout="total, sizes, prev, pager, next, jumper"
          background
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- IP分配对话框 -->
    <el-dialog
      v-model="allocateDialogVisible"
      title="分配IP地址"
      width="600px"
    >
      <el-form
        ref="allocateFormRef"
        :model="allocateForm"
        :rules="allocateRules"
        label-width="100px"
      >
        <el-form-item label="IP地址">
          <el-input :model-value="currentRow?.ip_address" disabled />
        </el-form-item>
        
        <el-form-item label="分配用户" prop="user_id">
          <el-select
            v-model="allocateForm.user_id"
            placeholder="请选择用户"
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

        <el-form-item label="设备名称" prop="device_name">
          <el-input v-model="allocateForm.device_name" placeholder="请输入设备名称" />
        </el-form-item>

        <el-form-item label="设备类型">
          <el-select v-model="allocateForm.device_type" placeholder="请选择设备类型">
            <el-option label="服务器" value="server" />
            <el-option label="工作站" value="workstation" />
            <el-option label="打印机" value="printer" />
            <el-option label="网络设备" value="network" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>

        <el-form-item label="MAC地址">
          <el-input v-model="allocateForm.mac_address" placeholder="请输入MAC地址" />
        </el-form-item>

        <el-form-item label="主机名">
          <el-input v-model="allocateForm.hostname" placeholder="请输入主机名" />
        </el-form-item>

        <el-form-item label="操作系统">
          <el-select 
            v-model="allocateForm.os_type" 
            placeholder="请选择操作系统"
            style="width: 100%"
            clearable
            filterable
          >
            <el-option
              v-for="osType in osTypes"
              :key="osType.value"
              :label="osType.label"
              :value="osType.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="用途说明">
          <el-input
            v-model="allocateForm.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入用途说明"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="allocateDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAllocateConfirm">确认分配</el-button>
      </template>
    </el-dialog>

    <!-- 编辑IP地址对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑IP地址"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
        class="edit-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="IP地址">
              <el-input :model-value="editForm.ip_address" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="网段">
              <el-select 
                v-model="editForm.network_segment_id" 
                placeholder="请选择网段"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="segment in networkSegments"
                  :key="segment.id"
                  :label="`${segment.name} (${segment.network})`"
                  :value="segment.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态">
              <el-select 
                v-model="editForm.status" 
                placeholder="请选择状态"
                style="width: 100%"
              >
                <el-option label="可用" value="available" />
                <el-option label="已分配" value="allocated" />
                <el-option label="保留" value="reserved" />
                <el-option label="黑名单" value="blacklisted" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备名称" prop="device_name">
              <el-input 
                v-model="editForm.device_name" 
                placeholder="请输入设备名称"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备类型">
              <el-select 
                v-model="editForm.device_type" 
                placeholder="请选择设备类型"
                style="width: 100%"
                clearable
              >
                <el-option label="服务器" value="server" />
                <el-option label="工作站" value="workstation" />
                <el-option label="打印机" value="printer" />
                <el-option label="网络设备" value="network" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="MAC地址" prop="mac_address">
              <el-input 
                v-model="editForm.mac_address" 
                placeholder="请输入MAC地址"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主机名" prop="hostname">
              <el-input 
                v-model="editForm.hostname" 
                placeholder="请输入主机名"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="操作系统">
              <el-select 
                v-model="editForm.os_type" 
                placeholder="请选择操作系统"
                style="width: 100%"
                clearable
                filterable
              >
                <el-option
                  v-for="osType in osTypes"
                  :key="osType.value"
                  :label="osType.label"
                  :value="osType.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="editForm.status === 'allocated'">
          <el-col :span="12">
            <el-form-item label="分配用户">
              <el-select
                v-model="editForm.assigned_user_id"
                placeholder="请选择用户"
                filterable
                remote
                :remote-method="searchUsers"
                style="width: 100%"
                clearable
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
            <el-form-item label="分配时间">
              <el-date-picker
                v-model="editForm.allocated_at"
                type="datetime"
                placeholder="选择分配时间"
                style="width: 100%"
                format="YYYY-MM-DD HH:mm:ss"
                value-format="YYYY-MM-DD HH:mm:ss"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="用途说明" prop="purpose">
          <el-input
            v-model="editForm.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入用途说明"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="editForm.notes"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleEditConfirm">确认修改</el-button>
      </template>
    </el-dialog>

    <!-- 添加IP地址对话框 -->
    <el-dialog
      v-model="addDialogVisible"
      title="添加IP地址"
      width="700px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="addFormRef"
        :model="addForm"
        :rules="addRules"
        label-width="120px"
        class="add-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="IP地址" prop="ip_address">
              <el-input 
                v-model="addForm.ip_address" 
                placeholder="请输入IP地址"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="网段" prop="network_segment_id">
              <el-select 
                v-model="addForm.network_segment_id" 
                placeholder="请选择网段"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="segment in networkSegments"
                  :key="segment.id"
                  :label="`${segment.name} (${segment.network})`"
                  :value="segment.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select 
                v-model="addForm.status" 
                placeholder="请选择状态"
                style="width: 100%"
              >
                <el-option label="可用" value="available" />
                <el-option label="已分配" value="allocated" />
                <el-option label="保留" value="reserved" />
                <el-option label="黑名单" value="blacklisted" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设备名称">
              <el-input 
                v-model="addForm.device_name" 
                placeholder="请输入设备名称"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="设备类型">
              <el-select 
                v-model="addForm.device_type" 
                placeholder="请选择设备类型"
                style="width: 100%"
                clearable
              >
                <el-option label="服务器" value="server" />
                <el-option label="工作站" value="workstation" />
                <el-option label="打印机" value="printer" />
                <el-option label="网络设备" value="network" />
                <el-option label="其他" value="other" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="MAC地址">
              <el-input 
                v-model="addForm.mac_address" 
                placeholder="请输入MAC地址"
                clearable
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="主机名">
              <el-input 
                v-model="addForm.hostname" 
                placeholder="请输入主机名"
                clearable
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="操作系统">
              <el-select 
                v-model="addForm.os_type" 
                placeholder="请选择操作系统"
                style="width: 100%"
                clearable
                filterable
              >
                <el-option
                  v-for="osType in osTypes"
                  :key="osType.value"
                  :label="osType.label"
                  :value="osType.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20" v-if="addForm.status === 'allocated'">
          <el-col :span="12">
            <el-form-item label="分配用户">
              <el-select
                v-model="addForm.assigned_user_id"
                placeholder="请选择用户"
                filterable
                remote
                :remote-method="searchUsers"
                style="width: 100%"
                clearable
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
            <el-form-item label="分配部门">
              <el-select
                v-model="addForm.assigned_department_id"
                placeholder="请选择部门"
                style="width: 100%"
                clearable
              >
                <!-- 这里需要添加部门选项，但由于没有部门数据，先留空 -->
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="用途说明">
          <el-input
            v-model="addForm.purpose"
            type="textarea"
            :rows="3"
            placeholder="请输入用途说明"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="addForm.notes"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddConfirm">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Plus,
  Connection,
  Download,
  ArrowDown
} from '@element-plus/icons-vue'
import { ipAddressApi } from '@/api/ipAddress'
import { networkSegmentApi } from '@/api/networkSegment'
import { userApi } from '@/api/user'
import type { IPAddress, NetworkSegment, User, IPStatus } from '@/types'

// 响应式数据
const loading = ref(false)
const tableData = ref<IPAddress[]>([])
const networkSegments = ref<NetworkSegment[]>([])
const users = ref<User[]>([])
const osTypes = ref<Array<{label: string, value: string}>>([])
const selectedRows = ref<IPAddress[]>([])
const isMobile = ref(false)

// 操作系统类型映射表
const osTypeEnumMap: { [key: string]: string } = {
  'Windows Server 2019': 'windows_server_2019',
  'Windows Server 2022': 'windows_server_2022',
  'Windows 10': 'windows_10',
  'Windows 11': 'windows_11',
  'Ubuntu 20.04': 'ubuntu_20_04',
  'Ubuntu 22.04': 'ubuntu_22_04',
  'CentOS 7': 'centos_7',
  'CentOS 8': 'centos_8',
  'Debian 10': 'debian_10',
  'Debian 11': 'debian_11',
  'Red Hat Enterprise Linux 8': 'redhat_8',
  'Red Hat Enterprise Linux 9': 'redhat_9',
  'SUSE Linux Enterprise 15': 'suse_15',
  'macOS Monterey': 'macos_monterey',
  'macOS Ventura': 'macos_ventura',
  'macOS Sonoma': 'macos_sonoma',
  'VMware vSphere ESXi 7': 'vmware_esxi_7',
  'VMware vSphere ESXi 8': 'vmware_esxi_8',
  '其他': 'other'
}

// 移动端列显示控制
const mobileVisibleColumns = ref({
  device_name: true,
  hostname: false,
  assigned_user: true,
  mac_address: false,
  network_segment: false,
  purpose: false,
  allocated_at: false
})

// 检测设备类型
const checkDevice = () => {
  isMobile.value = window.innerWidth <= 768
}

// 显示列控制
const showColumn = (columnName: string) => {
  return mobileVisibleColumns.value[columnName as keyof typeof mobileVisibleColumns.value]
}

// 搜索表单
const searchForm = reactive({
  search: '',
  network_segment_id: undefined as number | undefined,
  status: '' as IPStatus | '',
  assigned_user_id: undefined as number | undefined
})

// 分页数据
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 分配对话框
const allocateDialogVisible = ref(false)
const currentRow = ref<IPAddress>()
const allocateFormRef = ref()
const allocateForm = reactive({
  user_id: undefined as number | undefined,
  device_name: '',
  device_type: '',
  mac_address: '',
  hostname: '',
  os_type: '',
  purpose: ''
})

// 编辑IP对话框
const editDialogVisible = ref(false)
const editFormRef = ref()
const editForm = reactive({
  id: undefined as number | undefined,
  ip_address: '',
  network_segment_id: undefined as number | undefined,
  status: 'available' as IPStatus,
  device_name: '',
  device_type: '',
  mac_address: '',
  hostname: '',
  os_type: '',
  purpose: '',
  notes: '',
  assigned_user_id: undefined as number | undefined,
  assigned_department_id: undefined as number | undefined,
  allocated_at: ''
})

// 添加IP对话框
const addDialogVisible = ref(false)
const addFormRef = ref()
const addForm = reactive({
  ip_address: '',
  network_segment_id: undefined as number | undefined,
  status: 'available' as IPStatus,
  device_name: '',
  device_type: '',
  mac_address: '',
  hostname: '',
  os_type: '',
  purpose: '',
  notes: '',
  assigned_user_id: undefined as number | undefined,
  assigned_department_id: undefined as number | undefined
})

const addRules = {
  ip_address: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  network_segment_id: [
    { required: true, message: '请选择网段', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  mac_address: [
    { 
      pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 
      message: 'MAC地址格式不正确（如：00:1A:2B:3C:4D:5E）', 
      trigger: 'blur' 
    }
  ],
  hostname: [
    { max: 100, message: '主机名最长100个字符', trigger: 'blur' }
  ],
  device_name: [
    { max: 100, message: '设备名称最长100个字符', trigger: 'blur' }
  ]
}

const editRules = {
  ip_address: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  network_segment_id: [
    { required: true, message: '请选择网段', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ],
  mac_address: [
    { 
      pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 
      message: 'MAC地址格式不正确（如：00:1A:2B:3C:4D:5E）', 
      trigger: 'blur' 
    }
  ],
  hostname: [
    { max: 100, message: '主机名最长100个字符', trigger: 'blur' }
  ],
  device_name: [
    { max: 100, message: '设备名称最长100个字符', trigger: 'blur' }
  ],
  purpose: [
    { max: 500, message: '用途说明最长500个字符', trigger: 'blur' }
  ]
}

const allocateRules = {
  user_id: [
    { required: true, message: '请选择分配用户', trigger: 'change' }
  ],
  device_name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { max: 100, message: '设备名称最长100个字符', trigger: 'blur' }
  ],
  mac_address: [
    { 
      pattern: /^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$/, 
      message: 'MAC地址格式不正确（如：00:1A:2B:3C:4D:5E）', 
      trigger: 'blur' 
    }
  ]
}

// 方法
const getStatusType = (status: IPStatus) => {
  const statusMap = {
    available: 'success',
    allocated: 'warning',
    reserved: 'danger',
    blacklisted: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: IPStatus) => {
  const statusMap = {
    available: '可用',
    allocated: '已分配',
    reserved: '保留',
    blacklisted: '黑名单'
  }
  return statusMap[status] || status
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

    console.log('请求参数:', params)  // 添加日志以便调试

    const response = await ipAddressApi.getList(params)
    
    // 处理分页响应
    if (response.items && Array.isArray(response.items)) {
      tableData.value = response.items
      pagination.total = response.total || 0
    } else if (Array.isArray(response)) {
      // 兼容旧的响应格式（如果后端返回的是数组）
      tableData.value = response
      pagination.total = response.length
    } else {
      tableData.value = []
      pagination.total = 0
    }
    
    // 打印info级别日志
    console.info('IP地址列表数据加载完成', { params, count: tableData.value.length, total: pagination.total })
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

const loadOSTypes = async () => {
  // 直接使用硬编码的操作系统选项，确保功能立即可用
  osTypes.value = [
    {"label": "Windows Server 2019", "value": "Windows Server 2019"},
    {"label": "Windows Server 2022", "value": "Windows Server 2022"},
    {"label": "Windows 10", "value": "Windows 10"},
    {"label": "Windows 11", "value": "Windows 11"},
    {"label": "Ubuntu 20.04", "value": "Ubuntu 20.04"},
    {"label": "Ubuntu 22.04", "value": "Ubuntu 22.04"},
    {"label": "CentOS 7", "value": "CentOS 7"},
    {"label": "CentOS 8", "value": "CentOS 8"},
    {"label": "Debian 10", "value": "Debian 10"},
    {"label": "Debian 11", "value": "Debian 11"},
    {"label": "Red Hat Enterprise Linux 8", "value": "Red Hat Enterprise Linux 8"},
    {"label": "Red Hat Enterprise Linux 9", "value": "Red Hat Enterprise Linux 9"},
    {"label": "SUSE Linux Enterprise 15", "value": "SUSE Linux Enterprise 15"},
    {"label": "macOS Monterey", "value": "macOS Monterey"},
    {"label": "macOS Ventura", "value": "macOS Ventura"},
    {"label": "macOS Sonoma", "value": "macOS Sonoma"},
    {"label": "VMware vSphere ESXi 7", "value": "VMware vSphere ESXi 7"},
    {"label": "VMware vSphere ESXi 8", "value": "VMware vSphere ESXi 8"},
    {"label": "其他", "value": "其他"}
  ]
  
  // 后续可以改为从 API 获取
  // try {
  //   const data = await ipAddressApi.getOSTypes()
  //   osTypes.value = data
  // } catch (error) {
  //   console.error('加载操作系统选项失败:', error)
  //   // fallback 到硬编码选项
  // }
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
    status: '',
    assigned_user_id: undefined
  })
  handleSearch()
}

const handleAdd = () => {
  currentRow.value = null
  addDialogVisible.value = true
  
  // 重置表单
  Object.assign(addForm, {
    ip_address: '',
    network_segment_id: undefined,
    status: 'available',
    device_name: '',
    device_type: '',
    mac_address: '',
    hostname: '',
    os_type: '',
    purpose: '',
    notes: '',
    assigned_user_id: undefined,
    assigned_department_id: undefined
  })
}

const handleBatchAllocate = () => {
  // 屏蔽批量分配功能
  ElMessage.info('批量分配功能已屏蔽')
  /*
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要批量分配的IP地址')
    return
  }
  ElMessage.info('批量分配功能开发中...')
  */
}

const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

const handleSelectionChange = (selection: IPAddress[]) => {
  selectedRows.value = selection
}

const handleAllocate = (row: IPAddress) => {
  currentRow.value = row
  allocateDialogVisible.value = true
  
  // 使用当前行数据初始化表单，确保与前端展示一致
  Object.assign(allocateForm, {
    user_id: row.assigned_user?.id,
    device_name: row.device_name || '',
    device_type: row.device_type || '',
    mac_address: row.mac_address || '',
    hostname: row.hostname || '',
    os_type: row.os_type || '',
    purpose: row.purpose || ''
  })
  
  // 如果有分配用户，加载用户信息到下拉框
  if (row.assigned_user) {
    users.value = [row.assigned_user]
  }
}

const handleAllocateConfirm = async () => {
  if (!allocateFormRef.value) return
  
  try {
    await allocateFormRef.value.validate()
    
    if (!currentRow.value) return
    
    // 创建表单数据副本用于处理
    const allocateData = {...allocateForm}
    
    // 转换os_type值
    if (allocateData.os_type) {
      allocateData.os_type = osTypeEnumMap[allocateData.os_type] || allocateData.os_type
    }
    
    // 确保非必填字段在为空时设置为undefined而不是空字符串
    Object.keys(allocateData).forEach(key => {
      if (allocateData[key] === '') {
        allocateData[key] = undefined
      }
    })
    
    // 获取分配前的当前行数据索引，以便后续更新
    const rowIndex = tableData.value.findIndex(item => item.id === currentRow.value?.id)
    
    // 调用API进行分配
    const response = await ipAddressApi.allocate(currentRow.value.id, allocateData)
    
    // 立即更新前端展示数据
    if (rowIndex !== -1 && response) {
      // 更新表格中的对应行数据
      tableData.value[rowIndex] = response
      ElMessage.success('IP地址分配成功')
    } else {
      // 如果无法定位到行，则重新加载所有数据
      ElMessage.success('IP地址分配成功，正在刷新数据')
      loadData()
    }
    
    allocateDialogVisible.value = false
  } catch (error) {
    console.error('分配IP地址失败:', error)
  }
}

const handleAddConfirm = async () => {
  if (!addFormRef.value) return
  
  try {
    await addFormRef.value.validate()
    
    // 创建表单数据副本用于处理
    const formData = {...addForm}
    
    // 转换os_type值
    if (formData.os_type) {
      formData.os_type = osTypeEnumMap[formData.os_type] || formData.os_type
    }
    
    // 确保非必填字段在为空时设置为undefined而不是空字符串
    Object.keys(formData).forEach(key => {
      if (formData[key] === '') {
        formData[key] = undefined
      }
    })
    
    // 调用API创建IP地址
    const response = await ipAddressApi.create(formData)
    
    // 立即更新前端展示数据
    if (response) {
      // 将新添加的数据添加到表格顶部
      tableData.value.unshift(response)
      ElMessage.success('IP地址添加成功')
    } else {
      // 如果没有返回数据，则重新加载所有数据
      ElMessage.success('IP地址添加成功，正在刷新数据')
      loadData()
    }
    
    addDialogVisible.value = false
  } catch (error: any) {
    console.error('添加IP地址失败:', error)
    // 错误消息已由request拦截器处理，这里不需要再次显示
  }
}

const handleEditConfirm = async () => {
  if (!editFormRef.value) return
  
  try {
    await editFormRef.value.validate()
    
    if (!editForm.id) return
    
    // 准备更新数据
    const updateData = {
      ip_address: editForm.ip_address,
      network_segment_id: editForm.network_segment_id,
      status: editForm.status,
      device_name: editForm.device_name,
      device_type: editForm.device_type,
      mac_address: editForm.mac_address,
      hostname: editForm.hostname,
      os_type: editForm.os_type,
      purpose: editForm.purpose,
      notes: editForm.notes,
      assigned_user_id: editForm.assigned_user_id,
      assigned_department_id: editForm.assigned_department_id,
      allocated_at: editForm.allocated_at
    }
    
    // 转换os_type值
    if (updateData.os_type) {
      updateData.os_type = osTypeEnumMap[updateData.os_type] || updateData.os_type
    }
    
    // 确保非必填字段在为空时设置为undefined而不是空字符串
    Object.keys(updateData).forEach(key => {
      if (updateData[key] === '') {
        updateData[key] = undefined
      }
    })
    
    // 获取编辑前的当前行数据索引，以便后续更新
    const rowIndex = tableData.value.findIndex(item => item.id === editForm.id)
    
    // 调用API进行更新
    const response = await ipAddressApi.update(editForm.id, updateData)
    
    // 立即更新前端展示数据
    if (rowIndex !== -1 && response) {
      // 更新表格中的对应行数据
      tableData.value[rowIndex] = response
      ElMessage.success('IP地址修改成功')
    } else {
      // 如果无法定位到行，则重新加载所有数据
      ElMessage.success('IP地址修改成功，正在刷新数据')
      loadData()
    }
    
    editDialogVisible.value = false
  } catch (error: any) {
    console.error('修改IP地址失败:', error)
    // 错误消息已由request拦截器处理，这里不需要再次显示
  }
}

const handleRelease = async (row: IPAddress) => {
  try {
    await ElMessageBox.confirm(
      `确定要释放IP地址 ${row.ip_address} 吗？`,
      '确认释放',
      { type: 'warning' }
    )
    
    // 获取释放前的当前行数据索引，以便后续更新
    const rowIndex = tableData.value.findIndex(item => item.id === row.id)
    
    // 调用API进行释放
    const response = await ipAddressApi.release(row.id)
    
    // 立即更新前端展示数据
    if (rowIndex !== -1 && response) {
      // 更新表格中的对应行数据
      tableData.value[rowIndex] = response
      ElMessage.success('IP地址释放成功')
    } else {
      // 如果无法定位到行，则重新加载所有数据
      ElMessage.success('IP地址释放成功，正在刷新数据')
      loadData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('释放IP地址失败:', error)
    }
  }
}

const handleEdit = (row: IPAddress) => {
  currentRow.value = row
  editDialogVisible.value = true
  
  // 初始化编辑表单数据，确保与前端展示一致
  Object.assign(editForm, {
    id: row.id,
    ip_address: row.ip_address,
    network_segment_id: row.network_segment?.id,
    status: row.status,
    device_name: row.device_name || '',
    device_type: row.device_type || '',
    mac_address: row.mac_address || '',
    hostname: row.hostname || '',
    os_type: row.os_type || '',
    purpose: row.purpose || '',
    notes: row.notes || '',
    assigned_user_id: row.assigned_user?.id,
    assigned_department_id: row.assigned_department?.id,
    allocated_at: row.allocated_at || ''
  })
  
  // 如果有分配用户，需要加载用户信息到下拉框
  if (row.assigned_user) {
    users.value = [row.assigned_user]
  }
}

const handleDropdownCommand = (command: string, row: IPAddress) => {
  switch (command) {
    case 'history':
      ElMessage.info('查看使用历史功能开发中...')
      break
    case 'delete':
      handleDelete(row)
      break
  }
}

const handleDelete = async (row: IPAddress) => {
  try {
    // 检查IP地址状态，如果已分配或保留则提示警告
    if (row.status === 'allocated') {
      await ElMessageBox.confirm(
        `IP地址 ${row.ip_address} 当前已分配给用户 ${row.assigned_user?.real_name || '未知'}，确定要删除吗？`,
        '确认删除已分配IP',
        { type: 'warning' }
      )
      
      // 先释放已分配的IP
      try {
        await ipAddressApi.release(row.id)
        console.info(`IP地址 ${row.ip_address} 释放成功，准备删除`)
      } catch (releaseError) {
        console.error(`释放IP地址 ${row.ip_address} 失败:`, releaseError)
        ElMessage.error(`释放 ${row.ip_address} 失败，无法删除`)
        return
      }
    } else if (row.status === 'reserved') {
      await ElMessageBox.confirm(
        `IP地址 ${row.ip_address} 当前处于保留状态，确定要删除吗？`,
        '确认删除已保留IP',
        { type: 'warning' }
      )
    } else {
      await ElMessageBox.confirm(
        `确定要删除IP地址 ${row.ip_address} 吗？`,
        '确认删除',
        { type: 'warning' }
      )
    }
    
    // 获取要删除的行索引
    const rowIndex = tableData.value.findIndex(item => item.id === row.id)
    
    // 调用API删除IP地址
    await ipAddressApi.delete(row.id)
    
    // 如果能找到行索引，则直接从表格中移除该行
    if (rowIndex !== -1) {
      tableData.value.splice(rowIndex, 1)
      ElMessage.success('删除成功')
    } else {
      // 如果找不到行，则重新加载数据
      ElMessage.success('删除成功，正在刷新数据')
      loadData()
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除IP地址失败:', error)
      ElMessage.error('删除失败')
    }
  }
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

const handleBatchCommand = (command: string) => {
  switch (command) {
    case 'selectAll':
      // 全选当前页的所有数据
      selectedRows.value = [...tableData.value]
      break
    case 'unselectAll':
      // 取消所有选择
      selectedRows.value = []
      break
    case 'batchDelete':
      handleBatchDelete()
      break
  }
}

const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请选择要删除的IP地址')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要批量删除选中的 ${selectedRows.value.length} 个IP地址吗？此操作不可恢复！`,
      '确认批量删除',
      { type: 'warning' }
    )
    
    // 检查是否有已分配的IP地址
    const allocatedIps = selectedRows.value.filter(ip => ip.status === 'allocated')
    if (allocatedIps.length > 0) {
      await ElMessageBox.confirm(
        `选中的IP地址中有 ${allocatedIps.length} 个已分配的IP地址，需要先释放后才能删除。是否继续？`,
        '释放并删除已分配的IP',
        { type: 'warning' }
      )
      
      // 先释放已分配的IP地址
      loading.value = true
      ElMessage.info('正在释放已分配的IP地址...')
      
      try {
        // 先释放已分配的IP
        for (const ip of allocatedIps) {
          try {
            await ipAddressApi.release(ip.id)
            console.info(`IP地址 ${ip.ip_address} 释放成功`)
          } catch (releaseError) {
            console.error(`释放IP地址 ${ip.ip_address} 失败:`, releaseError)
            ElMessage.error(`释放 ${ip.ip_address} 失败，该IP地址将被跳过`)
          }
        }
      } catch (batchReleaseError) {
        console.error('批量释放IP地址失败:', batchReleaseError)
        ElMessage.error('部分IP地址释放失败，将只删除可用的IP地址')
      }
    }
    
    // 重新获取可删除的IP地址
    const deletableIps = selectedRows.value.filter(ip => ip.status !== 'allocated')
    
    if (deletableIps.length === 0) {
      ElMessage.warning('没有可删除的IP地址')
      loading.value = false
      return
    }
    
    // 批量删除
    ElMessage.info(`正在删除 ${deletableIps.length} 个IP地址...`)
    let successCount = 0
    let failCount = 0
    
    // 记录要删除的IP地址ID列表
    const deleteIds = deletableIps.map(ip => ip.id)
    
    // 逐个删除，以便跟踪进度和处理错误
    for (const ip of deletableIps) {
      try {
        await ipAddressApi.delete(ip.id)
        successCount++
        console.info(`删除IP地址 ${ip.ip_address} 成功`)
      } catch (deleteError) {
        failCount++
        console.error(`删除IP地址 ${ip.ip_address} 失败:`, deleteError)
      }
    }
    
    if (successCount > 0) {
      ElMessage.success(`成功删除 ${successCount} 个IP地址`)
    }
    
    if (failCount > 0) {
      ElMessage.warning(`${failCount} 个IP地址删除失败`)
    }
    
    // 直接从表格中移除已删除的行
    if (successCount > 0) {
      // 过滤掉已删除的行
      tableData.value = tableData.value.filter(item => !deleteIds.includes(item.id) || 
        deletableIps.some(deletedIp => deletedIp.id === item.id))
      
      // 清空选择
      selectedRows.value = []
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除IP地址失败:', error)
      ElMessage.error('批量删除失败')
    }
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  // 确保每页显示20行数据
  pagination.size = 20
  pagination.page = 1
  loadData()
  loadNetworkSegments()
  loadOSTypes()
  checkDevice()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

// 窗口大小变化处理
const handleResize = () => {
  checkDevice()
}
</script>

<style scoped>
.ip-address-list {
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
  padding: 10px 0;
  background-color: #f8f8f8;
  border-top: 1px solid #ebeef5;
}

.text-muted {
  color: #909399;
}

.small {
  font-size: 12px;
}

code {
  font-family: 'Courier New', Courier, monospace;
  background-color: #f5f5f5;
  padding: 2px 4px;
  border-radius: 2px;
  font-size: 12px;
}

/* 添加表单样式 */
.add-form .el-form-item,
.edit-form .el-form-item {
  margin-bottom: 20px;
}

.add-form .el-form-item__label,
.edit-form .el-form-item__label {
  font-weight: 500;
  color: #606266;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .search-form .el-form-item {
    margin-right: 8px;
    margin-bottom: 10px;
  }
  
  .toolbar {
    flex-wrap: wrap;
    gap: 10px;
  }
}

@media (max-width: 768px) {
  .ip-address-list {
    padding: 0 10px;
  }
  
  .search-card,
  .toolbar-card,
  .table-card {
    margin-bottom: 15px;
  }
  
  .search-form {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-form .el-form-item {
    margin-right: 0;
    margin-bottom: 15px;
    width: 100%;
  }
  
  .search-form .el-form-item .el-input,
  .search-form .el-form-item .el-select {
    width: 100% !important;
  }
  
  .toolbar {
    flex-direction: column;
    gap: 15px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
    gap: 10px;
  }
  
  .toolbar-left .el-button,
  .toolbar-right .el-button {
    flex: 1;
    min-width: 120px;
  }
  
  /* 表格响应式 */
  .table-card {
    overflow-x: auto;
  }
  
  .el-table {
    min-width: 1000px;
  }
  
  /* 分页容器相应式 */
  @media (max-width: 768px) {
    .pagination-container {
      justify-content: center;
      margin-top: 15px;
      padding: 15px 0;
    }
    
    .el-pagination {
      flex-wrap: wrap;
      justify-content: center;
      row-gap: 10px;
    }
    
    .el-pagination .el-pagination__total,
    .el-pagination .el-pagination__sizes,
    .el-pagination .el-pagination__jump {
      margin-right: 0;
      margin-bottom: 5px;
    }
  }
}

@media (max-width: 480px) {
  .ip-address-list {
    padding: 0 5px;
  }
  
  .toolbar-left .el-button,
  .toolbar-right .el-button {
    min-width: 100px;
    font-size: 12px;
    padding: 8px 15px;
  }
  
  .toolbar-left .el-button .el-icon,
  .toolbar-right .el-button .el-icon {
    margin-right: 4px;
  }
  
  .search-form .el-form-item {
    margin-bottom: 12px;
  }
  
  .search-form .el-button {
    width: 100%;
    margin-bottom: 8px;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-pagination {
    font-size: 12px;
  }
  
  .el-pagination .btn-prev,
  .el-pagination .btn-next,
  .el-pagination .el-pager li {
    min-width: 28px;
    height: 28px;
    line-height: 28px;
  }
}
</style>