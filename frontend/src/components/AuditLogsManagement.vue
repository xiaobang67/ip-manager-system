<template>
  <div class="audit-logs-management">
    <div class="header">
      <h2>审计日志管理</h2>
      <div class="header-actions">
        <el-button 
          type="primary" 
          @click="showExportDialog = true"
          :disabled="!isAdmin"
        >
          <el-icon><Download /></el-icon>
          导出日志
        </el-button>
        <el-button 
          type="warning" 
          @click="showArchiveDialog = true"
          :disabled="!isAdmin"
        >
          <el-icon><Delete /></el-icon>
          归档日志
        </el-button>
        <el-button 
          type="info" 
          @click="showStatsDialog = true"
          :disabled="!isAdmin"
        >
          <el-icon><DataAnalysis /></el-icon>
          统计信息
        </el-button>
      </div>
    </div>

    <!-- 搜索过滤器 -->
    <el-card class="search-card" shadow="never">
      <div class="search-form">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-select 
              v-model="searchForm.action" 
              placeholder="选择操作类型" 
              clearable
              style="width: 100%"
            >
              <el-option label="创建" value="CREATE" />
              <el-option label="更新" value="UPDATE" />
              <el-option label="删除" value="DELETE" />
              <el-option label="分配" value="ALLOCATE" />
              <el-option label="释放" value="RELEASE" />
              <el-option label="保留" value="RESERVE" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select 
              v-model="searchForm.entity_type" 
              placeholder="选择实体类型" 
              clearable
              style="width: 100%"
            >
              <el-option label="IP地址" value="ip" />
              <el-option label="网段" value="subnet" />
              <el-option label="用户" value="user" />
              <el-option label="自定义字段" value="custom_field" />
              <el-option label="标签" value="tag" />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select 
              v-model="searchForm.user_id" 
              placeholder="选择用户" 
              clearable
              filterable
              style="width: 100%"
            >
              <el-option 
                v-for="user in users" 
                :key="user.id" 
                :label="user.username" 
                :value="user.id" 
              />
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-input 
              v-model="searchForm.entity_id" 
              placeholder="实体ID" 
              clearable
              type="number"
            />
          </el-col>
        </el-row>
        <el-row :gutter="20" style="margin-top: 16px">
          <el-col :span="10">
            <el-date-picker
              v-model="dateRange"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              style="width: 100%"
            />
          </el-col>
          <el-col :span="6">
            <el-button type="primary" @click="searchLogs">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
            <el-button @click="resetSearch">
              <el-icon><Refresh /></el-icon>
              重置
            </el-button>
          </el-col>
        </el-row>
      </div>
    </el-card>

    <!-- 审计日志表格 -->
    <el-card class="table-card" shadow="never">
      <el-table 
        :data="auditLogs" 
        v-loading="loading"
        stripe
        style="width: 100%"
        @row-click="showLogDetail"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="action" label="操作" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="entity_type" label="实体类型" width="120">
          <template #default="{ row }">
            <el-tag type="info">
              {{ getEntityTypeText(row.entity_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="entity_id" label="实体ID" width="100" />
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="ip_address" label="操作IP" width="140" />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click.stop="showLogDetail(row)"
            >
              详情
            </el-button>
            <el-button 
              size="small" 
              type="primary"
              @click.stop="showEntityHistory(row)"
              v-if="row.entity_id"
            >
              历史记录
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
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
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog 
      v-model="showDetailDialog" 
      title="审计日志详情" 
      width="60%"
      :close-on-click-modal="false"
    >
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="日志ID">{{ selectedLog.id }}</el-descriptions-item>
          <el-descriptions-item label="操作类型">
            <el-tag :type="getActionTagType(selectedLog.action)">
              {{ getActionText(selectedLog.action) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="实体类型">
            <el-tag type="info">
              {{ getEntityTypeText(selectedLog.entity_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="实体ID">{{ selectedLog.entity_id || 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="操作用户">{{ selectedLog.username }}</el-descriptions-item>
          <el-descriptions-item label="操作IP">{{ selectedLog.ip_address || 'N/A' }}</el-descriptions-item>
          <el-descriptions-item label="操作时间" :span="2">
            {{ formatDateTime(selectedLog.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="用户代理" :span="2">
            {{ selectedLog.user_agent || 'N/A' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 变更详情 -->
        <div v-if="selectedLog.old_values || selectedLog.new_values" class="change-details">
          <h4>变更详情</h4>
          <el-row :gutter="20">
            <el-col :span="12" v-if="selectedLog.old_values">
              <h5>变更前</h5>
              <pre class="json-display">{{ JSON.stringify(selectedLog.old_values, null, 2) }}</pre>
            </el-col>
            <el-col :span="12" v-if="selectedLog.new_values">
              <h5>变更后</h5>
              <pre class="json-display">{{ JSON.stringify(selectedLog.new_values, null, 2) }}</pre>
            </el-col>
          </el-row>
        </div>
      </div>
    </el-dialog>

    <!-- 实体历史记录对话框 -->
    <el-dialog 
      v-model="showHistoryDialog" 
      title="实体历史记录" 
      width="80%"
      :close-on-click-modal="false"
    >
      <el-table :data="entityHistory" v-loading="historyLoading" stripe>
        <el-table-column prop="action" label="操作" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)">
              {{ getActionText(row.action) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="操作用户" width="120" />
        <el-table-column prop="ip_address" label="操作IP" width="140" />
        <el-table-column prop="created_at" label="操作时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="变更内容">
          <template #default="{ row }">
            <div v-if="row.old_values || row.new_values">
              <el-button size="small" @click="showChangeDetail(row)">查看变更</el-button>
            </div>
            <span v-else>无变更数据</span>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 导出对话框 -->
    <el-dialog 
      v-model="showExportDialog" 
      title="导出审计日志" 
      width="40%"
      :close-on-click-modal="false"
    >
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式">
          <el-radio-group v-model="exportForm.format">
            <el-radio label="csv">CSV</el-radio>
            <el-radio label="excel">Excel</el-radio>
            <el-radio label="json">JSON</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="exportDateRange"
            type="datetimerange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="exportForm.action" placeholder="选择操作类型" clearable>
            <el-option label="创建" value="CREATE" />
            <el-option label="更新" value="UPDATE" />
            <el-option label="删除" value="DELETE" />
            <el-option label="分配" value="ALLOCATE" />
            <el-option label="释放" value="RELEASE" />
            <el-option label="保留" value="RESERVE" />
          </el-select>
        </el-form-item>
        <el-form-item label="实体类型">
          <el-select v-model="exportForm.entity_type" placeholder="选择实体类型" clearable>
            <el-option label="IP地址" value="ip" />
            <el-option label="网段" value="subnet" />
            <el-option label="用户" value="user" />
            <el-option label="自定义字段" value="custom_field" />
            <el-option label="标签" value="tag" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="exportLogs" :loading="exportLoading">
          导出
        </el-button>
      </template>
    </el-dialog>

    <!-- 归档对话框 -->
    <el-dialog 
      v-model="showArchiveDialog" 
      title="归档审计日志" 
      width="40%"
      :close-on-click-modal="false"
    >
      <el-alert
        title="警告"
        type="warning"
        description="归档操作将永久删除指定天数之前的审计日志，此操作不可恢复！"
        show-icon
        :closable="false"
        style="margin-bottom: 20px"
      />
      <el-form :model="archiveForm" label-width="120px">
        <el-form-item label="保留天数">
          <el-input-number 
            v-model="archiveForm.daysToKeep" 
            :min="30" 
            :max="3650"
            controls-position="right"
            style="width: 200px"
          />
          <span style="margin-left: 10px; color: #909399;">
            将删除 {{ archiveForm.daysToKeep }} 天前的所有日志
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showArchiveDialog = false">取消</el-button>
        <el-button type="danger" @click="archiveLogs" :loading="archiveLoading">
          确认归档
        </el-button>
      </template>
    </el-dialog>

    <!-- 统计信息对话框 -->
    <el-dialog 
      v-model="showStatsDialog" 
      title="审计日志统计" 
      width="60%"
      :close-on-click-modal="false"
    >
      <div v-if="statistics" class="stats-content">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="总日志数" :value="statistics.total_logs" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="操作类型数" :value="Object.keys(statistics.actions_count).length" />
          </el-col>
          <el-col :span="8">
            <el-statistic title="涉及实体数" :value="Object.keys(statistics.entities_count).length" />
          </el-col>
        </el-row>

        <div class="stats-charts" style="margin-top: 30px">
          <el-row :gutter="20">
            <el-col :span="12">
              <h4>操作类型分布</h4>
              <div class="chart-container">
                <div v-for="(count, action) in statistics.actions_count" :key="action" class="stat-item">
                  <span class="stat-label">{{ getActionText(action) }}</span>
                  <span class="stat-value">{{ count }}</span>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <h4>实体类型分布</h4>
              <div class="chart-container">
                <div v-for="(count, entity) in statistics.entities_count" :key="entity" class="stat-item">
                  <span class="stat-label">{{ getEntityTypeText(entity) }}</span>
                  <span class="stat-value">{{ count }}</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <div class="recent-activities" style="margin-top: 30px">
          <h4>最近活动</h4>
          <el-table :data="statistics.recent_activities" size="small" max-height="300">
            <el-table-column prop="action" label="操作" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="getActionTagType(row.action)">
                  {{ getActionText(row.action) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="entity_type" label="实体" width="80">
              <template #default="{ row }">
                <el-tag size="small" type="info">
                  {{ getEntityTypeText(row.entity_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="username" label="用户" width="100" />
            <el-table-column prop="created_at" label="时间">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Delete, DataAnalysis, Search, Refresh } from '@element-plus/icons-vue'
import { useStore } from 'vuex'
import auditLogsApi from '@/api/auditLogs'
import { getUsers } from '@/api/users'

export default {
  name: 'AuditLogsManagement',
  components: {
    Download,
    Delete,
    DataAnalysis,
    Search,
    Refresh
  },
  setup() {
    const store = useStore()
    
    // 响应式数据
    const loading = ref(false)
    const historyLoading = ref(false)
    const exportLoading = ref(false)
    const archiveLoading = ref(false)
    
    const auditLogs = ref([])
    const entityHistory = ref([])
    const users = ref([])
    const statistics = ref(null)
    
    const currentPage = ref(1)
    const pageSize = ref(50)
    const total = ref(0)
    
    const dateRange = ref([])
    const exportDateRange = ref([])
    
    // 对话框显示状态
    const showDetailDialog = ref(false)
    const showHistoryDialog = ref(false)
    const showExportDialog = ref(false)
    const showArchiveDialog = ref(false)
    const showStatsDialog = ref(false)
    
    const selectedLog = ref(null)
    
    // 表单数据
    const searchForm = reactive({
      action: '',
      entity_type: '',
      user_id: null,
      entity_id: null
    })
    
    const exportForm = reactive({
      format: 'csv',
      action: '',
      entity_type: ''
    })
    
    const archiveForm = reactive({
      daysToKeep: 365
    })
    
    // 计算属性
    const isAdmin = computed(() => {
      return store.getters['auth/userRole'] === 'ADMIN'
    })
    
    // 方法
    const loadAuditLogs = async () => {
      loading.value = true
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value,
          ...searchForm
        }
        
        if (dateRange.value && dateRange.value.length === 2) {
          params.start_date = dateRange.value[0]
          params.end_date = dateRange.value[1]
        }
        
        const response = await auditLogsApi.searchAuditLogs(params)
        auditLogs.value = response.data.items
        total.value = response.data.total
      } catch (error) {
        ElMessage.error('加载审计日志失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    const loadUsers = async () => {
      try {
        const response = await getUsers()
        users.value = response.users || response.data || []
      } catch (error) {
        console.error('加载用户列表失败:', error)
      }
    }
    
    const searchLogs = () => {
      currentPage.value = 1
      loadAuditLogs()
    }
    
    const resetSearch = () => {
      Object.assign(searchForm, {
        action: '',
        entity_type: '',
        user_id: null,
        entity_id: null
      })
      dateRange.value = []
      currentPage.value = 1
      loadAuditLogs()
    }
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      loadAuditLogs()
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadAuditLogs()
    }
    
    const showLogDetail = (row) => {
      selectedLog.value = row
      showDetailDialog.value = true
    }
    
    const showEntityHistory = async (row) => {
      if (!row.entity_id) {
        ElMessage.warning('该记录没有关联的实体ID')
        return
      }
      
      historyLoading.value = true
      try {
        const response = await auditLogsApi.getEntityHistory(row.entity_type, row.entity_id)
        entityHistory.value = response.data.history
        showHistoryDialog.value = true
      } catch (error) {
        ElMessage.error('加载实体历史记录失败: ' + error.message)
      } finally {
        historyLoading.value = false
      }
    }
    
    const showChangeDetail = (row) => {
      selectedLog.value = row
      showDetailDialog.value = true
    }
    
    const exportLogs = async () => {
      exportLoading.value = true
      try {
        const params = {
          ...exportForm
        }
        
        if (exportDateRange.value && exportDateRange.value.length === 2) {
          params.start_date = exportDateRange.value[0]
          params.end_date = exportDateRange.value[1]
        }
        
        const response = await auditLogsApi.exportAuditLogs(params)
        
        // 创建下载链接
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-')
        link.download = `audit_logs_${timestamp}.${params.format}`
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('审计日志导出成功')
        showExportDialog.value = false
      } catch (error) {
        ElMessage.error('导出审计日志失败: ' + error.message)
      } finally {
        exportLoading.value = false
      }
    }
    
    const archiveLogs = async () => {
      try {
        await ElMessageBox.confirm(
          `确定要删除 ${archiveForm.daysToKeep} 天前的所有审计日志吗？此操作不可恢复！`,
          '确认归档',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        archiveLoading.value = true
        const response = await auditLogsApi.archiveOldLogs(archiveForm.daysToKeep)
        
        ElMessage.success(response.data.message)
        showArchiveDialog.value = false
        loadAuditLogs() // 重新加载数据
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('归档审计日志失败: ' + error.message)
        }
      } finally {
        archiveLoading.value = false
      }
    }
    
    const loadStatistics = async () => {
      try {
        const response = await auditLogsApi.getAuditStatistics()
        statistics.value = response.data
        showStatsDialog.value = true
      } catch (error) {
        ElMessage.error('加载统计信息失败: ' + error.message)
      }
    }
    
    // 辅助方法
    const getActionText = (action) => {
      const actionMap = {
        CREATE: '创建',
        UPDATE: '更新',
        DELETE: '删除',
        ALLOCATE: '分配',
        RELEASE: '释放',
        RESERVE: '保留'
      }
      return actionMap[action] || action
    }
    
    const getActionTagType = (action) => {
      const typeMap = {
        CREATE: 'success',
        UPDATE: 'warning',
        DELETE: 'danger',
        ALLOCATE: 'primary',
        RELEASE: 'info',
        RESERVE: 'warning'
      }
      return typeMap[action] || 'info'
    }
    
    const getEntityTypeText = (entityType) => {
      const typeMap = {
        ip: 'IP地址',
        subnet: '网段',
        user: '用户',
        custom_field: '自定义字段',
        tag: '标签'
      }
      return typeMap[entityType] || entityType
    }
    
    const formatDateTime = (dateTime) => {
      if (!dateTime) return 'N/A'
      return new Date(dateTime).toLocaleString('zh-CN')
    }
    
    // 生命周期
    onMounted(() => {
      loadAuditLogs()
      loadUsers()
    })
    
    return {
      // 响应式数据
      loading,
      historyLoading,
      exportLoading,
      archiveLoading,
      auditLogs,
      entityHistory,
      users,
      statistics,
      currentPage,
      pageSize,
      total,
      dateRange,
      exportDateRange,
      showDetailDialog,
      showHistoryDialog,
      showExportDialog,
      showArchiveDialog,
      showStatsDialog,
      selectedLog,
      searchForm,
      exportForm,
      archiveForm,
      
      // 计算属性
      isAdmin,
      
      // 方法
      loadAuditLogs,
      searchLogs,
      resetSearch,
      handleSizeChange,
      handleCurrentChange,
      showLogDetail,
      showEntityHistory,
      showChangeDetail,
      exportLogs,
      archiveLogs,
      loadStatistics,
      getActionText,
      getActionTagType,
      getEntityTypeText,
      formatDateTime
    }
  }
}
</script>

<style scoped>
.audit-logs-management {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.search-card {
  margin-bottom: 20px;
}

.search-form {
  padding: 10px 0;
}

.table-card {
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.log-detail {
  max-height: 600px;
  overflow-y: auto;
}

.change-details {
  margin-top: 20px;
}

.change-details h4 {
  margin-bottom: 15px;
  color: #303133;
}

.change-details h5 {
  margin-bottom: 10px;
  color: #606266;
}

.json-display {
  background-color: #f5f7fa;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.stats-content {
  max-height: 600px;
  overflow-y: auto;
}

.chart-container {
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  max-height: 200px;
  overflow-y: auto;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #ebeef5;
}

.stat-item:last-child {
  border-bottom: none;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  color: #303133;
  font-weight: bold;
  font-size: 16px;
}

.recent-activities {
  margin-top: 20px;
}

.recent-activities h4 {
  margin-bottom: 15px;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .audit-logs-management {
    padding: 10px;
  }
  
  .header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-start;
    flex-wrap: wrap;
  }
  
  .search-form .el-row {
    margin-bottom: 10px;
  }
  
  .search-form .el-col {
    margin-bottom: 10px;
  }
}

/* 暗色主题支持 */
.dark .json-display {
  background-color: #2d2d2d;
  border-color: #4c4d4f;
  color: #e4e7ed;
}

.dark .chart-container {
  background-color: #2d2d2d;
  border: 1px solid #4c4d4f;
}

.dark .stat-item {
  border-bottom-color: #4c4d4f;
}
</style>