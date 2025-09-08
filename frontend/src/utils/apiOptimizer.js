/**
 * API客户端优化工具
 * 提供请求缓存、防抖、重试等功能
 */
import axios from 'axios'
import { debounce } from 'lodash-es'

// 请求缓存
const requestCache = new Map()
const cacheTimeout = 5 * 60 * 1000 // 5分钟缓存

// 防抖请求映射
const debouncedRequests = new Map()

// 正在进行的请求映射（防止重复请求）
const pendingRequests = new Map()

/**
 * 生成缓存键
 */
function generateCacheKey(config) {
  const { method, url, params, data } = config
  return `${method}:${url}:${JSON.stringify(params)}:${JSON.stringify(data)}`
}

/**
 * 检查缓存
 */
function checkCache(cacheKey) {
  const cached = requestCache.get(cacheKey)
  if (cached && Date.now() - cached.timestamp < cacheTimeout) {
    return cached.data
  }
  return null
}

/**
 * 设置缓存
 */
function setCache(cacheKey, data) {
  requestCache.set(cacheKey, {
    data,
    timestamp: Date.now()
  })
  
  // 清理过期缓存
  if (requestCache.size > 100) {
    const now = Date.now()
    for (const [key, value] of requestCache.entries()) {
      if (now - value.timestamp > cacheTimeout) {
        requestCache.delete(key)
      }
    }
  }
}

/**
 * 清除缓存
 */
export function clearCache(pattern = null) {
  if (pattern) {
    for (const key of requestCache.keys()) {
      if (key.includes(pattern)) {
        requestCache.delete(key)
      }
    }
  } else {
    requestCache.clear()
  }
}

/**
 * 带缓存的请求
 */
export function cachedRequest(config, options = {}) {
  const {
    cache = true,
    cacheTTL = cacheTimeout,
    skipCache = false
  } = options
  
  return new Promise((resolve, reject) => {
    const cacheKey = generateCacheKey(config)
    
    // 检查缓存
    if (cache && !skipCache && config.method?.toLowerCase() === 'get') {
      const cached = checkCache(cacheKey)
      if (cached) {

        resolve(cached)
        return
      }
    }
    
    // 检查是否有相同的请求正在进行
    if (pendingRequests.has(cacheKey)) {

      pendingRequests.get(cacheKey).then(resolve).catch(reject)
      return
    }
    
    // 发起请求
    const requestPromise = axios(config)
      .then(response => {
        // 缓存GET请求的响应
        if (cache && config.method?.toLowerCase() === 'get') {
          setCache(cacheKey, response)
        }
        
        pendingRequests.delete(cacheKey)
        return response
      })
      .catch(error => {
        pendingRequests.delete(cacheKey)
        throw error
      })
    
    pendingRequests.set(cacheKey, requestPromise)
    requestPromise.then(resolve).catch(reject)
  })
}

/**
 * 防抖请求
 */
export function debouncedRequest(config, delay = 300) {
  const cacheKey = generateCacheKey(config)
  
  if (!debouncedRequests.has(cacheKey)) {
    debouncedRequests.set(cacheKey, debounce((resolve, reject) => {
      cachedRequest(config)
        .then(resolve)
        .catch(reject)
    }, delay))
  }
  
  return new Promise((resolve, reject) => {
    debouncedRequests.get(cacheKey)(resolve, reject)
  })
}

/**
 * 重试请求
 */
export function retryRequest(config, options = {}) {
  const {
    maxRetries = 3,
    retryDelay = 1000,
    retryCondition = (error) => {
      // 默认重试条件：网络错误或5xx错误
      return !error.response || error.response.status >= 500
    }
  } = options
  
  let retryCount = 0
  
  const executeRequest = () => {
    return cachedRequest(config).catch(error => {
      if (retryCount < maxRetries && retryCondition(error)) {
        retryCount++

        
        return new Promise(resolve => {
          setTimeout(() => {
            resolve(executeRequest())
          }, retryDelay * retryCount)
        })
      }
      throw error
    })
  }
  
  return executeRequest()
}

/**
 * 批量请求
 */
