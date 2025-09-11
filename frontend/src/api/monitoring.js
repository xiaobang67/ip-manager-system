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

