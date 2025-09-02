/**
 * 监控和报告相关的API接口
 */
import request from './request'

// 获取仪表盘汇总数据
export const getDashboardSummary = () => {
  return request.get('/monitoring/dashboard')
}

// 获取IP使用率统计
export const getIPUtilizationStats = () => {
  return request.get('/monitoring/ip-utilization')
}

// 获取网段使用率统计
export const getSubnetUtilizationStats = () => {
  return request.get('/monitoring/subnet-utilization')
}

// 获取IP分配趋势
export const getAllocationTrends = (days = 30) => {
  return request.get('/monitoring/allocation-trends', {
    params: { days }
  })
}

// 获取使用率最高的网段
export const getTopUtilizedSubnets = (limit = 10) => {
  return request.get('/monitoring/top-utilized-subnets', {
    params: { limit }
  })
}

// 获取警报统计
export const getAlertStatistics = () => {
  return request.get('/monitoring/alerts/statistics')
}

// 获取警报规则列表
export const getAlertRules = (params = {}) => {
  return request.get('/monitoring/alerts/rules', { params })
}

// 创建警报规则
export const createAlertRule = (data) => {
  return request.post('/monitoring/alerts/rules', data)
}

// 更新警报规则
export const updateAlertRule = (ruleId, data) => {
  return request.put(`/monitoring/alerts/rules/${ruleId}`, data)
}

// 删除警报规则
export const deleteAlertRule = (ruleId) => {
  return request.delete(`/monitoring/alerts/rules/${ruleId}`)
}

// 获取警报历史
export const getAlertHistory = (params = {}) => {
  return request.get('/monitoring/alerts/history', { params })
}

// 解决警报
export const resolveAlert = (alertId) => {
  return request.put(`/monitoring/alerts/history/${alertId}/resolve`)
}

// 手动触发警报检查
export const checkAlerts = () => {
  return request.post('/monitoring/alerts/check')
}

// 生成报告
export const generateReport = (data) => {
  return request.post('/monitoring/reports/generate', data)
}

// 获取报告状态
export const getReportStatus = (reportId) => {
  return request.get(`/monitoring/reports/${reportId}`)
}

// 下载报告
export const downloadReport = (reportId) => {
  return request.get(`/monitoring/reports/${reportId}/download`, {
    responseType: 'blob'
  })
}