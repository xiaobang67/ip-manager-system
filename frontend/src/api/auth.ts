/**
 * 认证相关 API
 */
import { http } from '@/utils/request'
import type { AuthUser, LoginForm } from '@/stores/auth'

export interface LoginResponse {
  access_token: string
  refresh_token: string
  expires_in: number
  user: AuthUser
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface LogoutRequest {
  refresh_token: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface AuthUserData {
  id: number
  username: string
  real_name: string
  display_name: string
  email: string
  employee_id?: string
  is_admin: boolean
  is_superuser: boolean
  is_active: boolean
  department?: string
  created_at: string
  last_login?: string
  login_count: number
}

export interface AuthGroupData {
  id: number
  name: string
  display_name: string
  description?: string
  is_active: boolean
  permissions: string[]
  user_count?: number
  created_at: string
}

export interface CreateUserRequest {
  username: string
  real_name: string
  display_name?: string
  email?: string
  employee_id?: string
  department?: string
  password?: string
  is_admin?: boolean
  is_superuser?: boolean
}

export interface UpdateUserRequest {
  real_name?: string
  display_name?: string
  email?: string
  employee_id?: string
  department?: string
  password?: string
  is_admin?: boolean
  is_superuser?: boolean
  is_active?: boolean
}

export interface CreateGroupRequest {
  name: string
  display_name: string
  description?: string
  permissions?: string[]
}

export interface UpdateGroupRequest {
  display_name?: string
  description?: string
  permissions?: string[]
  is_active?: boolean
}

export interface AuthStatsResponse {
  total_users: number
  active_users: number
  local_users: number
  total_groups: number
  active_sessions: number
}

export const authApi = {
  // 用户认证
  login: (data: LoginForm): Promise<LoginResponse> => {
    return http.post('/v1/auth/login', data)
  },

  logout: (data: LogoutRequest): Promise<{ message: string }> => {
    return http.post('/v1/auth/logout', data)
  },

  refreshToken: (data: RefreshTokenRequest): Promise<LoginResponse> => {
    return http.post('/v1/auth/refresh', data)
  },

  getCurrentUser: (): Promise<AuthUser> => {
    return http.get('/v1/auth/me')
  },

  changePassword: (data: ChangePasswordRequest): Promise<{ message: string }> => {
    return http.post('/v1/auth/change-password', data)
  },

  // 用户管理
  getUsers: (params?: {
    skip?: number
    limit?: number
    search?: string
    is_active?: boolean
  }): Promise<AuthUserData[]> => {
    return http.get('/v1/auth/users', { params })
  },

  createUser: (data: CreateUserRequest): Promise<AuthUserData> => {
    return http.post('/v1/auth/users', data)
  },

  updateUser: (id: number, data: UpdateUserRequest): Promise<AuthUserData> => {
    return http.put(`/v1/auth/users/${id}`, data)
  },

  deleteUser: (id: number): Promise<{ message: string }> => {
    return http.delete(`/v1/auth/users/${id}`)
  },

  // 用户组管理
  getGroups: (params?: {
    skip?: number
    limit?: number
    search?: string
    is_active?: boolean
  }): Promise<AuthGroupData[]> => {
    return http.get('/v1/auth/groups', { params })
  },

  createGroup: (data: CreateGroupRequest): Promise<AuthGroupData> => {
    return http.post('/v1/auth/groups', data)
  },

  updateGroup: (id: number, data: UpdateGroupRequest): Promise<AuthGroupData> => {
    return http.put(`/v1/auth/groups/${id}`, data)
  },

  deleteGroup: (id: number): Promise<{ message: string }> => {
    return http.delete(`/v1/auth/groups/${id}`)
  },

  // 系统管理
  getAuthStats: (): Promise<AuthStatsResponse> => {
    return http.get('/v1/auth/stats')
  }
}