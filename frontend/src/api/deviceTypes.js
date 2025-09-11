/**
 * 设备类型管理API
 */
import request from './request'

// 获取设备类型列表
export const getDeviceTypes = (params = {}) => {
  return request({
    url: '/device-types',
    method: 'get',
    params
  })
}

// 获取设备类型选项（用于下拉选择）
export const getDeviceTypeOptions = () => {
  return request({
    url: '/device-types/options',
    method: 'get'
  })
}

// 创建设备类型
export const createDeviceType = (data) => {
  return request({
    url: '/device-types',
    method: 'post',
    data
  })
}

// 更新设备类型
export const updateDeviceType = (id, data) => {
  return request({
    url: `/device-types/${id}`,
    method: 'put',
    data
  })
}

// 删除设备类型
export const deleteDeviceType = (id) => {
  return request({
    url: `/device-types/${id}`,
    method: 'delete'
  })
}

// 切换设备类型状态
export const toggleDeviceTypeStatus = (id, status) => {
  return request({
    url: `/device-types/${id}/status`,
    method: 'patch',
    data: { status }
  })
}

// 获取设备类型统计信息
export const getDeviceTypeStatistics = () => {
  return request({
    url: '/device-types/statistics',
    method: 'get'
  })
}

// 获取设备类型使用情况
export const getDeviceTypeUsage = (id) => {
  return request({
    url: `/device-types/${id}/usage`,
    method: 'get'
  })
}

export default {
  getDeviceTypes,
  getDeviceTypeOptions,
  createDeviceType,
  updateDeviceType,
  deleteDeviceType,
  toggleDeviceTypeStatus,
  getDeviceTypeStatistics,
  getDeviceTypeUsage
}