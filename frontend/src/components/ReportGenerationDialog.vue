<template>
  <el-dialog
    v-model="dialogVisible"
    title="生成报告"
    width="600px"
    :before-close="handleClose"
  >
    <el-form :model="reportForm" :rules="rules" ref="formRef" label-width="120px">
      <el-form-item label="报告类型" prop="report_type">
        <el-select v-model="reportForm.report_type" placeholder="请选择报告类型" style="width: 100%">
          <el-option label="使用率报告" value="utilization"></el-option>
          <el-option label="IP地址清单" value="inventory"></el-option>
          <el-option label="网段规划报告" value="subnet_planning"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="导出格式" prop="format">
        <el-select v-model="reportForm.format" placeholder="请选择导出格式" style="width: 100%">
          <el-option label="PDF" value="pdf"></el-option>
          <el-option label="Excel" value="excel"></el-option>
          <el-option label="CSV" value="csv"></el-option>
          <el-option label="JSON" value="json"></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="指定网段">
        <el-select
          v-model="reportForm.subnet_ids"
          multiple
          placeholder="选择特定网段（可选）"
          style="width: 100%"
          clearable
        >
          <el-option
            v-for="subnet in availableSubnets"
            :key="subnet.id"
            :label="`${subnet.network} - ${subnet.description || 'N/A'}`"
            :value="subnet.id"
          ></el-option>
        </el-select>
      </el-form-item>

      <el-form-item label="日期范围">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="包含详细信息">
        <el-switch v-model="reportForm.include_details"></el-switch>
      </el-form-item>
    </el-form>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button type="primary" @click="generateReport" :loading="generating">
          {{ generating ? '生成中...' : '生成报告' }}
        </el-button>
      </span>
    </template>

    <!-- 报告状态对话框 -->
    <el-dialog
      v-model="showStatusDialog"
      title="报告生成状态"
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="report-status">
        <div v-if="reportStatus.status === 'generating'" class="status-generating">
          <el-icon class="is-loading"><Loading /></el-icon>
          <p>正在生成报告，请稍候...</p>
        </div>
        
        <div v-else-if="reportStatus.status === 'completed'" class="status-completed">
          <el-icon class="success-icon"><SuccessFilled /></el-icon>
          <p>报告生成完成！</p>
          <div class="report-info">
            <p><strong>报告ID:</strong> {{ reportStatus.report_id }}</p>
            <p><strong>生成时间:</strong> {{ formatDateTime(reportStatus.generated_at) }}</p>
            <p><strong>过期时间:</strong> {{ formatDateTime(reportStatus.expires_at) }}</p>
          </div>
        </div>
        
        <div v-else-if="reportStatus.status === 'failed'" class="status-failed">
          <el-icon class="error-icon"><CircleCloseFilled /></el-icon>
          <p>报告生成失败，请重试</p>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button v-if="reportStatus.status === 'generating'" @click="checkStatus">
            刷新状态
          </el-button>
          <el-button 
            v-if="reportStatus.status === 'completed'" 
            type="primary" 
            @click="downloadReport"
            :loading="downloading"
          >
            {{ downloading ? '下载中...' : '下载报告' }}
          </el-button>
          <el-button @click="closeStatusDialog">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, SuccessFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { 
  generateReport as generateReportAPI, 
  getReportStatus, 
  downloadReport as downloadReportAPI 
} from '@/api/monitoring'
import { subnetApi } from '@/api/subnet'

