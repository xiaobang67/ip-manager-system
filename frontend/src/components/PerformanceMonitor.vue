<template>
  <div class="performance-monitor">
    <el-card class="monitor-card">
      <template #header>
        <div class="card-header">
          <span>性能监控</span>
          <div class="header-actions">
            <el-switch
              v-model="monitorEnabled"
              active-text="启用"
              inactive-text="禁用"
              @change="toggleMonitoring"
            />
            <el-button 
              size="small" 
              @click="clearMetrics"
              :disabled="!monitorEnabled"
            >
              清除数据
            </el-button>
            <el-button 
              size="small" 
              type="primary"
              @click="exportMetrics"
              :disabled="!monitorEnabled"
            >
              导出数据
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- 实时性能指标 -->
      <div class="metrics-grid">
        <div class="metric-item">
          <div class="metric-label">页面加载时间</div>
          <div class="metric-value">{{ formatTime(pageLoadTime) }}</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">API平均响应时间</div>
          <div class="metric-value">{{ formatTime(avgApiResponseTime) }}</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">内存使用</div>
          <div class="metric-value">{{ formatMemory(memoryUsage) }}</div>
        </div>
        
        <div class="metric-item">
          <div class="metric-label">缓存命中率</div>
          <div class="metric-value">{{ formatPercent(cacheHitRate) }}</div>
        </div>
      </div>
      
      <!-- 性能图表 -->
      <div class="charts-container">
        <div class="chart-item">
          <h4>API响应时间趋势</h4>
          <div ref="apiResponseChart" class="chart"></div>
        </div>
        
        <div class="chart-item">
          <h4>内存使用趋势</h4>
          <div ref="memoryChart" class="chart"></div>
        </div>
      </div>
      
      <!-- 慢请求列表 -->
      <div class="slow-requests">
        <h4>慢请求记录</h4>
        <el-table 
          :data="slowRequests" 
          size="small"
          max-height="300"
        >
          <el-table-column prop="url" label="请求URL" width="300" />
          <el-table-column prop="method" label="方法" width="80" />
          <el-table-column prop="duration" label="耗时(ms)" width="100" />
          <el-table-column prop="timestamp" label="时间" width="150" />
          <el-table-column prop="status" label="状态" width="80" />
        </el-table>
      </div>
      
      <!-- 性能建议 -->
      <div class="performance-suggestions" v-if="suggestions.length > 0">
        <h4>性能优化建议</h4>
        <el-alert
          v-for="(suggestion, index) in suggestions"
          :key="index"
          :title="suggestion.title"
          :description="suggestion.description"
          :type="suggestion.type"
          show-icon
          class="suggestion-item"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getCacheStats } from '@/utils/apiOptimizer'

