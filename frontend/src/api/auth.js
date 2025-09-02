/**
 * 认证相关API服务
 */
import request from './request'

/**
 * 用户登录
 * @param {Object} credentials - 登录凭据
 * @param {string} credentials.username - 用户名
 * @param {string} credentials.password - 密码
 * @returns {Promise} 登录响应
 */
export function login(credentials) {
  return request({
    url: '/auth/login',
    method: 'post',
    data: credentials
  })
}

/**
 * 用户登出
 * @returns {Promise} 登出响应
 */
export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

/**
 * 刷新访问令牌
 * @param {string} refreshToken - 刷新令牌
 * @returns {Promise} 刷新响应
 */
export function refreshToken(refreshToken) {
  return request({
    url: '/auth/refresh',
    method: 'post',
    data: { refresh_token: refreshToken }
  })
}

/**
 * 获取用户个人信息
 * @returns {Promise} 用户信息响应
 */
export function getProfile() {
  return request({
    url: '/auth/profile',
    method: 'get'
  })
}

/**
 * 更新用户个人信息
 * @param {Object} profileData - 个人信息数据
 * @param {string} profileData.email - 邮箱
 * @param {string} profileData.theme - 主题
 * @returns {Promise} 更新响应
 */
export function updateProfile(profileData) {
  return request({
    url: '/auth/profile',
    method: 'put',
    data: profileData
  })
}

/**
 * 修改密码
 * @param {Object} passwordData - 密码数据
 * @param {string} passwordData.old_password - 旧密码
 * @param {string} passwordData.new_password - 新密码
 * @returns {Promise} 修改响应
 */
export function changePassword(passwordData) {
  return request({
    url: '/auth/password',
    method: 'put',
    data: passwordData
  })
}

/**
 * 验证访问令牌
 * @returns {Promise} 验证响应
 */
export function verifyToken() {
  return request({
    url: '/auth/verify',
    method: 'get'
  })
}