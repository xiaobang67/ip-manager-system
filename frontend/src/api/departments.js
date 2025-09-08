/**
 * 部门管理API
 */
import request from './request'

/**
 * 获取部门列表
 */
export const getDepartments = (params = {}) => {
  console.log('发送部门列表请求:', params)
  return request({
    url: '/departments/',
    method: 'get',
    params
  }).then(response => {
    console.log('部门列表响应:', response)
    return response
  }).catch(error => {
    console.error('部门列表请求失败:', error)
    throw error
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