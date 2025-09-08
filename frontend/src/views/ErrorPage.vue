<template>
  <div class="error-page">
    <div class="error-container">
      <div class="error-icon">
        <el-icon :size="120" :color="errorConfig.color">
          <component :is="errorConfig.icon" />
        </el-icon>
      </div>
      
      <div class="error-content">
        <h1 class="error-title">{{ errorConfig.title }}</h1>
        <p class="error-message">{{ errorConfig.message }}</p>
        
        <div class="error-details" v-if="showDetails && errorDetails">
          <el-collapse v-model="activeCollapse">
            <el-collapse-item title="错误详情" name="details">
              <div class="error-detail-content">
                <p><strong>错误代码:</strong> {{ errorDetails.code }}</p>
                <p><strong>时间:</strong> {{ formatTime(errorDetails.timestamp) }}</p>
                <p v-if="errorDetails.requestId"><strong>请求ID:</strong> {{ errorDetails.requestId }}</p>
                <div v-if="errorDetails.details">
                  <strong>详细信息:</strong>
                  <pre>{{ JSON.stringify(errorDetails.details, null, 2) }}</pre>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <div class="error-actions">
          <el-button 
            type="primary" 
            @click="handlePrimaryAction"
            :loading="loading"
          >
            {{ errorConfig.primaryAction }}
          </el-button>
          
          <el-button 
            v-if="errorConfig.secondaryAction"
            @click="handleSecondaryAction"
          >
            {{ errorConfig.secondaryAction }}
          </el-button>
          
          <el-button 
            v-if="canReportError"
            type="info"
            @click="reportError"
          >
            报告问题
          </el-button>
        </div>
        
        <div class="error-suggestions" v-if="errorConfig.suggestions">
          <h3>建议解决方案:</h3>
          <ul>
            <li v-for="suggestion in errorConfig.suggestions" :key="suggestion">
              {{ suggestion }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  Warning, 
  CircleClose, 
  Lock, 
  Connection, 
  Document,
  QuestionFilled 
} from '@element-plus/icons-vue'

