<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <!-- 统计卡片 -->
      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon networks">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_segments }}</div>
              <div class="stat-label">网段总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon ips">
              <el-icon><Location /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_ips }}</div>
              <div class="stat-label">IP地址总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon users">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_users }}</div>
              <div class="stat-label">用户总数</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon departments">
              <el-icon><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_departments }}</div>
              <div class="stat-label">部门总数</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- IP地址使用情况 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>IP地址使用情况</span>
            </div>
          </template>
          <div class="chart-container" style="height: 300px;">
            <div class="ip-usage-chart">
              <div class="usage-item">
                <div class="usage-label">
                  <div class="usage-dot available"></div>
                  <span>可用</span>
                </div>
                <div class="usage-value">{{ stats.available_ips }}</div>
                <div class="usage-percent">
                  {{ getPercentage(stats.available_ips, stats.total_ips) }}%
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">
                  <div class="usage-dot allocated"></div>
                  <span>已分配</span>
                </div>
                <div class="usage-value">{{ stats.allocated_ips }}</div>
                <div class="usage-percent">
                  {{ getPercentage(stats.allocated_ips, stats.total_ips) }}%
                </div>
              </div>
              
              <div class="usage-item">
                <div class="usage-label">
                  <div class="usage-dot reserved"></div>
                  <span>已保留</span>
                </div>
                <div class="usage-value">{{ stats.reserved_ips }}</div>
                <div class="usage-percent">
                  {{ getPercentage(stats.reserved_ips, stats.total_ips) }}%
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 最近活动 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>最近活动</span>
              <el-button text @click="refreshActivities">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div class="activity-list">
            <div 
              v-for="activity in recentActivities" 
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon">
                <el-icon><Operation /></el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.title }}</div>
                <div class="activity-time">{{ activity.time }}</div>
              </div>
            </div>
            <div v-if="recentActivities.length === 0" class="empty-activities">
              <el-empty description="暂无活动记录" />
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <!-- 快速操作 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>快速操作</span>
            </div>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="goToIPManagement">
              <el-icon><Location /></el-icon>
              IP地址管理
            </el-button>
            <el-button type="success" @click="goToNetworkManagement">
              <el-icon><Connection /></el-icon>
              网段管理
            </el-button>
            <el-button type="warning" @click="goToReservedManagement">
              <el-icon><Lock /></el-icon>
              地址保留
            </el-button>
            <el-button type="info" @click="goToUserManagement">
              <el-icon><User /></el-icon>
              用户管理
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  Connection, 
  Location, 
  User, 
  OfficeBuilding, 
  Refresh, 
  Operation,
  Lock
} from '@element-plus/icons-vue'
import type { DashboardStats } from '@/types'
import { dashboardApi } from '@/api/dashboard'

const router = useRouter()

// 响应式数据
const stats = reactive<DashboardStats>({
  total_segments: 0,
  total_ips: 0,
  allocated_ips: 0,
  available_ips: 0,
  reserved_ips: 0,
  total_users: 0,
  total_departments: 0
})

const recentActivities = ref([])

const loadRecentActivities = async () => {
  try {
    const activities = await dashboardApi.getRecentActivities(5)
    recentActivities.value = activities
  } catch (error) {
    console.error('加载最近活动失败:', error)
    ElMessage.error('加载最近活动失败: ' + (error.message || '未知错误'))
    // 如果获取失败，使用默认数据
    recentActivities.value = [
      {
        id: 1,
        title: 'IP地址 192.168.1.100 已分配给用户张三',
        time: '2分钟前'
      },
      {
        id: 2,
        title: '新增网段 192.168.2.0/24',
        time: '10分钟前'
      },
      {
        id: 3,
        title: '用户李四的IP地址已释放',
        time: '1小时前'
      },
      {
        id: 4,
        title: '保留地址 192.168.1.1 即将过期',
        time: '2小时前'
      }
    ]
  }
}

// 方法
const getPercentage = (value: number, total: number): string => {
  if (total === 0) return '0'
  return ((value / total) * 100).toFixed(1)
}

const loadDashboardData = async () => {
  try {
    // 调用真实的API获取数据
    const data = await dashboardApi.getStats()
    Object.assign(stats, data)
    ElMessage.success('仪表盘数据加载成功')
  } catch (error) {
    console.error('加载仪表盘数据失败:', error)
    ElMessage.error('加载仪表盘数据失败: ' + (error.message || '未知错误'))
    // 如果获取数据失败，使用默认值
    Object.assign(stats, {
      total_segments: 0,
      total_ips: 0,
      allocated_ips: 0,
      available_ips: 0,
      reserved_ips: 0,
      total_users: 0,
      total_departments: 0
    })
  }
}

const refreshActivities = async () => {
  // 刷新最近活动数据
  await loadRecentActivities()
  ElMessage.success('活动数据已刷新')
}

// 导航方法
const goToIPManagement = () => {
  router.push('/ip-management/addresses')
}

const goToNetworkManagement = () => {
  router.push('/ip-management/segments')
}

const goToReservedManagement = () => {
  router.push('/ip-management/reserved')
}

const goToUserManagement = () => {
  router.push('/organization/users')
}

// 生命周期
onMounted(() => {
  loadDashboardData()
  loadRecentActivities()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stat-card {
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
  color: white;
}

.stat-icon.networks {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.ips {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.users {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.departments {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.ip-usage-chart {
  width: 100%;
}

.usage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.usage-item:last-child {
  border-bottom: none;
}

.usage-label {
  display: flex;
  align-items: center;
  flex: 1;
}

.usage-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}

.usage-dot.available {
  background-color: #67c23a;
}

.usage-dot.allocated {
  background-color: #e6a23c;
}

.usage-dot.reserved {
  background-color: #f56c6c;
}

.usage-value {
  font-weight: bold;
  color: #303133;
  margin-right: 12px;
}

.usage-percent {
  color: #909399;
  font-size: 12px;
}

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 32px;
  height: 32px;
  background-color: #f5f5f5;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  color: #909399;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  color: #303133;
  line-height: 1.4;
}

.activity-time {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 4px;
}

.empty-activities {
  padding: 40px 0;
}

.quick-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.quick-actions .el-button {
  flex: 1;
  min-width: 140px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .stat-value {
    font-size: 24px;
  }
  
  .quick-actions {
    flex-direction: column;
  }
  
  .quick-actions .el-button {
    width: 100%;
  }
}
</style>