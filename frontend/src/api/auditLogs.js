import request from './request'

/**
 * 审计日志API服务
 */
export const auditLogsApi = {
  /**
   * 搜索审计日志
   * @param {Object} searchParams - 搜索参数
   * @returns {Promise} 搜索结果
   */
  searchAuditLogs(searchParams) {
    return request.post('/audit-logs/search', searchParams)
  },

  /**
   * 获取审计日志列表
   * @param {Object} params - 查询参数
   * @returns {Promise} 审计日志列表
   */
  getAuditLogs(params = {}) {
    return request.get('/audit-logs/', { params })
  },

  /**
   * 获取单个审计日志详情
   * @param {number} logId - 日志ID
   * @returns {Promise} 审计日志详情
   */
  getAuditLog(logId) {
    return request.get(`/audit-logs/${logId}`)
  },

  /**
   * 获取实体历史记录
   * @param {string} entityType - 实体类型
   * @param {number} entityId - 实体ID
   * @param {number} limit - 限制数量
   * @returns {Promise} 实体历史记录
   */
  getEntityHistory(entityType, entityId, limit = 100) {
    return request.get(`/audit-logs/entity/${entityType}/${entityId}/history`, {
      params: { limit }
    })
  },

  /**
   * 获取用户活动记录
   * @param {number} userId - 用户ID
   * @param {Object} params - 查询参数
   * @returns {Promise} 用户活动记录
   */
  getUserActivity(userId, params = {}) {
    return request.get(`/audit-logs/user/${userId}/activity`, { params })
  },

  /**
   * 获取最近活动记录
   * @param {Object} params - 查询参数
   * @returns {Promise} 最近活动记录
   */
  getRecentActivities(params = {}) {
    return request.get('/audit-logs/recent', { params })
  },

  /**
   * 获取审计统计信息
   * @returns {Promise} 统计信息
   */
  getAuditStatistics() {
    return request.get('/audit-logs/statistics')
  },

  /**
   * 导出审计日志
   * @param {Object} exportParams - 导出参数
   * @returns {Promise} 导出文件
   */
  exportAuditLogs(exportParams) {
    return request.post('/audit-logs/export', exportParams, {
      responseType: 'blob'
    })
  },

  /**
   * 归档旧日志
   * @param {number} daysToKeep - 保留天数
   * @returns {Promise} 归档结果
   */
  archiveOldLogs(daysToKeep = 365) {
    return request.delete('/audit-logs/archive', {
      params: { days_to_keep: daysToKeep }
    })
  }
}

export default auditLogsApi