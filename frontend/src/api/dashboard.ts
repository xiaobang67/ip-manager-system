import { http } from '@/utils/request'
import type { DashboardStats } from '@/types'

export const dashboardApi = {
  // 获取仪表盘统计数据
  getStats() {
    return http.get<DashboardStats>('/v1/dashboard/stats')
  },

  // 获取最近活动记录
  getRecentActivities(limit = 10) {
    return http.get<Array<{
      id: number
      title: string
      time: string
      type: string
    }>>('/v1/dashboard/recent-activities', { 
      params: { limit } 
    })
  }
}