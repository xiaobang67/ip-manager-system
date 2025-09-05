/**
 * 部门管理API
 */
import request from './request'

/**
 * 获取部门列表
 */
export const getDepartments = (params = {}) => {
  return request({
    url: '/departments/',
    method: 'get',
    params
  })
}

/**
 * 获取部门选项列表（用于下拉菜单）
 */
export const getDepartmentOptions = () => {
  return request({
    url: '/departments/options',
    method: 'get'
  })
}

/**
 * 获取部门统计信息
 */
export const getDepartmentStatistics = () => {
  return request({
    url: '/departments/statistics',
    method: 'get'
  })
}

/**
 * 根据ID获取部门详情
 */
export const getDepartmentById = (departmentId) => {
  return request({
    url: `/departments/${departmentId}`,
    method: 'get'
  })
}

/**
 * 创建部门
 */
export const createDepartment = (data) => {
  return request({
    url: '/departments/',
    method: 'post',
    data
  })
}

/**
 * 更新部门
 */
export const updateDepartment = (departmentId, data) => {
  return request({
    url: `/departments/${departmentId}`,
    method: 'put',
    data
  })
}

/**
 * 删除部门
 */
export const deleteDepartment = (departmentId) => {
  return request({
    url: `/departments/${departmentId}`,
    method: 'delete'
  })
}