/**
 * 认证状态管理 Store
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi } from '@/api/auth'
import router from '@/router'

export interface AuthUser {
  id: number
  username: string
  real_name: string
  display_name: string
  email: string
  employee_id?: string
  is_admin: boolean
  is_superuser: boolean
  department?: string
  groups: string[]
  permissions: string[]
}

export interface LoginForm {
  username: string
  password: string
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const user = ref<AuthUser | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const isLoading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.is_admin || false)
  const isSuperuser = computed(() => user.value?.is_superuser || false)
  const userDisplayName = computed(() => {
    if (!user.value) return ''
    return user.value.display_name || user.value.real_name || user.value.username
  })

  // 设置令牌
  const setTokens = (accessToken: string, refresh?: string) => {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)
    
    if (refresh) {
      refreshToken.value = refresh
      localStorage.setItem('refresh_token', refresh)
    }
  }

  // 清除令牌
  const clearTokens = () => {
    token.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  // 登录
  const login = async (loginForm: LoginForm): Promise<boolean> => {
    isLoading.value = true
    try {
      const response = await authApi.login(loginForm)
      
      // 保存令牌
      setTokens(response.access_token, response.refresh_token)
      
      // 保存用户信息
      user.value = {
        id: response.user.id,
        username: response.user.username,
        real_name: response.user.real_name,
        display_name: response.user.display_name,
        email: response.user.email,
        employee_id: response.user.employee_id,
        is_admin: response.user.is_admin,
        is_superuser: response.user.is_superuser,
        department: response.user.department,
        groups: response.user.groups || [],
        permissions: response.user.permissions || []
      }
      
      ElMessage.success('登录成功')
      return true
    } catch (error: any) {
      console.error('登录失败:', error)
      const message = error.response?.data?.message || error.message || '登录失败'
      ElMessage.error(message)
      return false
    } finally {
      isLoading.value = false
    }
  }

  // 登出
  const logout = async () => {
    try {
      if (refreshToken.value) {
        await authApi.logout({ refresh_token: refreshToken.value })
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      // 清除本地状态
      user.value = null
      clearTokens()
      
      // 跳转到登录页
      router.push('/login')
      ElMessage.success('已退出登录')
    }
  }

  // 获取当前用户信息
  const fetchUserInfo = async (): Promise<boolean> => {
    if (!token.value) return false
    
    try {
      const userInfo = await authApi.getCurrentUser()
      user.value = {
        id: userInfo.id,
        username: userInfo.username,
        real_name: userInfo.real_name,
        display_name: userInfo.display_name,
        email: userInfo.email,
        employee_id: userInfo.employee_id,
        is_admin: userInfo.is_admin,
        is_superuser: userInfo.is_superuser,
        department: userInfo.department,
        groups: userInfo.groups || [],
        permissions: userInfo.permissions || []
      }
      return true
    } catch (error: any) {
      console.error('获取用户信息失败:', error)
      if (error.response?.status === 401) {
        // token 过期或无效，尝试刷新
        return await refreshTokenAction()
      }
      return false
    }
  }

  // 刷新令牌
  const refreshTokenAction = async (): Promise<boolean> => {
    if (!refreshToken.value) {
      await logout()
      return false
    }

    try {
      const response = await authApi.refreshToken({ refresh_token: refreshToken.value })
      
      // 更新令牌
      setTokens(response.access_token, response.refresh_token)
      
      // 更新用户信息
      user.value = {
        id: response.user.id,
        username: response.user.username,
        real_name: response.user.real_name,
        display_name: response.user.display_name,
        email: response.user.email,
        employee_id: response.user.employee_id,
        is_admin: response.user.is_admin,
        is_superuser: response.user.is_superuser,
        department: response.user.department,
        groups: response.user.groups || [],
        permissions: response.user.permissions || []
      }
      
      return true
    } catch (error) {
      console.error('刷新令牌失败:', error)
      await logout()
      return false
    }
  }

  // 修改密码
  const changePassword = async (oldPassword: string, newPassword: string): Promise<boolean> => {
    try {
      await authApi.changePassword({
        old_password: oldPassword,
        new_password: newPassword
      })
      ElMessage.success('密码修改成功')
      return true
    } catch (error: any) {
      console.error('修改密码失败:', error)
      const message = error.response?.data?.message || '修改密码失败'
      ElMessage.error(message)
      return false
    }
  }

  // 检查权限
  const hasPermission = (permission: string): boolean => {
    if (!user.value) return false
    return user.value.permissions.includes(permission)
  }

  // 检查是否在指定组中
  const hasGroup = (groupName: string): boolean => {
    if (!user.value) return false
    return user.value.groups.includes(groupName)
  }

  // 初始化认证状态
  const initAuth = async (): Promise<boolean> => {
    if (!token.value) return false
    
    // 尝试获取用户信息
    const success = await fetchUserInfo()
    if (!success) {
      clearTokens()
      return false
    }
    
    return true
  }

  return {
    // 状态
    user,
    token,
    refreshToken,
    isLoading,
    
    // 计算属性
    isLoggedIn,
    isAdmin,
    isSuperuser,
    userDisplayName,
    
    // 方法
    login,
    logout,
    fetchUserInfo,
    refreshTokenAction,
    changePassword,
    hasPermission,
    hasGroup,
    initAuth,
    setTokens,
    clearTokens
  }
})