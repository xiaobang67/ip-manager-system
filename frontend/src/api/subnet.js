import request from './request'

// 网段管理API
export const subnetApi = {
  // 获取网段列表
  getSubnets(params = {}) {
    return request({
      url: '/subnets',
      method: 'get',
      params
    })
  },

  // 搜索网段
  searchSubnets(params = {}) {
    return request({
      url: '/subnets/search',
      method: 'get',
      params
    })
  },

  // 获取单个网段详情
  getSubnet(id) {
    return request({
      url: `/subnets/${id}`,
      method: 'get'
    })
  },

  // 创建网段
  createSubnet(data) {
    return request({
      url: '/subnets',
      method: 'post',
      data
    })
  },

  // 更新网段
  updateSubnet(id, data) {
    return request({
      url: `/subnets/${id}`,
      method: 'put',
      data
    })
  },

  // 删除网段
  deleteSubnet(id) {
    return request({
      url: `/subnets/${id}`,
      method: 'delete'
    })
  },

  // 验证网段
  validateSubnet(data) {
    return request({
      url: '/subnets/validate',
      method: 'post',
      data
    })
  },

  // 根据VLAN获取网段
  getSubnetsByVlan(vlanId) {
    return request({
      url: `/subnets/vlan/${vlanId}`,
      method: 'get'
    })
  },

  // 获取网段下的IP地址
  getSubnetIPs(id, params = {}) {
    return request({
      url: `/subnets/${id}/ips`,
      method: 'get',
      params
    })
  }
}