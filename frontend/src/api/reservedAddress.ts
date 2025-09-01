import { http } from '@/utils/request'
import type { ReservedAddress, ReservedAddressCreate, ReservedAddressUpdate } from '@/types'

export const reservedAddressApi = {
  // 获取地址保留列表
  getList(params?: {
    skip?: number
    limit?: number
    network_segment_id?: number
    reserved_by_user_id?: number
    reserved_by_department_id?: number
    is_active?: boolean
    search?: string
  }) {
    return http.get<ReservedAddress[]>('/v1/reserved-addresses', { params })
  },

  // 根据ID获取地址保留
  getById(id: number) {
    return http.get<ReservedAddress>(`/v1/reserved-addresses/${id}`)
  },

  // 根据IP地址获取保留详情
  getByIp(ipAddress: string) {
    return http.get<ReservedAddress>(`/v1/reserved-addresses/by-ip/${ipAddress}`)
  },

  // 创建地址保留
  create(data: ReservedAddressCreate) {
    return http.post<ReservedAddress>('/v1/reserved-addresses', data)
  },

  // 更新地址保留
  update(id: number, data: ReservedAddressUpdate) {
    return http.put<ReservedAddress>(`/v1/reserved-addresses/${id}`, data)
  },

  // 删除地址保留
  delete(id: number) {
    return http.delete(`/v1/reserved-addresses/${id}`)
  },

  // 激活地址保留
  activate(id: number) {
    return http.post<ReservedAddress>(`/v1/reserved-addresses/${id}/activate`)
  },

  // 停用地址保留
  deactivate(id: number) {
    return http.post<ReservedAddress>(`/v1/reserved-addresses/${id}/deactivate`)
  },

  // 获取已过期的地址保留
  getExpired() {
    return http.get<ReservedAddress[]>('/v1/reserved-addresses/expired/list')
  },

  // 清理过期的地址保留
  cleanupExpired() {
    return http.post('/v1/reserved-addresses/expired/cleanup')
  },

  // 获取即将过期的地址保留
  getUpcomingExpiration(days: number = 7) {
    return http.get<ReservedAddress[]>('/v1/reserved-addresses/upcoming/expiration', {
      params: { days }
    })
  },

  // 延长地址保留期限
  extend(id: number, newEndDate: string) {
    return http.post<ReservedAddress>(`/v1/reserved-addresses/${id}/extend`, {
      new_end_date: newEndDate
    })
  },

  // 获取地址保留统计信息
  getStatistics() {
    return http.get('/v1/reserved-addresses/statistics/overview')
  }
}