export default {
  name: 'ReportGenerationDialog',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'report-generated'],
  setup(props, { emit }) {
    const formRef = ref(null)
    const generating = ref(false)
    const downloading = ref(false)
    const showStatusDialog = ref(false)
    const availableSubnets = ref([])
    const dateRange = ref(null)
    
    const reportForm = reactive({
      report_type: 'utilization',
      format: 'pdf',
      subnet_ids: [],
      include_details: true
    })

    const reportStatus = reactive({
      report_id: '',
      status: 'generating',
      generated_at: '',
      expires_at: '',
      download_url: ''
    })

    const dialogVisible = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value)
    })

    const rules = {
      report_type: [
        { required: true, message: '请选择报告类型', trigger: 'change' }
      ],
      format: [
        { required: true, message: '请选择导出格式', trigger: 'change' }
      ]
    }

    // 加载可用网段
    const loadAvailableSubnets = async () => {
      try {
        const response = await subnetApi.getSubnets()
        // 处理不同的响应格式
        if (response.data) {
          if (response.data.subnets) {
            availableSubnets.value = response.data.subnets
          } else if (Array.isArray(response.data)) {
            availableSubnets.value = response.data
          } else if (response.data.items) {
            availableSubnets.value = response.data.items
          }
        } else if (Array.isArray(response)) {
          availableSubnets.value = response
        }
      } catch (error) {
        console.error('Load subnets error:', error)
        ElMessage.error('加载网段列表失败')
      }
    }

    // 生成报告
    const generateReport = async () => {
      if (!formRef.value) return
      
      try {
        await formRef.value.validate()
        
        generating.value = true
        
        const requestData = {
          ...reportForm
        }

        // 添加日期范围
        if (dateRange.value && dateRange.value.length === 2) {
          requestData.date_range = {
            start_date: dateRange.value[0],
            end_date: dateRange.value[1]
          }
        }

        const response = await generateReportAPI(requestData)
        
        // 更新报告状态
        Object.assign(reportStatus, {
          report_id: response.data.report_id,
          status: 'generating',
          generated_at: response.data.generated_at,
          expires_at: response.data.expires_at
        })

        // 关闭主对话框，显示状态对话框
        dialogVisible.value = false
        showStatusDialog.value = true

        // 开始轮询状态
        pollReportStatus()

        emit('report-generated', response.data)
        
      } catch (error) {
        ElMessage.error('生成报告失败')
        console.error('Generate report error:', error)
      } finally {
        generating.value = false
      }
    }

    // 轮询报告状态
    const pollReportStatus = async () => {
      const maxAttempts = 30 // 最多轮询30次
      let attempts = 0

      const poll = async () => {
        if (attempts >= maxAttempts) {
          reportStatus.status = 'failed'
          return
        }

        try {
          const response = await getReportStatus(reportStatus.report_id)
          const status = response.data.status

          if (status === 'completed') {
            reportStatus.status = 'completed'
            reportStatus.download_url = response.data.download_url
          } else if (status === 'failed') {
            reportStatus.status = 'failed'
          } else {
            // 继续轮询
            attempts++
            setTimeout(poll, 2000) // 2秒后再次检查
          }
        } catch (error) {
          console.error('Poll status error:', error)
          attempts++
          setTimeout(poll, 2000)
        }
      }

      poll()
    }

    // 手动检查状态
    const checkStatus = async () => {
      try {
        const response = await getReportStatus(reportStatus.report_id)
        const status = response.data.status

        if (status === 'completed') {
          reportStatus.status = 'completed'
          reportStatus.download_url = response.data.download_url
        } else if (status === 'failed') {
          reportStatus.status = 'failed'
        }
      } catch (error) {
        ElMessage.error('检查状态失败')
        console.error('Check status error:', error)
      }
    }

    // 下载报告
    const downloadReport = async () => {
      downloading.value = true
      try {
        const response = await downloadReportAPI(reportStatus.report_id)
        
        // 创建下载链接
        const blob = new Blob([response.data])
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        
        // 根据格式设置文件名
        const extension = reportForm.format === 'excel' ? 'xlsx' : reportForm.format
        link.download = `report_${reportStatus.report_id}.${extension}`
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        ElMessage.success('报告下载成功')
        closeStatusDialog()
        
      } catch (error) {
        ElMessage.error('下载报告失败')
        console.error('Download report error:', error)
      } finally {
        downloading.value = false
      }
    }

    // 格式化日期时间
    const formatDateTime = (dateTime) => {
      if (!dateTime) return ''
      return new Date(dateTime).toLocaleString()
    }

    // 关闭主对话框
    const handleClose = () => {
      dialogVisible.value = false
      resetForm()
    }

    // 关闭状态对话框
    const closeStatusDialog = () => {
      showStatusDialog.value = false
      resetForm()
    }

    // 重置表单
    const resetForm = () => {
      if (formRef.value) {
        formRef.value.resetFields()
      }
      Object.assign(reportForm, {
        report_type: 'utilization',
        format: 'pdf',
        subnet_ids: [],
        include_details: true
      })
      dateRange.value = null
    }

    // 监听对话框显示状态
    watch(() => props.modelValue, (newVal) => {
      if (newVal) {
        loadAvailableSubnets()
      }
    })

    onMounted(() => {
      loadAvailableSubnets()
    })

    return {
      formRef,
      generating,
      downloading,
      showStatusDialog,
      availableSubnets,
      dateRange,
      reportForm,
      reportStatus,
      dialogVisible,
      rules,
      generateReport,
      checkStatus,
      downloadReport,
      formatDateTime,
      handleClose,
      closeStatusDialog,
      Loading,
      SuccessFilled,
      CircleCloseFilled
    }
  }
}
</script>

<style scoped>
.report-status {
  text-align: center;
  padding: 20px;
}

.status-generating {
  color: #409EFF;
}

.status-completed {
  color: #67C23A;
}

.status-failed {
  color: #F56C6C;
}

.success-icon,
.error-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.report-info {
  text-align: left;
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.report-info p {
  margin: 5px 0;
  font-size: 14px;
}

.is-loading {
  font-size: 24px;
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
</style>