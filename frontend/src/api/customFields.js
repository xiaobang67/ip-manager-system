import request from './request'

// 自定义字段管理
export const customFieldsAPI = {
  // 创建自定义字段
  createField(fieldData) {
    return request.post('/custom-fields/', fieldData)
  },

  // 获取自定义字段列表
  getFields(entityType = null) {
    const params = entityType ? { entity_type: entityType } : {}
    return request.get('/custom-fields/', { params })
  },

  // 根据ID获取自定义字段
  getFieldById(fieldId) {
    return request.get(`/custom-fields/${fieldId}`)
  },

  // 更新自定义字段
  updateField(fieldId, fieldData) {
    return request.put(`/custom-fields/${fieldId}`, fieldData)
  },

  // 删除自定义字段
  deleteField(fieldId) {
    return request.delete(`/custom-fields/${fieldId}`)
  },

  // 获取实体的自定义字段和值
  getEntityFields(entityType, entityId) {
    return request.get(`/custom-fields/entity/${entityType}/${entityId}`)
  },

  // 批量更新实体的自定义字段值
  updateEntityFields(entityType, entityId, fieldValues) {
    return request.put(`/custom-fields/entity/${entityType}/${entityId}`, fieldValues)
  },

  // 删除实体的所有自定义字段值
  deleteEntityFields(entityType, entityId) {
    return request.delete(`/custom-fields/entity/${entityType}/${entityId}`)
  },

  // 设置单个字段值
  setFieldValue(fieldId, entityId, entityType, value) {
    return request.post('/custom-fields/values', null, {
      params: {
        field_id: fieldId,
        entity_id: entityId,
        entity_type: entityType,
        value: value
      }
    })
  }
}

export default customFieldsAPI