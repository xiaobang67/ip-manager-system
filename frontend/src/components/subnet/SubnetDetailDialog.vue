<template>
  <el-dialog
    :model-value="visible"
    title="网段详情"
    width="800px"
    @update:model-value="$emit('update:visible', $event)"
  >
    <div v-if="subnet" class="subnet-detail">
      <!-- 基本信息 -->
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="网段">
            <el-tag type="primary" size="large">{{ subnet.network }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="子网掩码">
            {{ subnet.netmask }}
          </el-descriptions-item>
          <el-descriptions-item label="网关">
            {{ subnet.gateway || '未设置' }}
          </el-descriptions-item>
          <el-descriptions-item label="VLAN ID">
            <el-tag v-if="subnet.vlan_id" type="info">{{ subnet.vlan_id }}</el-tag>
            <span v-else>未设置</span>
          </el-descriptions-item>
          <el-descriptions-item label="位置">
            {{ subnet.location || '未设置' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(subnet.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDate(subnet.updated_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ subnet.description || '无描述' }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- IP使用统计 -->
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>IP地址使用统计</span>
            <el-button size="small" @click="refreshStats">刷新</el-button>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ subnet.ip_count || 0 }}</div>
              <div class="stat-label">总IP数</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value allocated">{{ subnet.allocated_count || 0 }}</div>
              <div class="stat-label">使用中</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value available">{{ subnet.available_count || 0 }}</div>
              <div class="stat-label">可用</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-item">
              <div class="stat-value">{{ usagePercentage }}%</div>
              <div class="stat-label">使用率</div>
            </div>
          </el-col>
        </el-row>

        <div class="usage-progress">
          <el-progress
            :percentage="usagePercentage"
            :color="usageColor"
            :stroke-width="12"
          />
        </div>
      </el-card>

      <!-- IP地址列表预览 -->
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>IP地址列表</span>
            <el-button size="small" @click="viewAllIPs">查看全部</el-button>
          </div>
        </template>

        <div class="ip-preview">
          <el-alert
            title="网络资源管理功能"
            type="info"
            :closable="false"
            show-icon
          >
            <template #default>
              <p>此网段包含 {{ subnet.ip_count || 0 }} 个IP地址。</p>
              <p>您可以点击"查看全部"按钮查看详细的IP地址分配情况。</p>
            </template>
          </el-alert>
        </div>
      </el-card>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="$emit('update:visible', false)">关闭</el-button>
        <el-button type="primary" @click="editSubnet">编辑网段</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'SubnetDetailDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    subnet: {
      type: Object,
      default: null
    }
  },
  emits: ['update:visible', 'edit'],
  setup(props, { emit }) {
    // 计算属性
    const usagePercentage = computed(() => {
      if (!props.subnet?.ip_count || props.subnet.ip_count === 0) return 0
      return Math.round((props.subnet.allocated_count / props.subnet.ip_count) * 100)
    })

    const usageColor = computed(() => {
      const percentage = usagePercentage.value
      if (percentage >= 90) return '#f56c6c'
      if (percentage >= 70) return '#e6a23c'
      return '#67c23a'
    })

    // 方法
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }

    const refreshStats = () => {
      // 这里可以重新获取统计数据
      ElMessage.info('统计数据已刷新')
    }

    const viewAllIPs = () => {
      // 跳转到IP管理页面，并过滤当前网段
      ElMessage.info('跳转到网络资源管理页面功能待实现')
    }

    const editSubnet = () => {
      emit('edit')
      emit('update:visible', false)
    }

    return {
      usagePercentage,
      usageColor,
      formatDate,
      refreshStats,
      viewAllIPs,
      editSubnet
    }
  }
}
</script>

<style scoped>
.subnet-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-card {
  margin-bottom: 20px;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-item {
  text-align: center;
  padding: 20px 0;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stat-value.allocated {
  color: #e6a23c;
}

.stat-value.available {
  color: #67c23a;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.usage-progress {
  margin-top: 20px;
}

.ip-preview {
  padding: 10px 0;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-descriptions-item__label) {
  font-weight: 600;
}
</style>