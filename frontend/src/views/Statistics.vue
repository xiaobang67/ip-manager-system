<template>
  <div class="statistics-container">
    <el-card class="page-header">
      <h1>统计报表</h1>
      <p>系统统计信息和数据分析</p>
    </el-card>

    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="32"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ ipStats.total }}</div>
              <div class="stat-label">总IP数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="32"><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ ipStats.allocated }}</div>
              <div class="stat-label">已分配IP</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="32"><Lock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ ipStats.reserved }}</div>
              <div class="stat-label">保留IP</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-item">
            <div class="stat-icon">
              <el-icon size="32"><OfficeBuilding /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ orgStats.departments }}</div>
              <div class="stat-label">部门数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="charts-row">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>IP使用率统计</span>
            </div>
          </template>
          <div class="chart-placeholder">
            <p>图表功能开发中...</p>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>网段分布图</span>
            </div>
          </template>
          <div class="chart-placeholder">
            <p>图表功能开发中...</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { DataAnalysis, Connection, Lock, OfficeBuilding } from '@element-plus/icons-vue'

// 响应式数据
const ipStats = ref({
  total: 0,
  allocated: 0,
  available: 0,
  reserved: 0
})

const orgStats = ref({
  departments: 0,
  users: 0
})

// 加载统计数据
const loadStatistics = async () => {
  try {
    // TODO: 调用API获取真实统计数据
    // 这里使用模拟数据
    ipStats.value = {
      total: 1000,
      allocated: 750,
      available: 200,
      reserved: 50
    }
    
    orgStats.value = {
      departments: 15,
      users: 120
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 10px 0;
  color: #303133;
}

.page-header p {
  margin: 0;
  color: #909399;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  padding: 10px;
}

.stat-icon {
  margin-right: 15px;
  color: #409EFF;
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
  margin-top: 5px;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  height: 400px;
}

.card-header {
  display: flex;
  justify-content: between;
  align-items: center;
}

.chart-placeholder {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #909399;
  font-size: 16px;
}
</style>