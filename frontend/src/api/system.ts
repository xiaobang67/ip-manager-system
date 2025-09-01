/**
 * 系统管理相关 API
 */
import request from '@/utils/request'

export interface LDAPConfig {
  enable_ldap: boolean
  server_uri: string
  bind_dn: string
  bind_password: string
  user_search_base: string
  user_search_filter: string
  group_search_base: string
  group_search_filter: string
  connect_timeout: number
  read_timeout: number
  always_update_user: boolean
}

export interface TestLDAPResponse {
  success: boolean
  message: string
}

export interface OperationLog {
  timestamp: string
  user: string
  action: string
  target: string
  description: string
  ip: string
  status: 'success' | 'error'
}

export interface PaginatedLogsResponse {
  items: OperationLog[]
  total: number
}

export const systemApi = {
  // LDAP配置
  getLDAPConfig: (): Promise<LDAPConfig> => {
    return request.get('/api/v1/system/ldap-config')
  },

  saveLDAPConfig: (data: Partial<LDAPConfig>): Promise<{ message: string }> => {
    return request.post('/api/v1/system/ldap-config', data)
  },

  testLDAPConnection: (data: Partial<LDAPConfig>): Promise<TestLDAPResponse> => {
    return request.post('/api/v1/system/ldap-test', data)
  },

  // 操作日志
  getOperationLogs: (params: {
    skip?: number
    limit?: number
  }): Promise<PaginatedLogsResponse> => {
    return request.get('/v1/system/logs', { params })
  }
}