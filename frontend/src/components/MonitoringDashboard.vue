<template>
  <div class="monitoring-dashboard">

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon ip-icon">
              <el-icon><Connection /></el-icon>
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
            <el-table-column prop="allocated_ips" label="使用中" width="100"></el-table-column>
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
import { Connection, PieChart, Grid, Warning, Refresh, Document, Setting, User, ArrowDown } from '@element-plus/icons-vue'
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
    ReportGenerationDialog,
    Connection,
    PieChart,
    Grid,
    Warning,
    Refresh,
    Document,
    Setting,
    User,
    ArrowDown
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
    const isAdmin = computed(() => store.getters['auth/userRole']?.toLowerCase() === 'admin')

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
        Object.assign(dashboardData, response)
        
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
        topSubnets.value = response
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
        if (response && Array.isArray(response)) {

          updateAllocationTrendChart(response)
        } else {
          console.error('Invalid response data:', response)
          ElMessage.error('分配趋势数据格式错误')
        }
      } catch (error) {
        console.error('Allocation trends error:', error)
        ElMessage.error(`加载分配趋势失败: ${error.message || error}`)
      }
    }

    // 加载警报历史
    const loadAlertHistory = async () => {
      alertsLoading.value = true
      try {
        const response = await getAlertHistory({ limit: 10 })
        recentAlerts.value = response
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
              { value: stats.allocated_ips, name: '使用中', itemStyle: { color: '#409EFF' } },
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
      Connection,
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
  padding: 0;
  background: transparent;
}

/* 统计卡片样式 */
.stats-cards {
  margin-bottom: 30px;
}

.stat-card {
  height: 140px;
  border-radius: 20px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
  position: relative;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
}

.stat-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.stat-icon {
  width: 70px;
  height: 70px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 28px;
  color: white;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.05) rotate(5deg);
}

.ip-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.utilization-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.subnet-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.alert-icon {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 800;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 15px;
  color: #7f8c8d;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 图表区域样式 */
.charts-section {
  margin-bottom: 30px;
}

.chart-card {
  height: 450px;
  border-radius: 20px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
}

.chart-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.15);
}

.chart-card .el-card__header {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  padding: 20px 25px;
}

.chart-container {
  height: 350px;
  padding: 10px;
}

/* 表格和警报区域样式 */
.table-section,
.alerts-section {
  margin-bottom: 30px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #2c3e50;
  font-size: 16px;
}

.card-header span {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.table-card,
.alerts-card {
  min-height: 350px;
  border-radius: 20px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  overflow: hidden;
}

.table-card:hover,
.alerts-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.15);
}

.table-card .el-card__header,
.alerts-card .el-card__header {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
  padding: 20px 25px;
}

/* 表格样式优化 */
.table-card .el-table,
.alerts-card .el-table {
  background: transparent;
  border-radius: 12px;
  overflow: hidden;
}

.table-card .el-table th,
.alerts-card .el-table th {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  color: #2c3e50;
  font-weight: 600;
  border: none;
}

.table-card .el-table td,
.alerts-card .el-table td {
  border: none;
  border-bottom: 1px solid rgba(102, 126, 234, 0.1);
}

