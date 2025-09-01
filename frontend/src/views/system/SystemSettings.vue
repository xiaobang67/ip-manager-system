<template>
  <div class="system-settings">
    <div class="page-header">
      <div class="header-content">
        <h1>系统设置</h1>
        <p>管理系统配置和认证设置</p>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 认证统计 -->
      <el-col :span="24">
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <h3>认证统计</h3>
              <el-button @click="loadStats" :loading="statsLoading">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_users }}</div>
                <div class="stat-label">总用户数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.active_users }}</div>
                <div class="stat-label">活跃用户</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.local_users }}</div>
                <div class="stat-label">本地用户</div>
              </div>
            </el-col>
          </el-row>

          <el-divider />

          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_groups }}</div>
                <div class="stat-label">总组数</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.total_groups }}</div>
                <div class="stat-label">本地组</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <div class="stat-value">{{ stats.active_sessions }}</div>
                <div class="stat-label">活跃会话</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 系统信息 -->
      <el-col :span="24">
        <el-card class="info-card">
          <template #header>
            <h3>系统信息</h3>
          </template>
          
          <div class="info-content">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="系统名称">
                企业IP地址管理系统
              </el-descriptions-item>
              <el-descriptions-item label="系统版本">
                v1.0.0
              </el-descriptions-item>
              <el-descriptions-item label="认证方式">
                本地认证
              </el-descriptions-item>
              <el-descriptions-item label="会话管理">
                JWT令牌
              </el-descriptions-item>
              <el-descriptions-item label="数据库">
                MySQL
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>

      <!-- 操作日志 -->
      <el-col :span="24">
        <el-card class="log-card">
          <template #header>
            <div class="card-header">
              <h3>最近操作</h3>
              <el-button @click="loadLogs" :loading="logLoading">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <el-table
            v-loading="logLoading"
            :data="operationLogs"
            style="width: 100%"
          >
            <el-table-column prop="timestamp" label="时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="user" label="操作用户" width="120" />
            <el-table-column prop="action" label="操作类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getActionType(row.action)">
                  {{ row.action }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="target" label="操作对象" width="150" />
            <el-table-column prop="description" label="操作描述" min-width="200" />
            <el-table-column prop="ip" label="IP地址" width="130" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.status === 'success' ? 'success' : 'danger'">
                  {{ row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-section">
            <el-pagination
              v-model:current-page="logPagination.page"
              v-model:page-size="logPagination.size"
              :total="logPagination.total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="loadLogs"
              @current-change="loadLogs"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { systemApi } from '@/api/system'
import type { AuthStatsResponse } from '@/api/auth'
import type { OperationLog } from '@/api/system'

// 响应式数据
const statsLoading = ref(false)
const logLoading = ref(false)

// 统计数据
const stats = ref<AuthStatsResponse>({
  total_users: 0,
  active_users: 0,
  ldap_users: 0,
  local_users: 0,
  total_groups: 0,
  ldap_groups: 0,
  active_sessions: 0
})

// 操作日志
const operationLogs = ref<OperationLog[]>([])

// 日志分页
const logPagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 方法
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const getActionType = (action: string) => {
  const typeMap: Record<string, string> = {
    '登录': 'success',
    '登出': 'info',
    '创建用户': 'primary',
    '修改用户': 'warning',
    '删除用户': 'danger'
  }
  return typeMap[action] || 'info'
}

// 加载统计数据
const loadStats = async () => {
  statsLoading.value = true
  try {
    const data = await authApi.getAuthStats()
    stats.value = data
  } catch (error) {
    ElMessage.error('加载统计数据失败')
    console.error(error)
  } finally {
    statsLoading.value = false
  }
}

// 加载操作日志
const loadLogs = async () => {
  logLoading.value = true
  try {
    const data = await systemApi.getOperationLogs({
      skip: (logPagination.page - 1) * logPagination.size,
      limit: logPagination.size
    })
    operationLogs.value = data.items
    logPagination.total = data.total
  } catch (error) {
    ElMessage.error('加载操作日志失败')
    console.error(error)
  } finally {
    logLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadStats()
  loadLogs()
})
</script>

<style scoped>
.system-settings {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.page-header h1 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 24px;
  font-weight: 600;
}

.page-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  color: #333;
  font-size: 16px;
  font-weight: 600;
}

.stats-card,
.info-card,
.log-card {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 10px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.info-content {
  padding: 10px 0;
}

.pagination-section {
  padding: 20px;
  text-align: right;
  border-top: 1px solid #eee;
}

/* Element Plus 样式覆盖 */
:deep(.el-card__header) {
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-table) {
  border-radius: 8px;
}

:deep(.el-table th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}

:deep(.el-alert) {
  margin-top: 10px;
}

:deep(.el-divider) {
  margin: 20px 0;
}
</style>