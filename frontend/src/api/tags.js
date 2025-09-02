import request from './request'

// 标签管理
export const tagsAPI = {
  // 创建标签
  createTag(tagData) {
    return request.post('/tags/', tagData)
  },

  // 获取标签列表
  getTags(params = {}) {
    return request.get('/tags/', { params })
  },

  // 根据ID获取标签
  getTagById(tagId) {
    return request.get(`/tags/${tagId}`)
  },

  // 更新标签
  updateTag(tagId, tagData) {
    return request.put(`/tags/${tagId}`, tagData)
  },

  // 删除标签
  deleteTag(tagId) {
    return request.delete(`/tags/${tagId}`)
  },

  // 搜索标签
  searchTags(query) {
    return request.get('/tags/', { params: { search: query } })
  },

  // 为实体分配标签
  assignTags(entityType, entityId, tagIds) {
    return request.post('/tags/assign', {
      entity_type: entityType,
      entity_id: entityId,
      tag_ids: tagIds
    })
  },

  // 获取IP地址的标签
  getIPTags(ipId) {
    return request.get(`/tags/entity/ip/${ipId}`)
  },

  // 获取网段的标签
  getSubnetTags(subnetId) {
    return request.get(`/tags/entity/subnet/${subnetId}`)
  },

  // 为IP地址添加标签
  addTagToIP(ipId, tagId) {
    return request.post(`/tags/entity/ip/${ipId}/tags/${tagId}`)
  },

  // 为网段添加标签
  addTagToSubnet(subnetId, tagId) {
    return request.post(`/tags/entity/subnet/${subnetId}/tags/${tagId}`)
  },

  // 从IP地址移除标签
  removeTagFromIP(ipId, tagId) {
    return request.delete(`/tags/entity/ip/${ipId}/tags/${tagId}`)
  },

  // 从网段移除标签
  removeTagFromSubnet(subnetId, tagId) {
    return request.delete(`/tags/entity/subnet/${subnetId}/tags/${tagId}`)
  },

  // 获取标签使用统计
  getTagsUsageStats() {
    return request.get('/tags/stats/usage')
  }
}

export default tagsAPI