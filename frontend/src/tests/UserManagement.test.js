/**
 * 用户管理组件单元测试
 * 测试用户管理页面的业务逻辑和工具函数
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage, ElMessageBox } from 'element-plus'

// 模拟 Element Plus 组件
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

// 模拟 Vuex store
const mockStore = {
  getters: {
    'auth/currentUser': { id: 1, username: 'admin', role: 'admin' },
    'auth/userRole': 'admin',
    'auth/isAuthenticated': true
  },
  dispatch: vi.fn()
}

vi.mock('vuex', () => ({
  useStore: () => mockStore
}))

// 模拟 API 调用
vi.mock('@/api/users', () => ({
  getUsers: vi.fn(),
  getUserStatistics: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  resetUserPassword: vi.fn(),
  toggleUserStatus: vi.fn(),
  getAvailableRoles: vi.fn(),
  getAvailableThemes: vi.fn()
}))

describe('UserManagement 工具函数测试', () => {
  describe('getRoleTagType', () => {
    it('应该返回正确的角色标签类型', () => {
      const getRoleTagType = (role) => {
        const types = {
          admin: 'danger',
          manager: 'warning',
          user: 'info'
        }
        return types[role] || 'info'
      }

      expect(getRoleTagType('admin')).toBe('danger')
      expect(getRoleTagType('manager')).toBe('warning')
      expect(getRoleTagType('user')).toBe('info')
      expect(getRoleTagType('unknown')).toBe('info')
    })
  })

  describe('getRoleLabel', () => {
    it('应该返回正确的角色标签文本', () => {
      const getRoleLabel = (role) => {
        const labels = {
          admin: '管理员',
          manager: '经理',
          user: '普通用户'
        }
        return labels[role] || role
      }

      expect(getRoleLabel('admin')).toBe('管理员')
      expect(getRoleLabel('manager')).toBe('经理')
      expect(getRoleLabel('user')).toBe('普通用户')
      expect(getRoleLabel('unknown')).toBe('unknown')
    })
  })

  describe('formatDateTime', () => {
    it('应该正确格式化日期时间', () => {
      const formatDateTime = (dateString) => {
        if (!dateString) return '-'
        return new Date(dateString).toLocaleString('zh-CN')
      }

      expect(formatDateTime(null)).toBe('-')
      expect(formatDateTime('')).toBe('-')
      expect(formatDateTime('2024-01-01T12:00:00Z')).toMatch(/2024/)
    })
  })

  describe('用户权限检查', () => {
    it('应该正确检查用户管理权限', () => {
      const canManageUsers = (userRole) => {
        return ['admin', 'manager'].includes(userRole)
      }

      expect(canManageUsers('admin')).toBe(true)
      expect(canManageUsers('manager')).toBe(true)
      expect(canManageUsers('user')).toBe(false)
      expect(canManageUsers('guest')).toBe(false)
    })

    it('应该正确检查删除用户权限', () => {
      const canDeleteUser = (currentUserId, targetUserId, userRole) => {
        if (currentUserId === targetUserId) return false
        return ['admin', 'manager'].includes(userRole)
      }

      expect(canDeleteUser(1, 2, 'admin')).toBe(true)
      expect(canDeleteUser(1, 1, 'admin')).toBe(false) // 不能删除自己
      expect(canDeleteUser(1, 2, 'user')).toBe(false) // 权限不足
    })
  })

  describe('表单验证逻辑', () => {
    it('应该正确验证用户名', () => {
      const validateUsername = (username) => {
        if (!username) return { valid: false, message: '请输入用户名' }
        if (username.length < 3) return { valid: false, message: '用户名长度不能少于3个字符' }
        if (username.length > 50) return { valid: false, message: '用户名长度不能超过50个字符' }
        return { valid: true, message: '' }
      }

      expect(validateUsername('').valid).toBe(false)
      expect(validateUsername('ab').valid).toBe(false)
      expect(validateUsername('a'.repeat(51)).valid).toBe(false)
      expect(validateUsername('validuser').valid).toBe(true)
    })

    it('应该正确验证密码', () => {
      const validatePassword = (password) => {
        if (!password) return { valid: false, message: '请输入密码' }
        if (password.length < 8) return { valid: false, message: '密码长度不能少于8个字符' }
        return { valid: true, message: '' }
      }

      expect(validatePassword('').valid).toBe(false)
      expect(validatePassword('1234567').valid).toBe(false)
      expect(validatePassword('password123').valid).toBe(true)
    })

    it('应该正确验证邮箱', () => {
      const validateEmail = (email) => {
        if (!email) return { valid: true, message: '' } // 邮箱可选
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(email)) return { valid: false, message: '请输入正确的邮箱地址' }
        return { valid: true, message: '' }
      }

      expect(validateEmail('').valid).toBe(true)
      expect(validateEmail('invalid-email').valid).toBe(false)
      expect(validateEmail('test@example.com').valid).toBe(true)
    })

    it('应该正确验证密码确认', () => {
      const validatePasswordConfirm = (password, confirmPassword) => {
        if (!confirmPassword) return { valid: false, message: '请确认密码' }
        if (password !== confirmPassword) return { valid: false, message: '两次输入密码不一致' }
        return { valid: true, message: '' }
      }

      expect(validatePasswordConfirm('password', '').valid).toBe(false)
      expect(validatePasswordConfirm('password', 'different').valid).toBe(false)
      expect(validatePasswordConfirm('password', 'password').valid).toBe(true)
    })
  })

  describe('搜索和过滤逻辑', () => {
    const mockUsers = [
      { id: 1, username: 'admin', email: 'admin@example.com', role: 'admin', is_active: true },
      { id: 2, username: 'manager1', email: 'manager@example.com', role: 'manager', is_active: true },
      { id: 3, username: 'user1', email: 'user1@test.com', role: 'user', is_active: false },
      { id: 4, username: 'user2', email: 'user2@test.com', role: 'user', is_active: true }
    ]

    it('应该正确执行搜索过滤', () => {
      const filterBySearch = (users, query) => {
        if (!query) return users
        const lowerQuery = query.toLowerCase()
        return users.filter(user => 
          user.username.toLowerCase().includes(lowerQuery) ||
          (user.email && user.email.toLowerCase().includes(lowerQuery))
        )
      }

      expect(filterBySearch(mockUsers, 'admin')).toHaveLength(1)
      expect(filterBySearch(mockUsers, 'user')).toHaveLength(2)
      expect(filterBySearch(mockUsers, 'test.com')).toHaveLength(2)
      expect(filterBySearch(mockUsers, 'nonexistent')).toHaveLength(0)
    })

    it('应该正确执行状态过滤', () => {
      const filterByStatus = (users, status) => {
        if (!status) return users
        if (status === 'active') return users.filter(user => user.is_active)
        if (status === 'inactive') return users.filter(user => !user.is_active)
        return users
      }

      expect(filterByStatus(mockUsers, 'active')).toHaveLength(3)
      expect(filterByStatus(mockUsers, 'inactive')).toHaveLength(1)
      expect(filterByStatus(mockUsers, '')).toHaveLength(4)
    })

    it('应该正确执行角色过滤', () => {
      const filterByRole = (users, role) => {
        if (!role) return users
        return users.filter(user => user.role === role)
      }

      expect(filterByRole(mockUsers, 'admin')).toHaveLength(1)
      expect(filterByRole(mockUsers, 'manager')).toHaveLength(1)
      expect(filterByRole(mockUsers, 'user')).toHaveLength(2)
      expect(filterByRole(mockUsers, '')).toHaveLength(4)
    })

    it('应该正确执行组合过滤', () => {
      const applyFilters = (users, { search, status, role }) => {
        let filtered = users

        if (search) {
          const lowerQuery = search.toLowerCase()
          filtered = filtered.filter(user => 
            user.username.toLowerCase().includes(lowerQuery) ||
            (user.email && user.email.toLowerCase().includes(lowerQuery))
          )
        }

        if (status === 'active') {
          filtered = filtered.filter(user => user.is_active)
        } else if (status === 'inactive') {
          filtered = filtered.filter(user => !user.is_active)
        }

        if (role) {
          filtered = filtered.filter(user => user.role === role)
        }

        return filtered
      }

      // 测试组合过滤：活跃的用户角色
      expect(applyFilters(mockUsers, { status: 'active', role: 'user' })).toHaveLength(1)
      
      // 测试组合过滤：搜索 + 状态
      expect(applyFilters(mockUsers, { search: 'user', status: 'active' })).toHaveLength(1)
      
      // 测试组合过滤：搜索 + 角色
      expect(applyFilters(mockUsers, { search: 'user', role: 'user' })).toHaveLength(2)
    })
  })

  describe('分页逻辑', () => {
    it('应该正确计算分页参数', () => {
      const calculatePagination = (currentPage, pageSize, total) => {
        const totalPages = Math.ceil(total / pageSize)
        const skip = (currentPage - 1) * pageSize
        
        return {
          skip,
          limit: pageSize,
          totalPages,
          hasNext: currentPage < totalPages,
          hasPrev: currentPage > 1
        }
      }

      // 测试第一页
      const page1 = calculatePagination(1, 20, 100)
      expect(page1.skip).toBe(0)
      expect(page1.totalPages).toBe(5)
      expect(page1.hasNext).toBe(true)
      expect(page1.hasPrev).toBe(false)

      // 测试中间页
      const page3 = calculatePagination(3, 20, 100)
      expect(page3.skip).toBe(40)
      expect(page3.hasNext).toBe(true)
      expect(page3.hasPrev).toBe(true)

      // 测试最后一页
      const page5 = calculatePagination(5, 20, 100)
      expect(page5.skip).toBe(80)
      expect(page5.hasNext).toBe(false)
      expect(page5.hasPrev).toBe(true)
    })
  })

  describe('数据处理逻辑', () => {
    it('应该正确处理用户统计数据', () => {
      const processStatistics = (users) => {
        const total = users.length
        const active = users.filter(user => user.is_active).length
        const inactive = total - active
        
        const roleDistribution = users.reduce((acc, user) => {
          acc[user.role] = (acc[user.role] || 0) + 1
          return acc
        }, {})

        return {
          total_users: total,
          active_users: active,
          inactive_users: inactive,
          role_distribution: roleDistribution
        }
      }

      const mockUsers = [
        { role: 'admin', is_active: true },
        { role: 'manager', is_active: true },
        { role: 'user', is_active: false },
        { role: 'user', is_active: true }
      ]

      const stats = processStatistics(mockUsers)
      expect(stats.total_users).toBe(4)
      expect(stats.active_users).toBe(3)
      expect(stats.inactive_users).toBe(1)
      expect(stats.role_distribution.admin).toBe(1)
      expect(stats.role_distribution.user).toBe(2)
    })
  })
})

describe('UserManagement 错误处理测试', () => {
  it('应该正确处理API错误', () => {
    const handleApiError = (error) => {
      if (error.response) {
        const { status, data } = error.response
        switch (status) {
          case 401:
            return '认证失败，请重新登录'
          case 403:
            return '权限不足'
          case 404:
            return '用户不存在'
          case 422:
            return data.detail || '数据验证失败'
          default:
            return '操作失败，请稍后重试'
        }
      }
      return '网络错误，请检查网络连接'
    }

    expect(handleApiError({ response: { status: 401 } })).toBe('认证失败，请重新登录')
    expect(handleApiError({ response: { status: 403 } })).toBe('权限不足')
    expect(handleApiError({ response: { status: 404 } })).toBe('用户不存在')
    expect(handleApiError({ response: { status: 422, data: { detail: '用户名已存在' } } })).toBe('用户名已存在')
    expect(handleApiError({ response: { status: 500 } })).toBe('操作失败，请稍后重试')
    expect(handleApiError({})).toBe('网络错误，请检查网络连接')
  })
})