export default {
  name: 'ErrorPage',
  components: {
    Warning,
    CircleClose,
    Lock,
    Connection,
    Document,
    QuestionFilled
  },
  props: {
    errorType: {
      type: String,
      default: '500'
    },
    errorMessage: {
      type: String,
      default: ''
    },
    errorDetails: {
      type: Object,
      default: null
    },
    showDetails: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      loading: false,
      activeCollapse: [],
      canReportError: true
    }
  },
  computed: {
    errorConfig() {
      const configs = {
        '400': {
          title: '请求错误',
          message: this.errorMessage || '您的请求包含无效参数，请检查后重试',
          icon: 'Warning',
          color: '#E6A23C',
          primaryAction: '返回上页',
          secondaryAction: '重新尝试',
          suggestions: [
            '检查输入的数据格式是否正确',
            '确认所有必填字段都已填写',
            '联系管理员获取帮助'
          ]
        },
        '401': {
          title: '认证失败',
          message: this.errorMessage || '您的登录已过期，请重新登录',
          icon: 'Lock',
          color: '#F56C6C',
          primaryAction: '重新登录',
          secondaryAction: '返回首页',
          suggestions: [
            '点击重新登录按钮',
            '检查用户名和密码是否正确',
            '清除浏览器缓存后重试'
          ]
        },
        '403': {
          title: '权限不足',
          message: this.errorMessage || '您没有权限访问此资源',
          icon: 'Lock',
          color: '#F56C6C',
          primaryAction: '返回首页',
          secondaryAction: '联系管理员',
          suggestions: [
            '联系系统管理员申请相应权限',
            '确认您的账户状态是否正常',
            '尝试使用其他账户登录'
          ]
        },
        '404': {
          title: '页面不存在',
          message: this.errorMessage || '抱歉，您访问的页面不存在',
          icon: 'Document',
          color: '#909399',
          primaryAction: '返回首页',
          secondaryAction: '返回上页',
          suggestions: [
            '检查URL地址是否正确',
            '尝试从导航菜单重新进入',
            '联系管理员确认页面是否已移除'
          ]
        },
        '429': {
          title: '请求过于频繁',
          message: this.errorMessage || '您的请求过于频繁，请稍后再试',
          icon: 'Warning',
          color: '#E6A23C',
          primaryAction: '稍后重试',
          suggestions: [
            '等待几分钟后再次尝试',
            '减少请求频率',
            '联系管理员调整限制'
          ]
        },
        '500': {
          title: '服务器错误',
          message: this.errorMessage || '服务器遇到了一个错误，请稍后再试',
          icon: 'CircleClose',
          color: '#F56C6C',
          primaryAction: '刷新页面',
          secondaryAction: '返回首页',
          suggestions: [
            '刷新页面重新尝试',
            '检查网络连接是否正常',
            '如果问题持续存在，请联系技术支持'
          ]
        },
        '503': {
          title: '服务不可用',
          message: this.errorMessage || '服务暂时不可用，请稍后再试',
          icon: 'Connection',
          color: '#E6A23C',
          primaryAction: '重新尝试',
          suggestions: [
            '系统可能正在维护中',
            '请稍后再次尝试',
            '关注系统公告获取最新信息'
          ]
        },
        'network': {
          title: '网络错误',
          message: this.errorMessage || '网络连接失败，请检查您的网络设置',
          icon: 'Connection',
          color: '#E6A23C',
          primaryAction: '重新尝试',
          suggestions: [
            '检查网络连接是否正常',
            '尝试刷新页面',
            '联系网络管理员'
          ]
        },
        'default': {
          title: '未知错误',
          message: this.errorMessage || '发生了未知错误，请联系技术支持',
          icon: 'QuestionFilled',
          color: '#909399',
          primaryAction: '返回首页',
          secondaryAction: '联系支持',
          suggestions: [
            '尝试刷新页面',
            '清除浏览器缓存',
            '联系技术支持团队'
          ]
        }
      }
      
      return configs[this.errorType] || configs['default']
    }
  },
  methods: {
    handlePrimaryAction() {
      this.loading = true
      
      switch (this.errorType) {
        case '401':
          this.$router.push('/login')
          break
        case '404':
        case '403':
        case '500':
        case 'default':
          this.$router.push('/')
          break
        case '400':
          this.$router.go(-1)
          break
        case '429':
        case '503':
        case 'network':
          this.retryRequest()
          break
        default:
          window.location.reload()
      }
      
      setTimeout(() => {
        this.loading = false
      }, 1000)
    },
    
    handleSecondaryAction() {
      switch (this.errorType) {
        case '401':
          this.$router.push('/')
          break
        case '400':
          this.retryRequest()
          break
        case '403':
          this.contactAdmin()
          break
        case '404':
        case '500':
          this.$router.go(-1)
          break
        default:
          this.$router.push('/')
      }
    },
    
    retryRequest() {
      // 触发重试事件
      this.$emit('retry')
      
      // 如果没有父组件处理重试，则刷新页面
      setTimeout(() => {
        if (!this.$listeners.retry) {
          window.location.reload()
        }
      }, 100)
    },
    
    contactAdmin() {
      // 可以集成邮件客户端或工单系统
      this.$message.info('请联系系统管理员获取帮助')
    },
    
    reportError() {
      // 发送错误报告
      const errorReport = {
        type: this.errorType,
        message: this.errorMessage,
        details: this.errorDetails,
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString()
      }
      
      // 这里可以调用API发送错误报告
      this.$message.success('错误报告已发送，感谢您的反馈')
    },
    
    formatTime(timestamp) {
      if (!timestamp) return ''
      
      const date = new Date(timestamp * 1000)
      return date.toLocaleString('zh-CN')
    }
  }
}
</script>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.error-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 40px;
  text-align: center;
  max-width: 600px;
  width: 100%;
}

.error-icon {
  margin-bottom: 30px;
}

.error-title {
  font-size: 32px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.error-message {
  font-size: 16px;
  color: #606266;
  margin-bottom: 30px;
  line-height: 1.6;
}

.error-details {
  margin: 20px 0;
  text-align: left;
}

.error-detail-content {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 6px;
  font-size: 14px;
}

.error-detail-content pre {
  background: #f1f2f3;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin-top: 10px;
}

.error-actions {
  margin: 30px 0;
}

.error-actions .el-button {
  margin: 0 8px;
}

.error-suggestions {
  text-align: left;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 20px;
}

.error-suggestions h3 {
  color: #303133;
  margin-bottom: 12px;
  font-size: 16px;
}

.error-suggestions ul {
  margin: 0;
  padding-left: 20px;
}

.error-suggestions li {
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .error-container {
    padding: 20px;
    margin: 10px;
  }
  
  .error-title {
    font-size: 24px;
  }
  
  .error-actions .el-button {
    display: block;
    width: 100%;
    margin: 8px 0;
  }
}
</style>