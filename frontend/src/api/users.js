/**
 * 用户管理相关API服务
 */
import request from './request'

/**
 * 获取用户列表
 * @param {Object} params - 查询参数
 * @param {number} params.skip - 跳过的记录数
 * @param {number} params.limit - 返回的记录数
 * @param {boolean} params.active_only - 是否只返回活跃用户
 * @param {string} params.role_filter - 角色过滤器
 * @returns {Promise} 用户列表响应
 */
export function getUsers(params = {}) {
  return request({
    url: '/users/',
    method: 'get',
    params
  })
}

/**
 * 获取用户统计信息
 * @returns {Promise} 用户统计响应
 */
export function getUserStatistics() {
  return request({
    url: '/users/statistics',
    method: 'get'
  })
}

/**
 * 根据ID获取用户详情
 * @param {number} userId - 用户ID
 * @returns {Promise} 用户详情响应
 */
export function getUserById(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'get'
  })
}

/**
 * 创建新用户
 * @param {Object} userData - 用户数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.password - 密码
 * @param {string} userData.email - 邮箱地址
 * @param {string} userData.role - 用户角色
 * @returns {Promise} 创建响应
 */
export function createUser(userData) {
  return request({
    url: '/users/',
    method: 'post',
    data: userData
  })
}

/**
 * 更新用户信息
 * @param {number} userId - 用户ID
 * @param {Object} userData - 用户数据
 * @param {string} userData.username - 用户名
 * @param {string} userData.email - 邮箱地址
 * @param {string} userData.role - 用户角色
 * @param {string} userData.theme - 主题设置
 * @param {boolean} userData.is_active - 是否激活
 * @returns {Promise} 更新响应
 */
export function updateUser(userId, userData) {
  return request({
    url: `/users/${userId}`,
    method: 'put',
    data: userData
  })
}

/**
 * 删除用户
 * @param {number} userId - 用户ID
 * @returns {Promise} 删除响应
 */
export function deleteUser(userId) {
  return request({
    url: `/users/${userId}`,
    method: 'delete'
  })
}

/**
 * 重置用户密码
 * @param {number} userId - 用户ID
 * @param {Object} passwordData - 密码数据
 * @param {string} passwordData.new_password - 新密码
 * @returns {Promise} 重置响应
 */
export function resetUserPassword(userId, passwordData) {
  return request({
    url: `/users/${userId}/password`,
    method: 'put',
    data: passwordData
  })
}

/**
 * 切换用户激活状态
 * @param {number} userId - 用户ID
 * @returns {Promise} 切换响应
 */
export function toggleUserStatus(userId) {
  return request({
    url: `/users/${userId}/toggle-status`,
    method: 'put'
  })
}

/**
 * 获取可用的用户角色列表
 * @returns {Promise} 角色列表响应
 */
export function getAvailableRoles() {
  return request({
    url: '/users/roles/available',
    method: 'get'
  })
}

/**
 * 获取可用的主题列表
 * @returns {Promise} 主题列表响应
 */
export function getAvailableThemes() {
  return request({
    url: '/users/themes/available',
    method: 'get'
  })
}