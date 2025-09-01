import { http } from '@/utils/request'
import type { NetworkSegment, NetworkSegmentCreate, NetworkSegmentUpdate, NetworkSegmentStats, PaginatedResponse } from '@/types'

export const networkSegmentApi = {
  // 获取网段列表
  getList(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
    search?: string
  }) {
    return http.get<PaginatedResponse<NetworkSegment>>('/v1/network-segments', { params })
  },

  // 根据ID获取网段
  getById(id: number) {
    return http.get<NetworkSegment>(`/v1/network-segments/${id}`)
  },

  // 创建网段
  create(data: NetworkSegmentCreate) {
    return http.post<NetworkSegment>('/v1/network-segments', data)
  },

  // 更新网段
  update(id: number, data: NetworkSegmentUpdate) {
    return http.put<NetworkSegment>(`/v1/network-segments/${id}`, data)
  },

  // 删除网段
  delete(id: number) {
    return http.delete(`/v1/network-segments/${id}`)
  },

  // 获取网段统计信息
  getStatistics(id: number) {
    return http.get<NetworkSegmentStats>(`/v1/network-segments/${id}/statistics`)
  },

  // 获取网段中可用的IP地址
  getAvailableIps(id: number, count: number = 10) {
    return http.get<{ available_ips: string[] }>(`/v1/network-segments/${id}/available-ips`, {
      params: { count }
    })
  }
}