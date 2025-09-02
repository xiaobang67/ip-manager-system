/**
 * 用户管理组件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import UserManagement from '@/views/UserManagement.vue'

// Mock API calls
const mockApi = {
  getUsers: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
  updateUserRole: vi.fn(),
  getUserPermissions: vi.fn()
}

vi.mock('@/api/user', () => ({
  getUsers: (...args) => mockApi.getUsers(...args),
  createUser: (...args) => mockApi.createUser(...args),
  updateUser: (...args) => mockApi.updateUser(...args),
  deleteUser: (...args) => mockApi.deleteUser(...args),
  updateUserRole: (...args) => mockApi.updateUserRole(...args),
  getUserPermissions: (...args) => mockApi.getUserPermissions(...args)
}))

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

describe('UserManagement.vue', () => {
  let wrapper
  let store

  const mockUserData = {
    items: [
      {
        id: 1,
        username: 'admin',
        email: 'admin@company.com',
        role: 'admin',
        theme: 'light',
        is_active: true,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-01-01T00:00:00Z'
      },
      {
        id: 2,
        username: 'network_manager',
        email: 'network@company.com',
        role: 'manager',
        theme: 'dark',
        is_active: true,
        created_at: '2023-01-02T00:00:00Z',
        updated_at: '2023-01-02T00:00:00Z'
      },
      {
        id: 3,
        username: 'readonly_user',
        email: 'readonly@company.com',
        role: 'user',
        theme: 'light',
        is_active: false,
        created_at: '2023-01-03T00:00:00Z',
        updated_at: '2023-01-03T00:00:00Z'
      }
    ],
    total: 3,
    page: 1,
    size: 10
  }

  beforeEach(() => {
    vi.clearAllMocks()

    store = createStore({
      modules: {
        auth: {
          namespaced: true,
          state: {
            user: { id: 1, username: 'admin', role: 'admin' }
          },
          getters: {
            currentUser: state => state.user
          }
        }
      }
    })

    mockApi.getUsers.mockResolvedValue({ data: mockUserData })
    mockApi.getUserPermissions.mockResolvedValue({
      data: { permissions: ['user:read', 'user:write', 'user:delete'] }
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('组件渲染', () => {
    it('应该正确渲染用户管理页面', async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(wrapper.find('.user-management').exists()).toBe(true)
      expect(wrapper.find('.user-list').exists()).toBe(true)
      expect(mockApi.getUsers).toHaveBeenCalled()
    })

    it('应该显示用户列表数据', async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      const userItems = wrapper.findAll('.user-item')
      expect(userItems).toHaveLength(3)
      expect(wrapper.text()).toContain('admin')
      expect(wrapper.text()).toContain('network_manager')
      expect(wrapper.text()).toContain('readonly_user')
    })

    it('应该显示用户角色和状态', async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(wrapper.text()).toContain('超级管理员')
      expect(wrapper.text()).toContain('网络管理员')
      expect(wrapper.text()).toContain('只读用户')
      expect(wrapper.text()).toContain('活跃')
      expect(wrapper.text()).toContain('禁用')
    })
  })

  describe('用户创建', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该打开创建用户对话框', async () => {
      const createBtn = wrapper.find('.create-user-btn')
      await createBtn.trigger('click')

      expect(wrapper.find('.user-dialog').exists()).toBe(true)
      expect(wrapper.find('.dialog-title').text()).toContain('创建用户')
    })

    it('应该验证用户名格式', async () => {
      const createBtn = wrapper.find('.create-user-btn')
      await createBtn.trigger('click')

      const usernameInput = wrapper.find('input[name="username"]')
      await usernameInput.setValue('invalid user name')
      await usernameInput.trigger('blur')

      expect(wrapper.find('.username-error').text()).toContain('用户名只能包含字母、数字和下划线')
    })

    it('应该验证邮箱格式', async () => {
      const createBtn = wrapper.find('.create-user-btn')
      await createBtn.trigger('click')

      const emailInput = wrapper.find('input[name="email"]')
      await emailInput.setValue('invalid-email')
      await emailInput.trigger('blur')

      expect(wrapper.find('.email-error').text()).toContain('请输入有效的邮箱地址')
    })

    it('应该成功创建用户', async () => {
      const newUser = {
        username: 'new_user',
        email: 'newuser@company.com',
        password: 'SecurePass123!',
        role: 'user',
        theme: 'light'
      }

      mockApi.createUser.mockResolvedValue({
        data: {
          id: 4,
          ...newUser,
          is_active: true,
          created_at: '2023-01-04T00:00:00Z'
        }
      })

      const createBtn = wrapper.find('.create-user-btn')
      await createBtn.trigger('click')

      // 填写表单
      await wrapper.find('input[name="username"]').setValue(newUser.username)
      await wrapper.find('input[name="email"]').setValue(newUser.email)
      await wrapper.find('input[name="password"]').setValue(newUser.password)
      await wrapper.find('select[name="role"]').setValue(newUser.role)
      await wrapper.find('select[name="theme"]').setValue(newUser.theme)

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockApi.createUser).toHaveBeenCalledWith(expect.objectContaining({
        username: newUser.username,
        email: newUser.email,
        password: newUser.password,
        role: newUser.role,
        theme: newUser.theme
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('用户创建成功')
    })

    it('应该处理用户名重复的情况', async () => {
      mockApi.createUser.mockRejectedValue({
        response: {
          status: 409,
          data: { message: '用户名已存在' }
        }
      })

      const createBtn = wrapper.find('.create-user-btn')
      await createBtn.trigger('click')

      await wrapper.find('input[name="username"]').setValue('admin')
      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('创建失败: 用户名已存在')
    })
  })

  describe('用户编辑', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该打开编辑用户对话框', async () => {
      const editBtn = wrapper.find('.edit-user-btn')
      await editBtn.trigger('click')

      expect(wrapper.find('.user-dialog').exists()).toBe(true)
      expect(wrapper.find('.dialog-title').text()).toContain('编辑用户')
    })

    it('应该预填充现有用户数据', async () => {
      const editBtn = wrapper.find('.edit-user-btn')
      await editBtn.trigger('click')

      expect(wrapper.find('input[name="username"]').element.value).toBe('admin')
      expect(wrapper.find('input[name="email"]').element.value).toBe('admin@company.com')
      expect(wrapper.find('select[name="role"]').element.value).toBe('admin')
    })

    it('应该成功更新用户信息', async () => {
      const updatedUser = {
        id: 1,
        username: 'admin',
        email: 'admin@newcompany.com',
        role: 'admin',
        theme: 'dark'
      }

      mockApi.updateUser.mockResolvedValue({ data: updatedUser })

      const editBtn = wrapper.find('.edit-user-btn')
      await editBtn.trigger('click')

      // 修改邮箱和主题
      await wrapper.find('input[name="email"]').setValue(updatedUser.email)
      await wrapper.find('select[name="theme"]').setValue(updatedUser.theme)

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockApi.updateUser).toHaveBeenCalledWith(1, expect.objectContaining({
        email: updatedUser.email,
        theme: updatedUser.theme
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('用户信息更新成功')
    })

    it('应该禁止编辑用户名', async () => {
      const editBtn = wrapper.find('.edit-user-btn')
      await editBtn.trigger('click')

      const usernameInput = wrapper.find('input[name="username"]')
      expect(usernameInput.element.disabled).toBe(true)
    })
  })

  describe('用户删除', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该显示删除确认对话框', async () => {
      const deleteBtn = wrapper.find('.delete-user-btn')
      await deleteBtn.trigger('click')

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除用户 "admin" 吗？删除后无法恢复。',
        '确认删除',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    it('应该成功删除用户', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.deleteUser.mockResolvedValue({ data: { success: true } })

      const deleteBtn = wrapper.find('.delete-user-btn')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(mockApi.deleteUser).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('用户删除成功')
    })

    it('应该禁止删除当前登录用户', async () => {
      // 当前用户是admin (id: 1)，尝试删除自己
      const deleteBtn = wrapper.find('.delete-user-btn')

      expect(deleteBtn.element.disabled).toBe(true)
    })

    it('应该处理删除失败的情况', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.deleteUser.mockRejectedValue(new Error('用户有关联数据，无法删除'))

      const deleteBtn = wrapper.findAll('.delete-user-btn')[1] // 删除第二个用户
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('删除失败: 用户有关联数据，无法删除')
    })
  })

  describe('角色管理', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该显示角色切换按钮', () => {
      expect(wrapper.find('.role-switch').exists()).toBe(true)
    })

    it('应该成功更新用户角色', async () => {
      mockApi.updateUserRole.mockResolvedValue({
        data: {
          id: 2,
          role: 'admin'
        }
      })

      const roleSelect = wrapper.find('.role-select')
      await roleSelect.setValue('admin')
      await roleSelect.trigger('change')
      await flushPromises()

      expect(mockApi.updateUserRole).toHaveBeenCalledWith(2, 'admin')
      expect(ElMessage.success).toHaveBeenCalledWith('用户角色更新成功')
    })

    it('应该显示角色权限说明', async () => {
      const roleInfoBtn = wrapper.find('.role-info-btn')
      await roleInfoBtn.trigger('click')

      expect(wrapper.find('.role-permissions-dialog').exists()).toBe(true)
      expect(wrapper.text()).toContain('超级管理员：拥有所有权限')
      expect(wrapper.text()).toContain('网络管理员：可管理IP和网段')
      expect(wrapper.text()).toContain('只读用户：仅可查看数据')
    })
  })

  describe('用户状态管理', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该支持启用/禁用用户', async () => {
      mockApi.updateUser.mockResolvedValue({
        data: {
          id: 3,
          is_active: true
        }
      })

      const statusSwitch = wrapper.find('.status-switch')
      await statusSwitch.trigger('click')
      await flushPromises()

      expect(mockApi.updateUser).toHaveBeenCalledWith(3, expect.objectContaining({
        is_active: true
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('用户状态更新成功')
    })

    it('应该显示用户状态标识', () => {
      const statusBadges = wrapper.findAll('.status-badge')
      expect(statusBadges[0].text()).toContain('活跃')
      expect(statusBadges[1].text()).toContain('活跃')
      expect(statusBadges[2].text()).toContain('禁用')
    })
  })

  describe('搜索和过滤', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该支持按用户名搜索', async () => {
      const searchInput = wrapper.find('.search-input')
      await searchInput.setValue('admin')
      await searchInput.trigger('input')

      // 等待防抖
      await new Promise(resolve => setTimeout(resolve, 350))
      await flushPromises()

      expect(mockApi.getUsers).toHaveBeenCalledWith(expect.objectContaining({
        search: 'admin'
      }))
    })

    it('应该支持按角色过滤', async () => {
      const roleFilter = wrapper.find('.role-filter')
      await roleFilter.setValue('admin')
      await roleFilter.trigger('change')

      expect(mockApi.getUsers).toHaveBeenCalledWith(expect.objectContaining({
        role: 'admin'
      }))
    })

    it('应该支持按状态过滤', async () => {
      const statusFilter = wrapper.find('.status-filter')
      await statusFilter.setValue('active')
      await statusFilter.trigger('change')

      expect(mockApi.getUsers).toHaveBeenCalledWith(expect.objectContaining({
        is_active: true
      }))
    })
  })

  describe('密码重置', () => {
    beforeEach(async () => {
      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该显示重置密码确认对话框', async () => {
      const resetBtn = wrapper.find('.reset-password-btn')
      await resetBtn.trigger('click')

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要重置用户 "admin" 的密码吗？新密码将通过邮件发送给用户。',
        '重置密码',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    it('应该成功重置密码', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.updateUser.mockResolvedValue({
        data: {
          id: 1,
          password_reset: true
        }
      })

      const resetBtn = wrapper.find('.reset-password-btn')
      await resetBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.success).toHaveBeenCalledWith('密码重置成功，新密码已发送到用户邮箱')
    })
  })

  describe('权限检查', () => {
    it('应该根据权限显示操作按钮', async () => {
      // 模拟只读权限用户
      store = createStore({
        modules: {
          auth: {
            namespaced: true,
            state: {
              user: { id: 3, username: 'readonly_user', role: 'user' }
            },
            getters: {
              currentUser: state => state.user
            }
          }
        }
      })

      mockApi.getUserPermissions.mockResolvedValue({
        data: { permissions: ['user:read'] }
      })

      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(wrapper.find('.create-user-btn').exists()).toBe(false)
      expect(wrapper.find('.edit-user-btn').exists()).toBe(false)
      expect(wrapper.find('.delete-user-btn').exists()).toBe(false)
    })
  })

  describe('错误处理', () => {
    it('应该处理网络请求失败', async () => {
      mockApi.getUsers.mockRejectedValue(new Error('网络错误'))

      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载用户列表失败: 网络错误')
    })

    it('应该处理权限不足的情况', async () => {
      mockApi.getUsers.mockRejectedValue({ response: { status: 403 } })

      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('权限不足，无法访问用户管理')
    })

    it('应该处理服务器错误', async () => {
      mockApi.createUser.mockRejectedValue({ response: { status: 500 } })

      wrapper = mount(UserManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()

      const createBtn = wrapper.find('.create-user-btn')
      await createBtn.trigger('click')

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('服务器错误，请稍后重试')
    })
  })
})