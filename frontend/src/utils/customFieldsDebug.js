/**
 * 自定义字段调试工具
 * 用于诊断和修复自定义字段相关的问题
 */
import customFieldsAPI from '@/api/customFields'
import { ElMessage } from 'element-plus'

export class CustomFieldsDebugger {
    constructor() {
        this.debugMode = process.env.NODE_ENV === 'development'
    }

    /**
     * 调试日志
     */
    log(message, data = null) {
        if (this.debugMode) {
            console.log(`[CustomFields Debug] ${message}`, data)
        }
    }

    /**
     * 错误日志
     */
    error(message, error = null) {
        console.error(`[CustomFields Error] ${message}`, error)
    }

    /**
     * 安全获取自定义字段列表
     */
    async safeGetFields(entityType = null) {
        try {
            this.log('开始获取自定义字段', { entityType })

            const response = await customFieldsAPI.getFields(entityType)
            this.log('API响应', response)

            // 检查响应结构
            if (!response) {
                this.error('API返回空响应')
                return []
            }

            let fields = []

            // 处理不同的响应格式
            if (Array.isArray(response)) {
                fields = response
            } else if (response.data && Array.isArray(response.data)) {
                fields = response.data
            } else if (response.fields && Array.isArray(response.fields)) {
                fields = response.fields
            } else {
                this.error('无法识别的响应格式', response)
                return []
            }

            // 标准化字段数据
            const normalizedFields = fields.map(field => this.normalizeField(field))

            this.log('标准化后的字段', normalizedFields)
            return normalizedFields

        } catch (error) {
            this.error('获取自定义字段失败', error)

            // 根据错误类型提供友好的错误信息
            if (error.response?.status === 404) {
                ElMessage.warning('自定义字段功能暂不可用')
            } else if (error.response?.status === 401) {
                ElMessage.error('请先登录')
            } else if (error.message?.includes('name')) {
                ElMessage.error('自定义字段数据格式错误，请联系管理员')
            } else {
                ElMessage.error('获取自定义字段失败，请稍后重试')
            }

            return []
        }
    }

    /**
     * 安全获取实体的自定义字段
     */
    async safeGetEntityFields(entityType, entityId) {
        try {
            this.log('开始获取实体自定义字段', { entityType, entityId })

            const response = await customFieldsAPI.getEntityFields(entityType, entityId)
            this.log('实体字段API响应', response)

            if (!response) {
                this.error('实体字段API返回空响应')
                return { fields: [] }
            }

            let result = { fields: [] }

            // 处理不同的响应格式
            if (response.data) {
                result = response.data
            } else if (response.fields) {
                result = { fields: response.fields }
            } else if (Array.isArray(response)) {
                result = { fields: response }
            }

            // 确保fields是数组
            if (!Array.isArray(result.fields)) {
                this.error('字段数据不是数组格式', result.fields)
                result.fields = []
            }

            // 标准化字段数据
            result.fields = result.fields.map(field => this.normalizeField(field))

            this.log('标准化后的实体字段', result)
            return result

        } catch (error) {
            this.error('获取实体自定义字段失败', error)

            if (error.message?.includes('name')) {
                ElMessage.error('自定义字段数据格式错误，请联系管理员')
            } else {
                ElMessage.error('获取字段信息失败')
            }

            return { fields: [] }
        }
    }

    /**
     * 标准化字段数据
     */
    normalizeField(field) {
        if (!field || typeof field !== 'object') {
            this.error('无效的字段数据', field)
            return {
                id: 0,
                field_name: '未知字段',
                field_type: 'text',
                entity_type: 'ip',
                is_required: false,
                value: null
            }
        }

        // 确保必要的字段存在
        const normalized = {
            id: field.id || 0,
            field_name: field.field_name || field.name || '未知字段',
            field_type: field.field_type || field.type || 'text',
            entity_type: field.entity_type || 'ip',
            is_required: Boolean(field.is_required || field.required),
            field_options: field.field_options || field.options || null,
            created_at: field.created_at || field.createdAt || new Date().toISOString(),
            value: field.value || null
        }

        // 验证字段类型
        const validTypes = ['text', 'number', 'date', 'select']
        if (!validTypes.includes(normalized.field_type)) {
            this.error('无效的字段类型', normalized.field_type)
            normalized.field_type = 'text'
        }

        // 验证实体类型
        const validEntityTypes = ['ip', 'subnet']
        if (!validEntityTypes.includes(normalized.entity_type)) {
            this.error('无效的实体类型', normalized.entity_type)
            normalized.entity_type = 'ip'
        }

        return normalized
    }

    /**
     * 验证字段数据完整性
     */
    validateField(field) {
        const errors = []

        if (!field.id) {
            errors.push('缺少字段ID')
        }

        if (!field.field_name || field.field_name.trim() === '') {
            errors.push('缺少字段名称')
        }

        if (!field.field_type) {
            errors.push('缺少字段类型')
        }

        if (!field.entity_type) {
            errors.push('缺少实体类型')
        }

        if (errors.length > 0) {
            this.error('字段验证失败', { field, errors })
            return false
        }

        return true
    }

    /**
     * 修复损坏的字段数据
     */
    repairField(field) {
        if (!this.validateField(field)) {
            this.log('尝试修复字段数据', field)
            return this.normalizeField(field)
        }
        return field
    }

    /**
     * 批量修复字段数据
     */
    repairFields(fields) {
        if (!Array.isArray(fields)) {
            this.error('字段数据不是数组', fields)
            return []
        }

        return fields.map(field => this.repairField(field)).filter(field => field.id > 0)
    }

    /**
     * 检查API连接状态
     */
    async checkApiHealth() {
        try {
            this.log('检查自定义字段API健康状态')

            // 尝试获取字段列表
            const response = await customFieldsAPI.getFields()

            this.log('API健康检查通过', response)
            return true

        } catch (error) {
            this.error('API健康检查失败', error)

            if (error.response?.status === 404) {
                ElMessage.warning('自定义字段API不可用，可能是后端服务未启动')
            } else if (error.response?.status >= 500) {
                ElMessage.error('服务器错误，请联系管理员')
            } else {
                ElMessage.error('网络连接错误，请检查网络设置')
            }

            return false
        }
    }
}

// 创建全局实例
export const customFieldsDebugger = new CustomFieldsDebugger()

// 导出便捷方法
export const safeGetCustomFields = (entityType) => customFieldsDebugger.safeGetFields(entityType)
export const safeGetEntityCustomFields = (entityType, entityId) => customFieldsDebugger.safeGetEntityFields(entityType, entityId)
export const normalizeCustomField = (field) => customFieldsDebugger.normalizeField(field)
export const repairCustomFields = (fields) => customFieldsDebugger.repairFields(fields)

export default customFieldsDebugger