export default {
  name: 'PerformanceMonitor',
  setup() {
    const monitorEnabled = ref(true)
    const pageLoadTime = ref(0)
    const apiResponseTimes = ref([])
    const memoryUsages = ref([])
    const slowRequests = ref([])
    const cacheStats = ref({ hitRate: 0 })
    
    // 图表实例
    const apiResponseChart = ref(null)
    const memoryChart = ref(null)
    let apiChart = null
    let memChart = null
    
    // 性能观察器
    let performanceObserver = null
    let memoryMonitorInterval = null
    let apiMonitorInterval = null
    
    // 计算属性
    const avgApiResponseTime = computed(() => {
      if (apiResponseTimes.value.length === 0) return 0
      const sum = apiResponseTimes.value.reduce((acc, time) => acc + time.value, 0)
      return sum / apiResponseTimes.value.length
    })
    
    const memoryUsage = computed(() => {
      if (memoryUsages.value.length === 0) return 0
      return memoryUsages.value[memoryUsages.value.length - 1]?.value || 0
    })
    
    const cacheHitRate = computed(() => {
      return cacheStats.value.hitRate || 0
    })
    
    const suggestions = computed(() => {
      const suggestions = []
      
      // 检查API响应时间
      if (avgApiResponseTime.value > 2000) {
        suggestions.push({
          title: 'API响应时间过慢',
          description: `平均响应时间为 ${formatTime(avgApiResponseTime.value)}，建议优化后端查询或启用缓存`,
          type: 'warning'
        })
      }
      
      // 检查内存使用
      if (memoryUsage.value > 100 * 1024 * 1024) { // 100MB
        suggestions.push({
          title: '内存使用过高',
          description: `当前内存使用 ${formatMemory(memoryUsage.value)}，建议检查内存泄漏或优化数据结构`,
          type: 'error'
        })
      }
      
      // 检查缓存命中率
      if (cacheHitRate.value < 0.5) {
        suggestions.push({
          title: '缓存命中率较低',
          description: `当前缓存命中率为 ${formatPercent(cacheHitRate.value)}，建议调整缓存策略`,
          type: 'info'
        })
      }
      
      // 检查慢请求
      if (slowRequests.value.length > 10) {
        suggestions.push({
          title: '慢请求过多',
          description: `发现 ${slowRequests.value.length} 个慢请求，建议优化相关接口`,
          type: 'warning'
        })
      }
      
      return suggestions
    })
    
    // 初始化性能监控
    const initPerformanceMonitoring = () => {
      // 页面加载时间
      if (window.performance && window.performance.timing) {
        const timing = window.performance.timing
        pageLoadTime.value = timing.loadEventEnd - timing.navigationStart
      }
      
      // Performance Observer
      if (window.PerformanceObserver) {
        performanceObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'navigation') {
              pageLoadTime.value = entry.loadEventEnd - entry.fetchStart
            } else if (entry.entryType === 'measure') {
              // 自定义性能测量

            }
          }
        })
        
        try {
          performanceObserver.observe({ entryTypes: ['navigation', 'measure'] })
        } catch (e) {

        }
      }
      
      // 监控API请求
      monitorApiRequests()
      
      // 监控内存使用
      monitorMemoryUsage()
      
      // 监控缓存统计
      monitorCacheStats()
    }
    
    // 监控API请求
    const monitorApiRequests = () => {
      // 拦截fetch请求
      const originalFetch = window.fetch
      window.fetch = function(...args) {
        const startTime = Date.now()
        const url = args[0]
        
        return originalFetch.apply(this, args)
          .then(response => {
            const duration = Date.now() - startTime
            recordApiRequest(url, 'GET', duration, response.status)
            return response
          })
          .catch(error => {
            const duration = Date.now() - startTime
            recordApiRequest(url, 'GET', duration, 0)
            throw error
          })
      }
      
      // 拦截XMLHttpRequest
      const originalXHROpen = XMLHttpRequest.prototype.open
      const originalXHRSend = XMLHttpRequest.prototype.send
      
      XMLHttpRequest.prototype.open = function(method, url, ...args) {
        this._method = method
        this._url = url
        this._startTime = Date.now()
        return originalXHROpen.apply(this, [method, url, ...args])
      }
      
      XMLHttpRequest.prototype.send = function(...args) {
        this.addEventListener('loadend', () => {
          const duration = Date.now() - this._startTime
          recordApiRequest(this._url, this._method, duration, this.status)
        })
        return originalXHRSend.apply(this, args)
      }
    }
    
    // 记录API请求
    const recordApiRequest = (url, method, duration, status) => {
      if (!monitorEnabled.value) return
      
      const timestamp = new Date().toLocaleTimeString()
      
      // 记录响应时间
      apiResponseTimes.value.push({
        time: timestamp,
        value: duration
      })
      
      // 保持最近100条记录
      if (apiResponseTimes.value.length > 100) {
        apiResponseTimes.value.shift()
      }
      
      // 记录慢请求
      if (duration > 2000) {
        slowRequests.value.unshift({
          url: url.length > 50 ? url.substring(0, 50) + '...' : url,
          method,
          duration,
          timestamp,
          status
        })
        
        // 保持最近50条慢请求记录
        if (slowRequests.value.length > 50) {
          slowRequests.value.pop()
        }
      }
      
      // 更新图表
      updateApiChart()
    }
    
    // 监控内存使用
    const monitorMemoryUsage = () => {
      memoryMonitorInterval = setInterval(() => {
        if (!monitorEnabled.value) return
        
        if (window.performance && window.performance.memory) {
          const memory = window.performance.memory
          const timestamp = new Date().toLocaleTimeString()
          
          memoryUsages.value.push({
            time: timestamp,
            value: memory.usedJSHeapSize
          })
          
          // 保持最近100条记录
          if (memoryUsages.value.length > 100) {
            memoryUsages.value.shift()
          }
          
          updateMemoryChart()
        }
      }, 5000) // 每5秒检查一次
    }
    
    // 监控缓存统计
    const monitorCacheStats = () => {
      apiMonitorInterval = setInterval(() => {
        if (!monitorEnabled.value) return
        
        try {
          cacheStats.value = getCacheStats()
        } catch (error) {

        }
      }, 10000) // 每10秒检查一次
    }
    
    // 初始化图表
    const initCharts = () => {
      nextTick(() => {
        if (apiResponseChart.value) {
          apiChart = echarts.init(apiResponseChart.value)
          updateApiChart()
        }
        
        if (memoryChart.value) {
          memChart = echarts.init(memoryChart.value)
          updateMemoryChart()
        }
      })
    }
    
    // 更新API响应时间图表
    const updateApiChart = () => {
      if (!apiChart) return
      
      const option = {
        title: {
          text: 'API响应时间',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          formatter: '{b}: {c}ms'
        },
        xAxis: {
          type: 'category',
          data: apiResponseTimes.value.map(item => item.time),
          axisLabel: { fontSize: 10 }
        },
        yAxis: {
          type: 'value',
          name: '响应时间(ms)',
          axisLabel: { fontSize: 10 }
        },
        series: [{
          data: apiResponseTimes.value.map(item => item.value),
          type: 'line',
          smooth: true,
          lineStyle: { color: '#409EFF' },
          areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
        }],
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%',
          top: '20%'
        }
      }
      
      apiChart.setOption(option)
    }
    
    // 更新内存使用图表
    const updateMemoryChart = () => {
      if (!memChart) return
      
      const option = {
        title: {
          text: '内存使用',
          textStyle: { fontSize: 14 }
        },
        tooltip: {
          trigger: 'axis',
          formatter: (params) => {
            const value = params[0].value
            return `${params[0].name}: ${formatMemory(value)}`
          }
        },
        xAxis: {
          type: 'category',
          data: memoryUsages.value.map(item => item.time),
          axisLabel: { fontSize: 10 }
        },
        yAxis: {
          type: 'value',
          name: '内存(MB)',
          axisLabel: { 
            fontSize: 10,
            formatter: (value) => (value / 1024 / 1024).toFixed(1) + 'MB'
          }
        },
        series: [{
          data: memoryUsages.value.map(item => item.value),
          type: 'line',
          smooth: true,
          lineStyle: { color: '#67C23A' },
          areaStyle: { color: 'rgba(103, 194, 58, 0.1)' }
        }],
        grid: {
          left: '10%',
          right: '10%',
          bottom: '15%',
          top: '20%'
        }
      }
      
      memChart.setOption(option)
    }
    
    // 切换监控状态
    const toggleMonitoring = (enabled) => {
      if (enabled) {
        initPerformanceMonitoring()
      } else {
        stopMonitoring()
      }
    }
    
    // 停止监控
    const stopMonitoring = () => {
      if (performanceObserver) {
        performanceObserver.disconnect()
      }
      
      if (memoryMonitorInterval) {
        clearInterval(memoryMonitorInterval)
      }
      
      if (apiMonitorInterval) {
        clearInterval(apiMonitorInterval)
      }
    }
    
    // 清除指标数据
    const clearMetrics = () => {
      apiResponseTimes.value = []
      memoryUsages.value = []
      slowRequests.value = []
      pageLoadTime.value = 0
      
      updateApiChart()
      updateMemoryChart()
    }
    
    // 导出指标数据
    const exportMetrics = () => {
      const data = {
        timestamp: new Date().toISOString(),
        pageLoadTime: pageLoadTime.value,
        apiResponseTimes: apiResponseTimes.value,
        memoryUsages: memoryUsages.value,
        slowRequests: slowRequests.value,
        cacheStats: cacheStats.value,
        avgApiResponseTime: avgApiResponseTime.value,
        suggestions: suggestions.value
      }
      
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `performance-metrics-${Date.now()}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
    
    // 格式化时间
    const formatTime = (ms) => {
      if (ms < 1000) return `${ms.toFixed(0)}ms`
      return `${(ms / 1000).toFixed(2)}s`
    }
    
    // 格式化内存
    const formatMemory = (bytes) => {
      if (bytes < 1024) return `${bytes}B`
      if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
      return `${(bytes / 1024 / 1024).toFixed(1)}MB`
    }
    
    // 格式化百分比
    const formatPercent = (ratio) => {
      return `${(ratio * 100).toFixed(1)}%`
    }
    
    onMounted(() => {
      if (monitorEnabled.value) {
        initPerformanceMonitoring()
      }
      initCharts()
    })
    
    onUnmounted(() => {
      stopMonitoring()
      
      if (apiChart) {
        apiChart.dispose()
      }
      
      if (memChart) {
        memChart.dispose()
      }
    })
    
    return {
      monitorEnabled,
      pageLoadTime,
      avgApiResponseTime,
      memoryUsage,
      cacheHitRate,
      slowRequests,
      suggestions,
      apiResponseChart,
      memoryChart,
      toggleMonitoring,
      clearMetrics,
      exportMetrics,
      formatTime,
      formatMemory,
      formatPercent
    }
  }
}
</script>

<style scoped>
.performance-monitor {
  padding: 20px;
}

.monitor-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.metric-item {
  text-align: center;
  padding: 20px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.metric-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-color-primary);
}

.charts-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.chart-item h4 {
  margin-bottom: 10px;
  color: var(--el-text-color-primary);
}

.chart {
  height: 300px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
}

.slow-requests {
  margin-bottom: 30px;
}

.slow-requests h4 {
  margin-bottom: 15px;
  color: var(--el-text-color-primary);
}

.performance-suggestions h4 {
  margin-bottom: 15px;
  color: var(--el-text-color-primary);
}

.suggestion-item {
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
}
</style>