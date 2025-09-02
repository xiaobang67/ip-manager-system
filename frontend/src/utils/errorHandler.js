/**
 * 前端错误处理工具
 * 提供统一的错误处理、用户友好的错误提示和错误报告功能
 */
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import router from '@/router'
import store from '@/store'

class ErrorHandler {
  constructor() {
    this.errorCodes = {
      // 认证相关错误
      'AUTHENTICATION_ERROR': {
        title: '认证失败',
        message: '登录已过期，请重新登录',
        type: 'error',
        action: 'redirect',
        target: '/login'
      },
      'AUTHORIZATION_ERROR': {
        title: '权限不足',
        message: '您没有权限执行此操作',
        type: 'error',
        action: 'none'
      },
      
      // 验证相关错误
      'VALIDATION_ERROR': {
        title: '数据验证失败',
        message: '请检查输入的数据格式',
        type: 'warning',
        action: 'none'
      },
      'INVALID_IP_FORMAT': {
        title: 'IP地址格式错误',
        message: '请输入有效的IP地址',
        type: 'warning',
        action: 'none'
      },
      'INVALID_SUBNET_FORMAT': {
        title: '子网格式错误',
        message: '请输入有效的子网地址',
        type: 'warning',
        action: 'none'
      },
      
      // 业务逻辑错误
      'IP_ALREADY_ALLOCATED': {
        title: 'IP地址已分配',
        message: '该IP地址已被分配，请选择其他地址',
        type: 'warning',
        action: 'none'
      },
      'SUBNET_OVERLAP': {
        title: '子网重叠',
        message: '子网地址与现有子网重叠',
        type: 'warning',
        action: 'none'
      },
      'CANNOT_DELETE_ALLOCATED_IP': {
        title: '无法删除',
        message: '无法删除已分配的IP地址',
        type: 'warning',
        action: 'none'
      },
      
      // 资源相关错误
      'NOT_FOUND': {
        title: '资源不存在',
        message: '请求的资源不存在',
        type: 'error',
        action: 'none'
      },
      'CONFLICT': {
        title: '资源冲突',
        message: '操作与现有资源冲突',
        type: 'error',
        action: 'none'
      },
      
      // 系统错误
      'DATABASE_ERROR': {
        title: '数据库错误',
        message: '数据库操作失败，请稍后重试',
        type: 'error',
        action: 'retry'
      },
      'INTERNAL_SERVER_ERROR': {
        title: '服务器错误',
        message: '服务器内部错误，请稍后重试',
        type: 'error',
        action: 'retry'
      },
      'RATE_LIMIT_EXCEEDED': {
        title: '请求过于频繁',
        message: '请求过于频繁，请稍后再试',
        type: 'warning',
        action: 'wait'
      },
      
      // 网络错误
      'NETWORK_ERROR': {
        title: '网络错误',
        message: '网络连接失败，请检查网络设置',
        type: 'error',
        action: 'retry'
      },
      'TIMEOUT_ERROR': {
        title: '请求超时',
        message: '请求超时，请稍后重试',
        type: 'warning',
        action: 'retry'
      }
    }
    
    this.setupGlobalErrorHandlers()
  }
  
