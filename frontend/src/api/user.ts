import { http } from '@/utils/request'
import type { User, UserCreate, UserUpdate } from '@/types'

export const userApi = {
  // 获取用户列表
  getList(params?: {
    skip?: number
    limit?: number
    department_id?: number
    is_active?: boolean
    search?: string
  }) {
    return http.get<User[]>('/v1/users', { params })
  },

  // 搜索用户
  search(params: {
    q: string
    limit?: number
  }) {
    return http.get<User[]>('/v1/users/search', { params })
  },

  // 根据ID获取用户
  getById(id: number) {
    return http.get<User>(`/v1/users/${id}`)
  },

  // 创建用户
  create(data: UserCreate) {
    return http.post<User>('/v1/users', data)
  },

  // 更新用户
  update(id: number, data: UserUpdate) {
    return http.put<User>(`/v1/users/${id}`, data)
  },

  // 删除用户
  delete(id: number) {
    return http.delete(`/v1/users/${id}`)
  },

  // 获取部门用户
  getByDepartment(departmentId: number, includeSubdepartments: boolean = false) {
    return http.get<User[]>(`/v1/users/department/${departmentId}`, {
      params: { include_subdepartments: includeSubdepartments }
    })
  },

  // 批量转移用户到新部门
  transferToDepartment(data: {
    user_ids: number[]
    new_department_id: number
  }) {
    return http.post<User[]>('/v1/users/transfer', data)
  },

  // 获取用户统计信息
  getStatistics(id: number) {
    return http.get(`/v1/users/${id}/statistics`)
  }
}