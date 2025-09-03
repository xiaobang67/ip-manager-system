/**
 * HTTP请求封装
 * 基于axios的请求拦截器和响应拦截器
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import store from '@/store'
import router from '@/router'
import errorHandler from '@/utils/errorHandler'

/**
 * 标准化自定义字段数据
 * 解决后端可能返回name而不是field_name的兼容性问题
 */
function normalizeCustomField(field) {
  if (!field || typeof field !== 'object') {
    return field
  }
  
  return {
    ...field,
    // 确保field_name字段存在，兼容可能的name字段
    field_name: field.field_name || field.name || '未知字段',
    // 确保其他必要字段存在
    field_type: field.field_type || field.type || 'text',
    entity_type: field.entity_type || 'ip',
    is_required: Boolean(field.is_required || field.required),
    id: field.id || 0
  }
}

// 创建axios实例
const service = axios.create({
  baseURL: '/api', // 统一使用相对路径，通过Nginx代理
  timeout: 15000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 添加访问令牌到请求头
    const token = store.getters['auth/accessToken']
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 处理自定义字段数据的兼容性问题
    const data = response.data
    
    // 如果是自定义字段相关的响应，进行数据标准化
    if (response.config.url && response.config.url.includes('/custom-fields')) {
      if (Array.isArray(data)) {
        // 直接是数组的情况
        return data.map(normalizeCustomField)
      } else if (data && Array.isArray(data.data)) {
        // 包装在data属性中的情况
        return {
          ...data,
          data: data.data.map(normalizeCustomField)
        }
      } else if (data && data.fields && Array.isArray(data.fields)) {
        // 包装在fields属性中的情况
        return {
          ...data,
          fields: data.fields.map(normalizeCustomField)
        }
      }
    }
    
    // 直接返回响应数据
    return data
  },
  async error => {
    // 使用统一的错误处理器
    errorHandler.handleApiError(error, {
      showType: 'message',
      duration: 3000
    })
    
    // 特殊处理401错误的token刷新逻辑
    if (error.response?.status === 401) {
      const refreshSuccess = await handleTokenRefresh()
      if (refreshSuccess) {
        // 重新发送原请求
        return service(error.config)
      } else {
        // 刷新失败，跳转到登录页
        store.dispatch('auth/logout')
        router.push('/login')
      }
    }
    
    return Promise.reject(error)
  }
)

/**
 * 处理令牌刷新
 * @returns {Promise<boolean>} 刷新成功返回true，失败返回false
 */
async function handleTokenRefresh() {
  try {
    const refreshToken = store.getters['auth/refreshToken']
    if (!refreshToken) {
      return false
    }
    
    // 调用刷新令牌API
    const response = await axios.post('/api/auth/refresh', {
      refresh_token: refreshToken
    })
    
    // 更新访问令牌
    const { access_token } = response.data
    store.commit('auth/SET_ACCESS_TOKEN', access_token)
    
    return true
  } catch (error) {
    console.error('Token refresh failed:', error)
    return false
  }
}

export default service