.table-card .el-table tbody tr:hover td,
.alerts-card .el-table tbody tr:hover td {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

/* 按钮样式优化 */
.card-header .el-button {
  border-radius: 10px;
  transition: all 0.3s ease;
}

.card-header .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.card-header .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.card-header .el-button--text {
  color: #667eea;
  border-radius: 8px;
  padding: 8px 12px;
}

.card-header .el-button--text:hover {
  background: rgba(102, 126, 234, 0.1);
  color: #764ba2;
}

/* 进度条样式优化 */
.el-progress {
  margin: 0;
}

.el-progress__text {
  font-weight: 600;
  color: #2c3e50;
}

.el-progress-bar__outer {
  background-color: rgba(102, 126, 234, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.el-progress-bar__inner {
  border-radius: 10px;
  transition: all 0.4s ease;
}

/* 标签样式优化 */
.el-tag {
  border-radius: 8px;
  font-weight: 600;
  border: none;
  padding: 4px 12px;
}

.el-tag--success {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  color: white;
}

.el-tag--warning {
  background: linear-gradient(135deg, #e6a23c 0%, #eebc6c 100%);
  color: white;
}

.el-tag--danger {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
  color: white;
}

.el-tag--info {
  background: linear-gradient(135deg, #909399 0%, #a6a9ad 100%);
  color: white;
}

/* 下拉选择器样式优化 */
.el-select {
  border-radius: 8px;
}

.el-select .el-input__wrapper {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.el-select .el-input__wrapper:hover {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

/* 加载动画优化 */
.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(4px);
}

.el-loading-spinner {
  color: #667eea;
}

/* 滚动条样式 */
.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 4px;
  transition: background 0.3s ease;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}

/* 动画关键帧 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 为卡片添加入场动画 */
.stat-card {
  animation: fadeInUp 0.6s ease-out;
}

.stat-card:nth-child(1) { animation-delay: 0.1s; }
.stat-card:nth-child(2) { animation-delay: 0.2s; }
.stat-card:nth-child(3) { animation-delay: 0.3s; }
.stat-card:nth-child(4) { animation-delay: 0.4s; }

.chart-card,
.table-card,
.alerts-card {
  animation: fadeInUp 0.8s ease-out;
}

.nav-item {
  animation: slideInLeft 0.5s ease-out;
}

.nav-item:nth-child(1) { animation-delay: 0.1s; }
.nav-item:nth-child(2) { animation-delay: 0.2s; }
.nav-item:nth-child(3) { animation-delay: 0.3s; }
.nav-item:nth-child(4) { animation-delay: 0.4s; }

/* 按钮颜色统一样式 */
.btn-allocation, .btn-edit {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: white !important;
}

.btn-allocation:hover, .btn-edit:hover {
  background-color: #66b1ff !important;
  border-color: #66b1ff !important;
}

.btn-reservation, .btn-sync {
  background-color: #e6a23c !important;
  border-color: #e6a23c !important;
  color: white !important;
}

.btn-reservation:hover, .btn-sync:hover {
  background-color: #ebb563 !important;
  border-color: #ebb563 !important;
}

.btn-release, .btn-delete {
  background-color: #f56c6c !important;
  border-color: #f56c6c !important;
  color: white !important;
}

.btn-release:hover, .btn-delete:hover {
  background-color: #f78989 !important;
  border-color: #f78989 !important;
}

.btn-history, .btn-view {
  background-color: #909399 !important;
  border-color: #909399 !important;
  color: white !important;
}

.btn-history:hover, .btn-view:hover {
  background-color: #a6a9ad !important;
  border-color: #a6a9ad !important;
}

/* 暗黑主题适配 */
.dark .btn-allocation, .dark .btn-edit,
.dark .btn-reservation, .dark .btn-sync,
.dark .btn-release, .dark .btn-delete,
.dark .btn-history, .dark .btn-view {
  opacity: 0.9;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .sidebar-navigation {
    width: 260px;
  }
  
  .nav-header {
    padding: 30px 20px 20px;
  }
  
  .nav-item {
    padding: 15px 20px;
    margin: 6px 12px;
  }
  
  .main-content {
    padding: 25px;
  }
  
  .stat-card {
    height: 130px;
  }
  
  .stat-icon {
    width: 65px;
    height: 65px;
    font-size: 26px;
  }
  
  .stat-value {
    font-size: 30px;
  }
}

@media (max-width: 768px) {
  .monitoring-dashboard {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  }
  
  .dashboard-content {
    flex-direction: column;
  }
  
  .sidebar-navigation {
    width: 100%;
    height: auto;
    flex-direction: row;
    overflow-x: auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }
  
  .nav-header {
    min-width: 220px;
    padding: 20px;
    border-bottom: none;
    border-right: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  .nav-header h2 {
    font-size: 18px;
  }
  
  .nav-description {
    font-size: 12px;
  }
  
  .nav-menu {
    display: flex;
    padding: 0;
    min-width: 400px;
    align-items: center;
  }
  
  .nav-item {
    flex-direction: column;
    padding: 20px 15px;
    min-width: 90px;
    text-align: center;
    margin: 10px 8px;
    border-radius: 12px;
  }
  
  .nav-item:hover {
    transform: translateY(-4px);
  }
  
  .nav-icon {
    margin-right: 0;
    margin-bottom: 8px;
    font-size: 18px;
  }
  
  .nav-text {
    font-size: 13px;
    font-weight: 600;
  }
  
  .user-section {
    min-width: 180px;
    padding: 20px;
    border-top: none;
    border-left: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  .main-content {
    padding: 20px;
  }
  
  .stats-cards {
    margin-bottom: 25px;
  }
  
  .stats-cards .el-col {
    margin-bottom: 15px;
  }
  
  .stat-card {
    height: 120px;
  }
  
  .stat-content {
    padding: 15px;
  }
  
  .stat-icon {
    width: 60px;
    height: 60px;
    font-size: 24px;
    margin-right: 15px;
  }
  
  .stat-value {
    font-size: 28px;
  }
  
  .stat-label {
    font-size: 14px;
  }
  
  .chart-card {
    height: 350px;
    margin-bottom: 20px;
  }
  
  .chart-container {
    height: 270px;
  }
  
  .table-card,
  .alerts-card {
    min-height: 300px;
  }
}

@media (max-width: 480px) {
  .sidebar-navigation {
    flex-direction: column;
    height: auto;
  }
  
  .nav-header {
    width: 100%;
    min-width: auto;
    padding: 20px;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  .nav-header h2 {
    font-size: 16px;
  }
  
  .nav-description {
    font-size: 11px;
  }
  
  .nav-menu {
    width: 100%;
    min-width: auto;
    flex-wrap: wrap;
    justify-content: center;
    padding: 15px 0;
  }
  
  .nav-item {
    min-width: 70px;
    padding: 15px 10px;
    margin: 5px;
  }
  
  .nav-text {
    font-size: 11px;
  }
  
  .user-section {
    width: 100%;
    min-width: auto;
    padding: 15px 20px;
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  .main-content {
    padding: 15px;
  }
  
  .stats-cards .el-col {
    margin-bottom: 12px;
  }
  
  .stat-card {
    height: 110px;
  }
  
  .stat-content {
    padding: 12px;
  }
  
  .stat-icon {
    width: 50px;
    height: 50px;
    font-size: 20px;
    margin-right: 12px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .stat-label {
    font-size: 12px;
  }
  
  .chart-card {
    height: 300px;
  }
  
  .chart-container {
    height: 220px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .card-header span {
    font-size: 14px;
  }
}
</style>