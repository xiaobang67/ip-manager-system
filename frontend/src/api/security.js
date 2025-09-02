/**
 * 安全监控API
 */
import request from './request'

export const securityAPI = {
  /**
   * 获取安全仪表盘数据
   */
  getDashboard() {
    return request({
      url: '/security/dashboard',
      method: 'get'
    })
  },

  /**
   * 获取安全事件列表
   * @param {Object} params - 查询参数
   * @param {number} params.limit - 返回数量限制
   * @param {string} params.event_type - 事件类型过滤
   * @param {string} params.level - 安全级别过滤
   * @param {number} params.start_time - 开始时间戳
   * @param {number} params.end_time - 结束时间戳
   */
  getEvents(params = {}) {
    return request({
      url: '/security/events',
      method: 'get',
      params
    })
  },

  /**
   * 获取安全警报列表
   * @param {Object} params - 查询参数
   * @param {boolean} params.acknowledged - 是否已确认
   * @param {number} params.limit - 返回数量限制
   */
  getAlerts(params = {}) {
    return request({
      url: '/security/alerts',
      method: 'get',
      params
    })
  },

  /**
   * 确认安全警报
   * @param {string} alertId - 警报ID
   */
  acknowledgeAlert(alertId) {
    return request({
      url: `/security/alerts/${alertId}/acknowledge`,
      method: 'post'
    })
  },

  /**
   * 获取安全统计信息
   * @param {string} period - 统计周期 (1h, 24h, 7d, 30d)
   */
  getStatistics(period = '24h') {
    return request({
      url: '/security/statistics',
      method: 'get',
      params: { period }
    })
  },

  /**
   * 获取威胁分析报告
   */
  getThreatAnalysis() {
    return request({
      url: '/security/threat-analysis',
      method: 'get'
    })
  },

  /**
   * 测试安全事件记录（仅用于测试）
   * @param {string} eventType - 事件类型
   * @param {string} level - 安全级别
   * @param {Object} details - 事件详情
   */
  testSecurityEvent(eventType, level = 'medium', details = null) {
    return request({
      url: '/security/test-security',
      method: 'post',
      data: {
        event_type: eventType,
        level,
        details
      }
    })
  }
}

export default securityAPI