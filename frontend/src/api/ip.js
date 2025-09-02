import request from './request'

/**
 * IP地址管理API
 */
export const ipAPI = {
  /**
   * 获取IP地址列表
   * @param {Object} params - 查询参数
   * @returns {Promise}
   */
  getIPs(params = {}) {
    return request({
      url: '/ips',
      method: 'get',
      params
    })
  },

  /**
   * 搜索IP地址
   * @param {Object} params - 搜索参数
   * @returns {Promise}
   */
  searchIPs(params = {}) {
    return request({
      url: '/ips/search',
      method: 'get',
      params
    })
  },

  /**
   * 高级搜索IP地址
   * @param {Object} data - 搜索数据
   * @returns {Promise}
   */
  advancedSearchIPs(data) {
    return request({
      url: '/ips/advanced-search',
      method: 'post',
      data
    })
  },

  /**
   * 分配IP地址
   * @param {Object} data - 分配数据
   * @returns {Promise}
   */
  allocateIP(data) {
    return request({
      url: '/ips/allocate',
      method: 'post',
      data
    })
  },

  /**
   * 保留IP地址
   * @param {Object} data - 保留数据
   * @returns {Promise}
   */
  reserveIP(data) {
    return request({
      url: '/ips/reserve',
      method: 'post',
      data
    })
  },

  /**
   * 释放IP地址
   * @param {Object} data - 释放数据
   * @returns {Promise}
   */
  releaseIP(data) {
    return request({
      url: '/ips/release',
      method: 'post',
      data
    })
  },

  /**
   * 获取IP地址统计信息
   * @param {number} subnetId - 网段ID（可选）
   * @returns {Promise}
   */
  getStatistics(subnetId = null) {
    const params = {}
    if (subnetId) {
      params.subnet_id = subnetId
    }
    return request({
      url: '/ips/statistics',
      method: 'get',
      params
    })
  },

  /**
   * 检测IP地址冲突
   * @param {number} subnetId - 网段ID（可选）
   * @returns {Promise}
   */
  getConflicts(subnetId = null) {
    const params = {}
    if (subnetId) {
      params.subnet_id = subnetId
    }
    return request({
      url: '/ips/conflicts',
      method: 'get',
      params
    })
  },

  /**
   * 获取IP地址范围状态
   * @param {Object} data - 范围数据
   * @returns {Promise}
   */
  getRangeStatus(data) {
    return request({
      url: '/ips/range-status',
      method: 'post',
      data
    })
  },

  /**
   * 批量IP地址操作
   * @param {Object} data - 批量操作数据
   * @returns {Promise}
   */
  bulkOperation(data) {
    return request({
      url: '/ips/bulk-operation',
      method: 'post',
      data
    })
  },

  /**
   * 获取IP地址历史记录
   * @param {string} ipAddress - IP地址
   * @returns {Promise}
   */
  getIPHistory(ipAddress) {
    return request({
      url: `/ips/${ipAddress}/history`,
      method: 'get'
    })
  },

  /**
   * 同步网段IP地址
   * @param {number} subnetId - 网段ID
   * @param {string} network - 网段CIDR
   * @returns {Promise}
   */
  syncSubnetIPs(subnetId, network) {
    return request({
      url: `/ips/sync`,
      method: 'post',
      data: {
        subnet_id: subnetId,
        network: network
      }
    })
  },

  /**
   * 获取可用IP地址
   * @param {number} subnetId - 网段ID
   * @param {number} limit - 限制数量
   * @returns {Promise}
   */
  getAvailableIPs(subnetId, limit = 10) {
    return request({
      url: '/ips/available',
      method: 'get',
      params: {
        subnet_id: subnetId,
        limit: limit
      }
    })
  },

  /**
   * 验证IP地址格式
   * @param {string} ipAddress - IP地址
   * @returns {Promise}
   */
  validateIP(ipAddress) {
    return request({
      url: '/ips/validate',
      method: 'post',
      data: {
        ip_address: ipAddress
      }
    })
  },

  /**
   * 获取IP地址详情
   * @param {string} ipAddress - IP地址
   * @returns {Promise}
   */
  getIPDetail(ipAddress) {
    return request({
      url: `/ips/${ipAddress}`,
      method: 'get'
    })
  },

  /**
   * 更新IP地址信息
   * @param {string} ipAddress - IP地址
   * @param {Object} data - 更新数据
   * @returns {Promise}
   */
  updateIP(ipAddress, data) {
    return request({
      url: `/ips/${ipAddress}`,
      method: 'put',
      data
    })
  },

  /**
   * 导出IP地址列表
   * @param {Object} params - 导出参数
   * @returns {Promise}
   */
  exportIPs(params = {}) {
    return request({
      url: '/ips/export',
      method: 'get',
      params,
      responseType: 'blob'
    })
  },

  /**
   * 导入IP地址
   * @param {FormData} formData - 文件数据
   * @returns {Promise}
   */
  importIPs(formData) {
    return request({
      url: '/ips/import',
      method: 'post',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  /**
   * 获取搜索历史
   * @param {number} limit - 限制数量
   * @returns {Promise}
   */
  getSearchHistory(limit = 20) {
    return request({
      url: '/ips/search-history',
      method: 'get',
      params: { limit }
    })
  },

  /**
   * 获取收藏的搜索
   * @returns {Promise}
   */
  getSearchFavorites() {
    return request({
      url: '/ips/search-favorites',
      method: 'get'
    })
  },

  /**
   * 保存搜索历史
   * @param {Object} data - 搜索数据
   * @returns {Promise}
   */
  saveSearchHistory(data) {
    return request({
      url: '/ips/search-history',
      method: 'post',
      data
    })
  },

  /**
   * 切换搜索收藏状态
   * @param {number} searchId - 搜索ID
   * @returns {Promise}
   */
  toggleSearchFavorite(searchId) {
    return request({
      url: `/ips/search-history/${searchId}/favorite`,
      method: 'put'
    })
  },

  /**
   * 更新搜索名称
   * @param {number} searchId - 搜索ID
   * @param {string} searchName - 搜索名称
   * @returns {Promise}
   */
  updateSearchName(searchId, searchName) {
    return request({
      url: `/ips/search-history/${searchId}/name`,
      method: 'put',
      params: { search_name: searchName }
    })
  },

  /**
   * 删除搜索历史
   * @param {number} searchId - 搜索ID
   * @returns {Promise}
   */
  deleteSearchHistory(searchId) {
    return request({
      url: `/ips/search-history/${searchId}`,
      method: 'delete'
    })
  }
}

export default ipAPI