/**
 * HTTP请求封装
 * 基于axios的请求拦截器和响应拦截器
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'
import store from '@/store'
import router from '@/router'
import errorHandler from '@/utils/errorHandler'

// 创建axios实例
const service = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000/api',
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
    // 直接返回响应数据
    return response.data
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