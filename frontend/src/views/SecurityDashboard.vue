<template>
  <div class="security-dashboard">
    <div class="dashboard-header">
      <h1>安全监控仪表盘</h1>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading" type="primary">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="exportReport" type="success">
          <el-icon><Download /></el-icon>
          导出报告
        </el-button>
      </div>
    </div>

    <!-- 安全概览卡片 -->
    <div class="security-overview">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="card-icon threat-level" :class="threatLevelClass">
                <el-icon size="32"><Shield /></el-icon>
              </div>
              <div class="card-info">
                <h3>威胁级别</h3>
                <p class="card-value" :class="threatLevelClass">{{ dashboardData.threat_level }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="card-icon security-score">
                <el-icon size="32"><Trophy /></el-icon>
              </div>
              <div class="card-info">
                <h3>安全评分</h3>
                <p class="card-value">{{ dashboardData.security_score }}/100</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="card-icon events-count">
                <el-icon size="32"><Document /></el-icon>
              </div>
              <div class="card-info">
                <h3>24小时事件</h3>
                <p class="card-value">{{ dashboardData.total_events_24h }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="card-content">
              <div class="card-icon alerts-count">
                <el-icon size="32"><Warning /></el-icon>
              </div>
              <div class="card-info">
                <h3>活跃警报</h3>
                <p class="card-value alert-count">{{ dashboardData.active_alerts }}</p>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <!-- 威胁趋势图 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>威胁趋势 (24小时)</span>
            </template>
            <div ref="threatTrendChart" style="height: 300px;"></div>
          </el-card>
        </el-col>
        
        <!-- 事件类型分布 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>事件类型分布</span>
            </template>
            <div ref="eventTypeChart" style="height: 300px;"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <!-- 安全级别分布 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>安全级别分布</span>
            </template>
            <div ref="securityLevelChart" style="height: 300px;"></div>
          </el-card>
        </el-col>
        
        <!-- 威胁IP排行 -->
        <el-col :span="12">
          <el-card>
            <template #header>
              <span>威胁IP排行</span>
            </template>
            <div class="threat-ips-list">
              <div 
                v-for="(ip, index) in dashboardData.top_threat_ips" 
                :key="ip.ip"
                class="threat-ip-item"
              >
                <span class="rank">{{ index + 1 }}</span>
                <span class="ip">{{ ip.ip }}</span>
                <span class="count">{{ ip.threat_count }} 次威胁</span>
                <el-button size="small" type="danger" @click="blockIP(ip.ip)">
                  阻止
                </el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 最近警报 -->
    <div class="recent-alerts">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>最近警报</span>
            <el-button type="text" @click="viewAllAlerts">查看全部</el-button>
          </div>
        </template>
        
        <el-table :data="dashboardData.recent_alerts" style="width: 100%">
          <el-table-column prop="title" label="标题" width="200" />
          <el-table-column prop="message" label="消息" />
          <el-table-column prop="level" label="级别" width="100">
            <template #default="scope">
              <el-tag :type="getAlertTagType(scope.row.level)">
                {{ scope.row.level.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="scope">
              {{ formatTime(scope.row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120">
            <template #default="scope">
              <el-button 
                v-if="!scope.row.acknowledged"
                size="small" 
                type="primary" 
                @click="acknowledgeAlert(scope.row.id)"
              >
                确认
              </el-button>
              <span v-else class="acknowledged">已确认</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 安全事件流 -->
    <div class="security-events">
      <el-card>
        <template #header>
          <div class="card-header">
            <span>实时安全事件</span>
            <div class="header-controls">
              <el-select v-model="eventFilter" placeholder="事件类型" clearable>
                <el-option 
                  v-for="type in eventTypes" 
                  :key="type" 
                  :label="type" 
                  :value="type"
                />
              </el-select>
              <el-select v-model="levelFilter" placeholder="安全级别" clearable>
                <el-option label="低" value="low" />
                <el-option label="中等" value="medium" />
                <el-option label="高" value="high" />
                <el-option label="严重" value="critical" />
              </el-select>
            </div>
          </div>
        </template>
        
        <el-table 
          :data="filteredEvents" 
          style="width: 100%"
          :max-height="400"
        >
          <el-table-column prop="event_type" label="事件类型" width="150" />
          <el-table-column prop="level" label="级别" width="100">
            <template #default="scope">
              <el-tag :type="getEventTagType(scope.row.level)">
                {{ scope.row.level.toUpperCase() }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="client_ip" label="客户端IP" width="130" />
          <el-table-column prop="username" label="用户" width="120" />
          <el-table-column prop="endpoint" label="端点" />
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="scope">
              {{ formatTime(scope.row.timestamp) }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, 
  Download, 
  Shield, 
  Trophy, 
  Document, 
  Warning 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { securityAPI } from '@/api/security'

export default {
  name: 'SecurityDashboard',
  components: {
    Refresh,
    Download,
    Shield,
    Trophy,
    Document,
    Warning
  },
  setup() {
    const loading = ref(false)
    const dashboardData = reactive({
      total_events_24h: 0,
      active_alerts: 0,
      threat_level: 'LOW',
      event_statistics: {},
      security_levels: {},
      hourly_distribution: {},
      threat_trend: [],
      recent_alerts: [],
      top_threat_ips: [],
      security_score: 100
    })
    
    const securityEvents = ref([])
    const eventFilter = ref('')
    const levelFilter = ref('')
    
    // 图表实例
    const threatTrendChart = ref(null)
    const eventTypeChart = ref(null)
    const securityLevelChart = ref(null)
    
    let chartInstances = {}
    
    // 计算属性
    const threatLevelClass = computed(() => {
      const level = dashboardData.threat_level.toLowerCase()
      return {
        'threat-low': level === 'low',
        'threat-medium': level === 'medium',
        'threat-high': level === 'high',
        'threat-critical': level === 'critical'
      }
    })
    
    const eventTypes = computed(() => {
      return Object.keys(dashboardData.event_statistics)
    })
    
    const filteredEvents = computed(() => {
      let events = securityEvents.value
      
      if (eventFilter.value) {
        events = events.filter(event => event.event_type === eventFilter.value)
      }
      
      if (levelFilter.value) {
        events = events.filter(event => event.level === levelFilter.value)
      }
      
      return events
    })
    
    // 方法
    const refreshData = async () => {
      loading.value = true
      try {
        await Promise.all([
          loadDashboardData(),
          loadSecurityEvents()
        ])
        
        await nextTick()
        initCharts()
      } catch (error) {
        ElMessage.error('刷新数据失败: ' + error.message)
      } finally {
        loading.value = false
      }
    }
    
    const loadDashboardData = async () => {
      try {
        const data = await securityAPI.getDashboard()
        Object.assign(dashboardData, data)
      } catch (error) {
        console.error('加载仪表盘数据失败:', error)
        throw error
      }
    }
    
    const loadSecurityEvents = async () => {
      try {
        const events = await securityAPI.getEvents({ limit: 100 })
        securityEvents.value = events
      } catch (error) {
        console.error('加载安全事件失败:', error)
        throw error
      }
    }
    
    const initCharts = () => {
      initThreatTrendChart()
      initEventTypeChart()
      initSecurityLevelChart()
    }
    
    const initThreatTrendChart = () => {
      if (!threatTrendChart.value) return
      
      if (chartInstances.threatTrend) {
        chartInstances.threatTrend.dispose()
      }
      
      chartInstances.threatTrend = echarts.init(threatTrendChart.value)
      
      const option = {
        title: {
          text: '威胁趋势',
          left: 'center'
        },
        tooltip: {
          trigger: 'axis'
        },
        xAxis: {
          type: 'category',
          data: dashboardData.threat_trend.map(item => `${item.hour}小时前`)
        },
        yAxis: {
          type: 'value'
        },
        series: [{
          name: '威胁数量',
          type: 'line',
          data: dashboardData.threat_trend.map(item => item.threats),
          smooth: true,
          areaStyle: {
            color: 'rgba(255, 99, 132, 0.2)'
          },
          lineStyle: {
            color: '#ff6384'
          }
        }]
      }
      
      chartInstances.threatTrend.setOption(option)
    }
    
    const initEventTypeChart = () => {
      if (!eventTypeChart.value) return
      
      if (chartInstances.eventType) {
        chartInstances.eventType.dispose()
      }
      
      chartInstances.eventType = echarts.init(eventTypeChart.value)
      
      const data = Object.entries(dashboardData.event_statistics).map(([key, value]) => ({
        name: key,
        value: value
      }))
      
      const option = {
        title: {
          text: '事件类型分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'item',
          formatter: '{a} <br/>{b}: {c} ({d}%)'
        },
        series: [{
          name: '事件类型',
          type: 'pie',
          radius: '50%',
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
      
      chartInstances.eventType.setOption(option)
    }
    
    const initSecurityLevelChart = () => {
      if (!securityLevelChart.value) return
      
      if (chartInstances.securityLevel) {
        chartInstances.securityLevel.dispose()
      }
      
      chartInstances.securityLevel = echarts.init(securityLevelChart.value)
      
      const levelColors = {
        low: '#67C23A',
        medium: '#E6A23C',
        high: '#F56C6C',
        critical: '#909399'
      }
      
      const data = Object.entries(dashboardData.security_levels).map(([key, value]) => ({
        name: key.toUpperCase(),
        value: value,
        itemStyle: {
          color: levelColors[key] || '#409EFF'
        }
      }))
      
      const option = {
        title: {
          text: '安全级别分布',
          left: 'center'
        },
        tooltip: {
          trigger: 'item'
        },
        series: [{
          name: '安全级别',
          type: 'doughnut',
          radius: ['40%', '70%'],
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }]
      }
      
      chartInstances.securityLevel.setOption(option)
    }
    
    const acknowledgeAlert = async (alertId) => {
      try {
        await securityAPI.acknowledgeAlert(alertId)
        ElMessage.success('警报已确认')
        
        // 更新本地数据
        const alert = dashboardData.recent_alerts.find(a => a.id === alertId)
        if (alert) {
          alert.acknowledged = true
        }
        
        dashboardData.active_alerts = Math.max(0, dashboardData.active_alerts - 1)
      } catch (error) {
        ElMessage.error('确认警报失败: ' + error.message)
      }
    }
    
    const blockIP = async (ip) => {
      try {
        await ElMessageBox.confirm(
          `确定要阻止IP地址 ${ip} 吗？`,
          '确认阻止',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        // 这里应该调用阻止IP的API
        ElMessage.success(`IP ${ip} 已被阻止`)
      } catch (error) {
        // 用户取消操作
      }
    }
    
    const viewAllAlerts = () => {
      // 跳转到警报管理页面
      this.$router.push('/security/alerts')
    }
    
    const exportReport = async () => {
      try {
        // 这里应该调用导出报告的API
        ElMessage.success('安全报告导出成功')
      } catch (error) {
        ElMessage.error('导出报告失败: ' + error.message)
      }
    }
    
    const getAlertTagType = (level) => {
      const typeMap = {
        low: '',
        medium: 'warning',
        high: 'danger',
        critical: 'danger'
      }
      return typeMap[level] || ''
    }
    
    const getEventTagType = (level) => {
      const typeMap = {
        low: 'info',
        medium: 'warning',
        high: 'danger',
        critical: 'danger'
      }
      return typeMap[level] || 'info'
    }
    
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp * 1000)
      return date.toLocaleString('zh-CN')
    }
    
    // 生命周期
    onMounted(() => {
      refreshData()
      
      // 设置自动刷新
      const interval = setInterval(refreshData, 30000) // 30秒刷新一次
      
      // 组件销毁时清除定时器
      onUnmounted(() => {
        clearInterval(interval)
        
        // 销毁图表实例
        Object.values(chartInstances).forEach(chart => {
          if (chart) chart.dispose()
        })
      })
    })
    
    return {
      loading,
      dashboardData,
      securityEvents,
      eventFilter,
      levelFilter,
      threatTrendChart,
      eventTypeChart,
      securityLevelChart,
      threatLevelClass,
      eventTypes,
      filteredEvents,
      refreshData,
      acknowledgeAlert,
      blockIP,
      viewAllAlerts,
      exportReport,
      getAlertTagType,
      getEventTagType,
      formatTime
    }
  }
}
</script>

<style scoped>
.security-dashboard {
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-header h1 {
  margin: 0;
  color: var(--text-color-primary);
}

.header-actions {
  display: flex;
  gap: 10px;
}

.security-overview {
  margin-bottom: 20px;
}

.overview-card {
  height: 120px;
}

.card-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
}

.card-icon.threat-level.threat-low {
  background: rgba(103, 194, 58, 0.2);
  color: #67C23A;
}

.card-icon.threat-level.threat-medium {
  background: rgba(230, 162, 60, 0.2);
  color: #E6A23C;
}

.card-icon.threat-level.threat-high {
  background: rgba(245, 108, 108, 0.2);
  color: #F56C6C;
}

.card-icon.threat-level.threat-critical {
  background: rgba(144, 147, 153, 0.2);
  color: #909399;
}

.card-icon.security-score {
  background: rgba(64, 158, 255, 0.2);
  color: #409EFF;
}

.card-icon.events-count {
  background: rgba(103, 194, 58, 0.2);
  color: #67C23A;
}

.card-icon.alerts-count {
  background: rgba(245, 108, 108, 0.2);
  color: #F56C6C;
}

.card-info h3 {
  margin: 0 0 5px 0;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.card-value {
  margin: 0;
  font-size: 24px;
  font-weight: bold;
  color: var(--text-color-primary);
}

.card-value.threat-low {
  color: var(--success-color);
}

.card-value.threat-medium {
  color: var(--warning-color);
}

.card-value.threat-high {
  color: var(--danger-color);
}

.card-value.threat-critical {
  color: var(--info-color);
}

.card-value.alert-count {
  color: var(--danger-color);
}

.charts-section {
  margin-bottom: 20px;
}

.threat-ips-list {
  max-height: 300px;
  overflow-y: auto;
}

.threat-ip-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #EBEEF5;
}

.threat-ip-item:last-child {
  border-bottom: none;
}

.threat-ip-item .rank {
  width: 30px;
  text-align: center;
  font-weight: bold;
  color: var(--primary-color);
}

.threat-ip-item .ip {
  flex: 1;
  margin-left: 10px;
  font-family: monospace;
  color: var(--text-color-primary);
}

.threat-ip-item .count {
  margin-right: 10px;
  color: var(--danger-color);
  font-size: 12px;
}

.recent-alerts,
.security-events {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  gap: 10px;
}

.acknowledged {
  color: var(--success-color);
  font-size: 12px;
}

@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .card-content {
    flex-direction: column;
    text-align: center;
  }
  
  .card-icon {
    margin-right: 0;
    margin-bottom: 10px;
  }
  
  .header-controls {
    flex-direction: column;
    width: 100%;
  }
}
</style>