  /**
   * 设置全局错误处理器
   */
  setupGlobalErrorHandlers() {
    // 捕获未处理的Promise错误
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason)
      this.handleError(event.reason, { source: 'unhandledrejection' })
      event.preventDefault()
    })
    
    // 捕获JavaScript运行时错误
    window.addEventListener('error', (event) => {
      console.error('JavaScript error:', event.error)
      this.handleError(event.error, { 
        source: 'javascript',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      })
    })
    
    // Vue错误处理
    if (window.Vue) {
      window.Vue.config.errorHandler = (err, vm, info) => {
        console.error('Vue error:', err, info)
        this.handleError(err, { source: 'vue', info })
      }
    }
  }
  
  /**
   * 处理API错误响应
   * @param {Object} error - 错误对象
   * @param {Object} options - 处理选项
   */
  handleApiError(error, options = {}) {
    const { response, request, message } = error
    
    if (response) {
      // 服务器返回错误响应
      const { status, data } = response
      this.handleHttpError(status, data, options)
    } else if (request) {
      // 请求发送但没有收到响应
      this.handleNetworkError(options)
    } else {
      // 请求配置错误
      this.handleGenericError(message, options)
    }
  }
  
  /**
   * 处理HTTP错误
   * @param {number} status - HTTP状态码
   * @param {Object} data - 错误数据
   * @param {Object} options - 处理选项
   */
  handleHttpError(status, data, options = {}) {
    const errorCode = data?.error?.code || `HTTP_${status}`
    const errorMessage = data?.error?.message || data?.detail || data?.message
    const errorDetails = data?.error?.details
    
    const config = this.errorCodes[errorCode] || {
      title: `HTTP ${status} 错误`,
      message: errorMessage || this.getDefaultHttpMessage(status),
      type: 'error',
      action: 'none'
    }
    
    this.showError(config, {
      ...options,
      errorCode,
      errorDetails,
      httpStatus: status
    })
    
    // 执行相应的动作
    this.executeAction(config.action, { status, data, options })
  }
  
  /**
   * 处理网络错误
   * @param {Object} options - 处理选项
   */
  handleNetworkError(options = {}) {
    const config = this.errorCodes['NETWORK_ERROR']
    this.showError(config, options)
  }
  
  /**
   * 处理通用错误
   * @param {string} message - 错误消息
   * @param {Object} options - 处理选项
   */
  handleGenericError(message, options = {}) {
    this.showError({
      title: '操作失败',
      message: message || '发生未知错误',
      type: 'error',
      action: 'none'
    }, options)
  }
  
  /**
   * 处理业务逻辑错误
   * @param {string} errorCode - 错误代码
   * @param {string} customMessage - 自定义消息
   * @param {Object} options - 处理选项
   */
  handleBusinessError(errorCode, customMessage = null, options = {}) {
    const config = this.errorCodes[errorCode] || {
      title: '操作失败',
      message: customMessage || '业务逻辑错误',
      type: 'warning',
      action: 'none'
    }
    
    if (customMessage) {
      config.message = customMessage
    }
    
    this.showError(config, options)
  }
  
  /**
   * 显示错误信息
   * @param {Object} config - 错误配置
   * @param {Object} options - 显示选项
   */
  showError(config, options = {}) {
    const { 
      showType = 'message', 
      duration = 0,
      showClose = true,
      center = false 
    } = options
    
    switch (showType) {
      case 'notification':
        ElNotification({
          title: config.title,
          message: config.message,
          type: config.type,
          duration: duration || 4500,
          showClose
        })
        break
        
      case 'messagebox':
        ElMessageBox.alert(config.message, config.title, {
          type: config.type,
          center,
          showClose
        })
        break
        
      case 'message':
      default:
        ElMessage({
          message: config.message,
          type: config.type,
          duration: duration || 3000,
          showClose,
          center
        })
        break
    }
    
    // 记录错误日志
    this.logError(config, options)
  }
  
  /**
   * 执行错误处理动作
   * @param {string} action - 动作类型
   * @param {Object} context - 上下文信息
   */
  executeAction(action, context = {}) {
    switch (action) {
      case 'redirect':
        const target = context.target || '/login'
        router.push(target)
        break
        
      case 'logout':
        store.dispatch('auth/logout')
        router.push('/login')
        break
        
      case 'retry':
        // 可以触发重试事件
        this.$emit && this.$emit('error-retry', context)
        break
        
      case 'reload':
        window.location.reload()
        break
        
      case 'wait':
        // 显示等待提示
        ElMessage.info('请稍后再试')
        break
        
      case 'none':
      default:
        // 不执行任何动作
        break
    }
  }
  
  /**
   * 获取默认HTTP错误消息
   * @param {number} status - HTTP状态码
   * @returns {string} 错误消息
   */
  getDefaultHttpMessage(status) {
    const messages = {
      400: '请求参数错误',
      401: '未授权访问',
      403: '权限不足',
      404: '资源不存在',
      405: '请求方法不允许',
      408: '请求超时',
      409: '资源冲突',
      422: '请求数据验证失败',
      429: '请求过于频繁',
      500: '服务器内部错误',
      502: '网关错误',
      503: '服务不可用',
      504: '网关超时'
    }
    
    return messages[status] || `HTTP ${status} 错误`
  }
  
  /**
   * 记录错误日志
   * @param {Object} config - 错误配置
   * @param {Object} options - 选项
   */
  logError(config, options = {}) {
    const logData = {
      timestamp: new Date().toISOString(),
      title: config.title,
      message: config.message,
      type: config.type,
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: store.getters['auth/currentUser']?.id,
      ...options
    }
    
    // 发送到后端日志系统
    this.sendErrorLog(logData)
    
    // 本地存储（用于离线时的错误收集）
    this.storeErrorLocally(logData)
  }
  
  /**
   * 发送错误日志到后端
   * @param {Object} logData - 日志数据
   */
  async sendErrorLog(logData) {
    try {
      // 这里可以调用API发送错误日志
      // await api.post('/api/logs/error', logData)
      console.log('Error logged:', logData)
    } catch (error) {
      // 发送失败时存储到本地
      this.storeErrorLocally(logData)
    }
  }
  
  /**
   * 本地存储错误日志
   * @param {Object} logData - 日志数据
   */
  storeErrorLocally(logData) {
    try {
      const errors = JSON.parse(localStorage.getItem('error_logs') || '[]')
      errors.push(logData)
      
      // 只保留最近100条错误日志
      if (errors.length > 100) {
        errors.splice(0, errors.length - 100)
      }
      
      localStorage.setItem('error_logs', JSON.stringify(errors))
    } catch (error) {
      console.error('Failed to store error locally:', error)
    }
  }
  
  /**
   * 获取本地存储的错误日志
   * @returns {Array} 错误日志数组
   */
  getLocalErrorLogs() {
    try {
      return JSON.parse(localStorage.getItem('error_logs') || '[]')
    } catch (error) {
      return []
    }
  }
  
  /**
   * 清除本地错误日志
   */
  clearLocalErrorLogs() {
    localStorage.removeItem('error_logs')
  }
  
  /**
   * 处理表单验证错误
   * @param {Array} errors - 验证错误数组
   */
  handleValidationErrors(errors) {
    if (!Array.isArray(errors) || errors.length === 0) {
      return
    }
    
    const errorMessages = errors.map(error => {
      if (typeof error === 'string') {
        return error
      }
      
      if (error.field && error.message) {
        return `${error.field}: ${error.message}`
      }
      
      return error.message || '验证失败'
    })
    
    ElMessage({
      message: errorMessages.join('; '),
      type: 'warning',
      duration: 5000,
      showClose: true
    })
  }
  
  /**
   * 创建错误边界组件
   * @param {Function} fallbackComponent - 降级组件
   * @returns {Object} Vue组件选项
   */
  createErrorBoundary(fallbackComponent) {
    return {
      name: 'ErrorBoundary',
      data() {
        return {
          hasError: false,
          error: null
        }
      },
      errorCaptured(err, vm, info) {
        this.hasError = true
        this.error = err
        
        // 记录错误
        errorHandler.handleError(err, { source: 'vue-boundary', info })
        
        return false // 阻止错误继续传播
      },
      render() {
        if (this.hasError) {
          return fallbackComponent ? fallbackComponent(this.error) : null
        }
        
        return this.$slots.default()
      }
    }
  }
}

// 创建全局错误处理器实例
const errorHandler = new ErrorHandler()

// 导出错误处理器和相关工具
export default errorHandler

export {
  ErrorHandler
}