<template>
  <div class="monitoring-dashboard">
    <!-- 导航头部 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1>IP地址管理系统</h1>
        <p class="header-description">企业网络资源管理平台</p>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button @click="navigateTo('/ip-management')">
            <el-icon><Network /></el-icon>
            IP管理
          </el-button>
          <el-button @click="navigateTo('/subnet-management')">
            <el-icon><Grid /></el-icon>
            网段管理
          </el-button>
          <el-button @click="navigateTo('/user-management')" v-if="isAdmin">
            <el-icon><User /></el-icon>
            用户管理
          </el-button>
          <el-button @click="navigateTo('/audit-logs')" v-if="isAdmin">
            <el-icon><Document /></el-icon>
            审计日志
          </el-button>
        </el-button-group>
        <el-dropdown @command="handleUserAction" style="margin-left: 15px">
          <el-button type="primary">
            {{ currentUser?.username || 'User' }}
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人资料</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon ip-icon">
              <el-icon><Network /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.ip_statistics?.total_ips || 0 }}</div>
              <div class="stat-label">总IP地址</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon utilization-icon">
              <el-icon><PieChart /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.ip_statistics?.utilization_rate || 0 }}%</div>
              <div class="stat-label">使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon subnet-icon">
              <el-icon><Grid /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.total_subnets || 0 }}</div>
              <div class="stat-label">网段数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon alert-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboardData.alert_statistics?.unresolved_alerts || 0 }}</div>
              <div class="stat-label">未解决警报</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-section">
      <!-- IP使用率饼图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>IP地址使用分布</span>
              <el-button type="text" @click="refreshIPStats">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <div ref="ipUtilizationChart" class="chart-container"></div>
        </el-card>
      </el-col>

      <!-- 分配趋势图 -->
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>IP分配趋势 (最近30天)</span>
              <el-select v-model="trendDays" @change="refreshTrends" size="small" style="width: 100px">
                <el-option label="7天" :value="7"></el-option>
                <el-option label="30天" :value="30"></el-option>
                <el-option label="90天" :value="90"></el-option>
              </el-select>
            </div>
          </template>
          <div ref="allocationTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 网段使用率表格 -->
    <el-row :gutter="20" class="table-section">
      <el-col :span="24">
        <el-card class="table-card">
          <template #header>
            <div class="card-header">
              <span>网段使用率排行</span>
              <div>
                <el-button type="primary" size="small" @click="showReportDialog = true">
                  <el-icon><Document /></el-icon>
                  生成报告
                </el-button>
                <el-button type="text" @click="refreshSubnetStats">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          
          <el-table :data="topSubnets" style="width: 100%" v-loading="loading">
            <el-table-column prop="network" label="网段" width="150"></el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip></el-table-column>
            <el-table-column prop="vlan_id" label="VLAN ID" width="100">
              <template #default="scope">
                {{ scope.row.vlan_id || 'N/A' }}
              </template>
            </el-table-column>
            <el-table-column prop="total_ips" label="总IP数" width="100"></el-table-column>
            <el-table-column prop="allocated_ips" label="已分配" width="100"></el-table-column>
            <el-table-column prop="utilization_rate" label="使用率" width="120">
              <template #default="scope">
                <el-progress 
                  :percentage="scope.row.utilization_rate" 
                  :color="getUtilizationColor(scope.row.utilization_rate)"
                  :show-text="true"
                  :format="() => `${scope.row.utilization_rate}%`"
                ></el-progress>
              </template>
            </el-table-column>
            <el-table-column prop="location" label="位置" show-overflow-tooltip></el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 警报面板 -->
    <el-row :gutter="20" class="alerts-section">
      <el-col :span="24">
        <el-card class="alerts-card">
          <template #header>
            <div class="card-header">
              <span>最近警报</span>
              <el-button type="text" @click="showAlertManagement">
                <el-icon><Setting /></el-icon>
                管理警报规则
              </el-button>
            </div>
          </template>
          
          <el-table :data="recentAlerts" style="width: 100%" v-loading="alertsLoading">
            <el-table-column prop="alert_message" label="警报信息" show-overflow-tooltip></el-table-column>
            <el-table-column prop="severity" label="严重程度" width="120">
              <template #default="scope">
                <el-tag :type="getSeverityType(scope.row.severity)">
                  {{ getSeverityText(scope.row.severity) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="scope">
                {{ formatDateTime(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column prop="is_resolved" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_resolved ? 'success' : 'warning'">
                  {{ scope.row.is_resolved ? '已解决' : '未解决' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button 
                  v-if="!scope.row.is_resolved"
                  type="text" 
                  size="small" 
                  @click="resolveAlert(scope.row.id)"
                >
                  解决
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 报告生成对话框 -->
    <ReportGenerationDialog 
      v-model="showReportDialog"
      @report-generated="handleReportGenerated"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Network, PieChart, Grid, Warning, Refresh, Document, Setting, User, ArrowDown } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { 
  getDashboardSummary, 
  getTopUtilizedSubnets, 
  getAllocationTrends,
  getAlertHistory,
  resolveAlert as resolveAlertAPI
} from '@/api/monitoring'
import ReportGenerationDialog from './ReportGenerationDialog.vue'

export default {
  name: 'MonitoringDashboard',
  components: {
    ReportGenerationDialog
  },
  setup() {
    const router = useRouter()
    const store = useStore()
    
    const loading = ref(false)
    const alertsLoading = ref(false)
    const dashboardData = reactive({})
    const topSubnets = ref([])
    const recentAlerts = ref([])
    const trendDays = ref(30)
    const showReportDialog = ref(false)
    
    // 计算属性
    const currentUser = computed(() => store.getters['auth/currentUser'])
    const isAdmin = computed(() => store.getters['auth/userRole'] === 'admin')

    // 图表实例
    const ipUtilizationChart = ref(null)
    const allocationTrendChart = ref(null)
    let ipChart = null
    let trendChart = null

    // 加载仪表盘数据
    const loadDashboardData = async () => {
      loading.value = true
      try {
        const response = await getDashboardSummary()
        Object.assign(dashboardData, response.data)
        
        // 更新IP使用率图表
        await nextTick()
        updateIPUtilizationChart()
      } catch (error) {
        ElMessage.error('加载仪表盘数据失败')
        console.error('Dashboard data error:', error)
      } finally {
        loading.value = false
      }
    }

    // 加载网段统计
    const loadSubnetStats = async () => {
      try {
        const response = await getTopUtilizedSubnets(10)
        topSubnets.value = response.data
      } catch (error) {
        ElMessage.error('加载网段统计失败')
        console.error('Subnet stats error:', error)
      }
    }

    // 加载分配趋势
    const loadAllocationTrends = async () => {
      try {
        const response = await getAllocationTrends(trendDays.value)
        await nextTick()
        updateAllocationTrendChart(response.data)
      } catch (error) {
        ElMessage.error('加载分配趋势失败')
        console.error('Allocation trends error:', error)
      }
    }

    // 加载警报历史
    const loadAlertHistory = async () => {
      alertsLoading.value = true
      try {
        const response = await getAlertHistory({ limit: 10 })
        recentAlerts.value = response.data
      } catch (error) {
        ElMessage.error('加载警报历史失败')
        console.error('Alert history error:', error)
      } finally {
        alertsLoading.value = false
      }
    }

    // 更新IP使用率图表
    const updateIPUtilizationChart = () => {
      if (!ipUtilizationChart.value || !dashboardData.ip_statistics) return

      if (!ipChart) {
        ipChart = echarts.init(ipUtilizationChart.value)
      }

      const stats = dashboardData.ip_statistics
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        legend: {
          orient: 'vertical',
          left: 'left'
        },
        series: [
          {
            name: 'IP地址分布',
            type: 'pie',
            radius: '50%',
            data: [
              { value: stats.allocated_ips, name: '已分配', itemStyle: { color: '#409EFF' } },
              { value: stats.reserved_ips, name: '保留', itemStyle: { color: '#E6A23C' } },
              { value: stats.available_ips, name: '可用', itemStyle: { color: '#67C23A' } },
              { value: stats.conflict_ips, name: '冲突', itemStyle: { color: '#F56C6C' } }
            ],
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            }
          }
        ]
      }

      ipChart.setOption(option)
    }

    // 更新分配趋势图表
    const updateAllocationTrendChart = (data) => {
      if (!allocationTrendChart.value) return

      if (!trendChart) {
        trendChart = echarts.init(allocationTrendChart.value)
      }

      const dates = data.map(item => item.date)
      const allocations = data.map(item => item.allocations)

      const option = {
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: dates,
          axisLabel: {
            formatter: function(value) {
              return new Date(value).toLocaleDateString()
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '分配数量'
        },
        series: [
          {
            name: 'IP分配',
            type: 'line',
            data: allocations,
            smooth: true,
            itemStyle: {
              color: '#409EFF'
            },
            areaStyle: {
              color: 'rgba(64, 158, 255, 0.1)'
            }
          }
        ]
      }

      trendChart.setOption(option)
    }

    // 获取使用率颜色
    const getUtilizationColor = (rate) => {
      if (rate >= 90) return '#F56C6C'
      if (rate >= 80) return '#E6A23C'
      if (rate >= 60) return '#409EFF'
      return '#67C23A'
    }

    // 获取严重程度类型
    const getSeverityType = (severity) => {
      const types = {
        'low': 'info',
        'medium': 'warning',
        'high': 'danger',
        'critical': 'danger'
      }
      return types[severity] || 'info'
    }

    // 获取严重程度文本
    const getSeverityText = (severity) => {
      const texts = {
        'low': '低',
        'medium': '中',
        'high': '高',
        'critical': '严重'
      }
      return texts[severity] || severity
    }

    // 格式化日期时间
    const formatDateTime = (dateTime) => {
      return new Date(dateTime).toLocaleString()
    }

    // 解决警报
    const resolveAlert = async (alertId) => {
      try {
        await resolveAlertAPI(alertId)
        ElMessage.success('警报已解决')
        loadAlertHistory()
      } catch (error) {
        ElMessage.error('解决警报失败')
        console.error('Resolve alert error:', error)
      }
    }

    // 刷新函数
    const refreshIPStats = () => {
      loadDashboardData()
    }

    const refreshTrends = () => {
      loadAllocationTrends()
    }

    const refreshSubnetStats = () => {
      loadSubnetStats()
    }

    // 显示警报管理
    const showAlertManagement = () => {
      // 这里可以导航到警报管理页面或打开对话框
      ElMessage.info('警报管理功能开发中')
    }

    // 处理报告生成
    const handleReportGenerated = (reportInfo) => {
      ElMessage.success('报告生成请求已提交')
      console.log('Report generated:', reportInfo)
    }

    // 导航功能
    const navigateTo = (path) => {
      router.push(path)
    }

    // 处理用户操作
    const handleUserAction = (command) => {
      switch (command) {
        case 'profile':
          ElMessage.info('个人资料功能开发中')
          break
        case 'logout':
          store.dispatch('auth/logout')
          router.push('/login')
          break
      }
    }

    // 窗口大小变化时重新调整图表
    const handleResize = () => {
      if (ipChart) ipChart.resize()
      if (trendChart) trendChart.resize()
    }

    onMounted(() => {
      loadDashboardData()
      loadSubnetStats()
      loadAllocationTrends()
      loadAlertHistory()

      window.addEventListener('resize', handleResize)
    })

    return {
      loading,
      alertsLoading,
      dashboardData,
      topSubnets,
      recentAlerts,
      trendDays,
      showReportDialog,
      ipUtilizationChart,
      allocationTrendChart,
      currentUser,
      isAdmin,
      getUtilizationColor,
      getSeverityType,
      getSeverityText,
      formatDateTime,
      resolveAlert,
      refreshIPStats,
      refreshTrends,
      refreshSubnetStats,
      showAlertManagement,
      handleReportGenerated,
      navigateTo,
      handleUserAction,
      Network,
      PieChart,
      Grid,
      Warning,
      Refresh,
      Document,
      Setting,
      User,
      ArrowDown
    }
  }
}
</script>

<style scoped>
.monitoring-dashboard {
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.header-left h1 {
  margin: 0 0 5px 0;
  font-size: 24px;
  font-weight: 600;
  color: white;
}

.header-description {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.header-right {
  display: flex;
  align-items: center;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  height: 120px;
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 24px;
  color: white;
}

.ip-icon {
  background: linear-gradient(135deg, #409EFF, #66B1FF);
}

.utilization-icon {
  background: linear-gradient(135deg, #67C23A, #85CE61);
}

.subnet-icon {
  background: linear-gradient(135deg, #E6A23C, #EEBC6C);
}

.alert-icon {
  background: linear-gradient(135deg, #F56C6C, #F78989);
}

.stat-info {
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
  margin-top: 5px;
}

.charts-section {
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
}

.chart-container {
  height: 320px;
}

.table-section,
.alerts-section {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-card,
.alerts-card {
  min-height: 300px;
}

@media (max-width: 768px) {
  .monitoring-dashboard {
    padding: 10px;
  }
  
  .stats-cards .el-col {
    margin-bottom: 10px;
  }
  
  .chart-card {
    height: 300px;
  }
  
  .chart-container {
    height: 220px;
  }
}
</style>