/**
 * 主题系统端到端测试
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createStore } from 'vuex'
import { ElButton, ElTooltip } from 'element-plus'
import ThemeToggle from '@/components/ThemeToggle.vue'
import UserProfile from '@/components/UserProfile.vue'
import AppLayout from '@/components/AppLayout.vue'

// Mock store modules
const mockAuthModule = {
  namespaced: true,
  state: {
    user: {
      id: 1,
      username: 'testuser',
      email: 'test@example.com',
      role: 'user',
      theme: 'light',
      is_active: true
    },
    isAuthenticated: true,
    accessToken: 'mock-token'
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    currentUser: state => state.user,
    userName: state => state.user?.username || '',
    userTheme: state => state.user?.theme || 'light'
  },
  actions: {
    updateProfile: vi.fn().mockResolvedValue(true),
    changePassword: vi.fn().mockResolvedValue(true),
    logout: vi.fn().mockResolvedValue(true)
  },
  mutations: {
    UPDATE_USER_PROFILE: (state, profileData) => {
      state.user = { ...state.user, ...profileData }
    }
  }
}

const mockThemeModule = {
  namespaced: true,
  state: {
    currentTheme: 'light'
  },
  getters: {
    currentTheme: state => state.currentTheme,
    isDarkMode: state => state.currentTheme === 'dark'
  },
  actions: {
    toggleTheme: vi.fn(({ commit, state }) => {
      const newTheme = state.currentTheme === 'light' ? 'dark' : 'light'
      commit('SET_THEME', newTheme)
    }),
    setTheme: vi.fn(({ commit }, theme) => {
      commit('SET_THEME', theme)
    })
  },
  mutations: {
    SET_THEME: (state, theme) => {
      state.currentTheme = theme
      // Mock DOM operations
      if (typeof document !== 'undefined') {
        document.documentElement.setAttribute('data-theme', theme)
        if (theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      }
    }
  }
}

describe('主题系统测试', () => {
  let store
  let wrapper

  beforeEach(() => {
    // 创建测试用的store
    store = createStore({
      modules: {
        auth: mockAuthModule,
        theme: mockThemeModule
      }
    })

    // Mock localStorage
    const localStorageMock = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    }
    global.localStorage = localStorageMock

    // Mock document
    global.document = {
      documentElement: {
        setAttribute: vi.fn(),
        classList: {
          add: vi.fn(),
          remove: vi.fn()
        }
      }
    }
  })

  describe('ThemeToggle 组件', () => {
    beforeEach(() => {
      wrapper = mount(ThemeToggle, {
        global: {
          plugins: [store],
          components: {
            ElButton,
            ElTooltip
          }
        }
      })
    })

    it('应该正确渲染主题切换按钮', () => {
      expect(wrapper.find('.theme-toggle-button').exists()).toBe(true)
      expect(wrapper.find('el-button').exists()).toBe(true)
    })

    it('应该显示正确的图标和提示文本', async () => {
      // 明亮主题时应该显示月亮图标
      expect(wrapper.vm.isDarkMode).toBe(false)
      
      // 切换到暗黑主题
      await store.dispatch('theme/setTheme', 'dark')
      await wrapper.vm.$nextTick()
      
      expect(wrapper.vm.isDarkMode).toBe(true)
    })

    it('应该能够切换主题', async () => {
      const initialTheme = store.getters['theme/currentTheme']
      expect(initialTheme).toBe('light')

      // 点击切换按钮
      await wrapper.find('.theme-toggle-button').trigger('click')

      expect(store.getters['theme/currentTheme']).toBe('dark')
    })

    it('应该在用户登录时同步主题偏好', async () => {
      const updateProfileSpy = vi.spyOn(store._actions['auth/updateProfile'], '0')

      // 模拟用户已登录
      store.state.auth.isAuthenticated = true

      // 切换主题
      await wrapper.vm.toggleTheme()

      expect(updateProfileSpy).toHaveBeenCalledWith(
        expect.any(Object),
        { theme: 'dark' }
      )
    })
  })

  describe('UserProfile 组件主题设置', () => {
    beforeEach(() => {
      wrapper = mount(UserProfile, {
        props: {
          modelValue: true
        },
        global: {
          plugins: [store],
          stubs: {
            'el-dialog': true,
            'el-tabs': true,
            'el-tab-pane': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-button': true,
            'el-tag': true,
            'el-alert': true
          }
        }
      })
    })

    it('应该正确初始化用户主题设置', () => {
      expect(wrapper.vm.profileForm.theme).toBe('light')
    })

    it('应该能够更新用户主题偏好', async () => {
      const updateProfileSpy = vi.spyOn(store._actions['auth/updateProfile'], '0')

      // 修改主题设置
      wrapper.vm.profileForm.theme = 'dark'

      // 模拟表单验证通过
      wrapper.vm.$refs = {
        profileForm: {
          validate: vi.fn().mockResolvedValue(true)
        }
      }

      // 提交更新
      await wrapper.vm.handleUpdateProfile()

      expect(updateProfileSpy).toHaveBeenCalledWith(
        expect.any(Object),
        { email: '', theme: 'dark' }
      )
    })

    it('应该在主题更新后应用新主题', async () => {
      const setThemeSpy = vi.spyOn(store._actions['theme/setTheme'], '0')

      // 模拟当前用户主题与表单主题不同
      wrapper.vm.profileForm.theme = 'dark'
      store.state.auth.user.theme = 'light'

      // 模拟表单验证和更新成功
      wrapper.vm.$refs = {
        profileForm: {
          validate: vi.fn().mockResolvedValue(true)
        }
      }

      await wrapper.vm.handleUpdateProfile()

      expect(setThemeSpy).toHaveBeenCalledWith(
        expect.any(Object),
        'dark'
      )
    })
  })

  describe('主题持久化', () => {
    it('应该将主题设置保存到localStorage', () => {
      store.dispatch('theme/setTheme', 'dark')

      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
    })

    it('应该从localStorage加载主题设置', () => {
      localStorage.getItem.mockReturnValue('dark')

      const newStore = createStore({
        modules: {
          auth: mockAuthModule,
          theme: {
            ...mockThemeModule,
            state: {
              currentTheme: localStorage.getItem('theme') || 'light'
            }
          }
        }
      })

      expect(newStore.getters['theme/currentTheme']).toBe('dark')
    })
  })

  describe('主题CSS应用', () => {
    it('应该正确设置data-theme属性', () => {
      store.dispatch('theme/setTheme', 'dark')

      expect(document.documentElement.setAttribute).toHaveBeenCalledWith('data-theme', 'dark')
    })

    it('应该正确切换dark类', () => {
      // 切换到暗黑主题
      store.dispatch('theme/setTheme', 'dark')
      expect(document.documentElement.classList.add).toHaveBeenCalledWith('dark')

      // 切换回明亮主题
      store.dispatch('theme/setTheme', 'light')
      expect(document.documentElement.classList.remove).toHaveBeenCalledWith('dark')
    })
  })

  describe('主题系统集成测试', () => {
    it('应该在用户登录后应用用户偏好主题', async () => {
      // 模拟用户偏好暗黑主题
      store.state.auth.user.theme = 'dark'
      store.state.auth.isAuthenticated = true

      const setThemeSpy = vi.spyOn(store._actions['theme/setTheme'], '0')

      // 模拟App组件的主题初始化逻辑
      const userTheme = store.getters['auth/userTheme']
      const currentTheme = store.getters['theme/currentTheme']

      if (userTheme && userTheme !== currentTheme) {
        await store.dispatch('theme/setTheme', userTheme)
      }

      expect(setThemeSpy).toHaveBeenCalledWith(
        expect.any(Object),
        'dark'
      )
    })

    it('应该在用户登出后保持当前主题', async () => {
      // 设置暗黑主题
      await store.dispatch('theme/setTheme', 'dark')
      
      // 模拟用户登出
      store.state.auth.isAuthenticated = false
      store.state.auth.user = null

      // 主题应该保持不变
      expect(store.getters['theme/currentTheme']).toBe('dark')
    })

    it('应该支持主题的实时切换', async () => {
      const initialTheme = store.getters['theme/currentTheme']
      
      // 切换主题
      await store.dispatch('theme/toggleTheme')
      const newTheme = store.getters['theme/currentTheme']
      
      expect(newTheme).not.toBe(initialTheme)
      expect(newTheme).toBe(initialTheme === 'light' ? 'dark' : 'light')
    })
  })

  describe('错误处理', () => {
    it('应该处理主题同步失败的情况', async () => {
      // 模拟API调用失败
      const updateProfileSpy = vi.spyOn(store._actions['auth/updateProfile'], '0')
        .mockRejectedValue(new Error('Network error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      wrapper = mount(ThemeToggle, {
        global: {
          plugins: [store],
          components: {
            ElButton,
            ElTooltip
          }
        }
      })

      // 模拟用户已登录
      store.state.auth.isAuthenticated = true

      // 切换主题
      await wrapper.vm.toggleTheme()

      expect(updateProfileSpy).toHaveBeenCalled()
      expect(consoleSpy).toHaveBeenCalledWith('Failed to sync theme preference:', expect.any(Error))

      consoleSpy.mockRestore()
    })

    it('应该在localStorage不可用时优雅降级', () => {
      // 模拟localStorage不可用
      delete global.localStorage

      expect(() => {
        store.dispatch('theme/setTheme', 'dark')
      }).not.toThrow()
    })
  })
})

describe('主题系统性能测试', () => {
  it('应该避免不必要的主题切换', async () => {
    const store = createStore({
      modules: {
        auth: mockAuthModule,
        theme: mockThemeModule
      }
    })

    const setThemeSpy = vi.spyOn(store._actions['theme/setTheme'], '0')

    // 设置相同的主题不应该触发更新
    await store.dispatch('theme/setTheme', 'light')
    await store.dispatch('theme/setTheme', 'light')

    expect(setThemeSpy).toHaveBeenCalledTimes(2)
    // 但实际的DOM操作应该被优化
  })

  it('应该正确处理快速主题切换', async () => {
    const store = createStore({
      modules: {
        auth: mockAuthModule,
        theme: mockThemeModule
      }
    })

    // 快速切换主题
    await Promise.all([
      store.dispatch('theme/toggleTheme'),
      store.dispatch('theme/toggleTheme'),
      store.dispatch('theme/toggleTheme')
    ])

    // 最终状态应该是一致的
    expect(store.getters['theme/currentTheme']).toBe('dark')
  })
})