export function batchRequest(requests, options = {}) {
  const {
    concurrency = 5,
    failFast = false
  } = options
  
  return new Promise((resolve, reject) => {
    const results = []
    const errors = []
    let completed = 0
    let running = 0
    let index = 0
    
    const processNext = () => {
      while (running < concurrency && index < requests.length) {
        const currentIndex = index++
        const request = requests[currentIndex]
        running++
        
        cachedRequest(request)
          .then(response => {
            results[currentIndex] = response
          })
          .catch(error => {
            errors[currentIndex] = error
            if (failFast) {
              reject(error)
              return
            }
          })
          .finally(() => {
            running--
            completed++
            
            if (completed === requests.length) {
              if (errors.length > 0 && failFast) {
                reject(errors[0])
              } else {
                resolve({ results, errors })
              }
            } else {
              processNext()
            }
          })
      }
    }
    
    processNext()
  })
}

/**
 * 请求拦截器 - 添加性能监控
 */
export function setupPerformanceInterceptors(axiosInstance) {
  // 请求拦截器
  axiosInstance.interceptors.request.use(
    config => {
      config.metadata = { startTime: Date.now() }
      return config
    },
    error => Promise.reject(error)
  )
  
  // 响应拦截器
  axiosInstance.interceptors.response.use(
    response => {
      const endTime = Date.now()
      const duration = endTime - response.config.metadata.startTime
      
      // 记录性能数据

      
      // 慢请求警告
      if (duration > 2000) {

      }
      
      return response
    },
    error => {
      if (error.config?.metadata) {
        const endTime = Date.now()
        const duration = endTime - error.config.metadata.startTime

      }
      return Promise.reject(error)
    }
  )
}

/**
 * 预加载资源
 */
export function preloadResources(urls) {
  const promises = urls.map(url => {
    return cachedRequest({ method: 'GET', url })
      .catch(error => {

        return null
      })
  })
  
  return Promise.allSettled(promises)
}

/**
 * 获取缓存统计
 */
export function getCacheStats() {
  const now = Date.now()
  let validCount = 0
  let expiredCount = 0
  
  for (const [key, value] of requestCache.entries()) {
    if (now - value.timestamp < cacheTimeout) {
      validCount++
    } else {
      expiredCount++
    }
  }
  
  return {
    total: requestCache.size,
    valid: validCount,
    expired: expiredCount,
    hitRate: validCount / (validCount + expiredCount) || 0
  }
}

/**
 * 智能预取
 */
export class SmartPrefetcher {
  constructor() {
    this.accessPatterns = new Map()
    this.prefetchQueue = []
    this.isProcessing = false
  }
  
  // 记录访问模式
  recordAccess(url) {
    const pattern = this.accessPatterns.get(url) || { count: 0, lastAccess: 0 }
    pattern.count++
    pattern.lastAccess = Date.now()
    this.accessPatterns.set(url, pattern)
  }
  
  // 预测下一个可能访问的资源
  predictNext(currentUrl) {
    // 简单的预测逻辑：基于访问频率和时间
    const candidates = []
    
    for (const [url, pattern] of this.accessPatterns.entries()) {
      if (url !== currentUrl) {
        const score = pattern.count * (1 / (Date.now() - pattern.lastAccess + 1))
        candidates.push({ url, score })
      }
    }
    
    return candidates
      .sort((a, b) => b.score - a.score)
      .slice(0, 3)
      .map(c => c.url)
  }
  
  // 添加到预取队列
  addToPrefetchQueue(urls) {
    this.prefetchQueue.push(...urls)
    this.processPrefetchQueue()
  }
  
  // 处理预取队列
  async processPrefetchQueue() {
    if (this.isProcessing || this.prefetchQueue.length === 0) {
      return
    }
    
    this.isProcessing = true
    
    while (this.prefetchQueue.length > 0) {
      const url = this.prefetchQueue.shift()
      
      try {
        await cachedRequest({ method: 'GET', url })

      } catch (error) {

      }
      
      // 避免过于频繁的预取
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    this.isProcessing = false
  }
}

// 全局智能预取器实例
export const smartPrefetcher = new SmartPrefetcher()

/**
 * 请求优化配置
 */
export const optimizationConfig = {
  // 缓存配置
  cache: {
    enabled: true,
    ttl: 5 * 60 * 1000, // 5分钟
    maxSize: 100
  },
  
  // 防抖配置
  debounce: {
    enabled: true,
    delay: 300
  },
  
  // 重试配置
  retry: {
    enabled: true,
    maxRetries: 3,
    retryDelay: 1000
  },
  
  // 批量请求配置
  batch: {
    concurrency: 5,
    failFast: false
  },
  
  // 预取配置
  prefetch: {
    enabled: true,
    maxPredictions: 3
  }
}