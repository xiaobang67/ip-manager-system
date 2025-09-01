import { http } from '@/utils/request'
import type { IPAddress, IPAddressCreate, IPAddressUpdate, IPStatus } from '@/types'

export const ipAddressApi = {
  // 获取IP地址列表
  getList(params?: {
    skip?: number
    limit?: number
    network_segment_id?: number
    status?: IPStatus
    assigned_user_id?: number
    assigned_department_id?: number
    search?: string
  }) {
    return http.get<PaginatedResponse<IPAddress>>('/v1/ip-addresses', { params })
  },

  // 根据ID获取IP地址
  getById(id: number) {
    return http.get<IPAddress>(`/v1/ip-addresses/${id}`)
  },

  // 根据IP地址获取详情
  getByIp(ipAddress: string) {
    return http.get<IPAddress>(`/v1/ip-addresses/by-ip/${ipAddress}`)
  },

  // 创建IP地址记录
  create(data: IPAddressCreate) {
    return http.post<IPAddress>('/v1/ip-addresses', data)
  },

  // 更新IP地址
  update(id: number, data: IPAddressUpdate) {
    return http.put<IPAddress>(`/v1/ip-addresses/${id}`, data)
  },

  // 删除IP地址
  delete(id: number) {
    return http.delete(`/v1/ip-addresses/${id}`)
  },

  // 分配IP地址
  allocate(id: number, data?: {
    user_id?: number
    department_id?: number
    device_name?: string
    device_type?: string
    mac_address?: string
    hostname?: string
    os_type?: string
    purpose?: string
  }) {
    return http.post<IPAddress>(`/v1/ip-addresses/${id}/allocate`, data)
  },

  // 释放IP地址
  release(id: number) {
    return http.post<IPAddress>(`/v1/ip-addresses/${id}/release`)
  },

  // 获取IP地址使用历史
  getHistory(ipAddress: string) {
    return http.get(`/v1/ip-addresses/${ipAddress}/history`)
  },

  // 批量分配IP地址
  batchAllocate(data: {
    segment_id: number
    count: number
    user_id?: number
    department_id?: number
  }) {
    return http.post<IPAddress[]>('/v1/ip-addresses/batch-allocate', data)
  },

  // 获取操作系统选项
  getOSTypes() {
    return http.get<Array<{label: string, value: string}>>('/v1/ip-addresses/options/os-types')
  }
}