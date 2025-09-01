import { http } from '@/utils/request'
import type { Department, DepartmentCreate, DepartmentUpdate } from '@/types'

export const departmentApi = {
  // 获取部门列表
  getList(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }) {
    return http.get<Department[]>('/v1/departments', { params })
  },

  // 获取部门树形结构
  getTree() {
    return http.get<Department[]>('/v1/departments/tree')
  },

  // 根据ID获取部门
  getById(id: number) {
    return http.get<Department>(`/v1/departments/${id}`)
  },

  // 创建部门
  create(data: DepartmentCreate) {
    return http.post<Department>('/v1/departments', data)
  },

  // 更新部门
  update(id: number, data: DepartmentUpdate) {
    return http.put<Department>(`/v1/departments/${id}`, data)
  },

  // 删除部门
  delete(id: number) {
    return http.delete(`/v1/departments/${id}`)
  },

  // 获取子部门
  getChildren(id: number) {
    return http.get<Department[]>(`/v1/departments/${id}/children`)
  },

  // 获取部门统计信息
  getStatistics(id: number) {
    return http.get(`/v1/departments/${id}/statistics`)
  }
}