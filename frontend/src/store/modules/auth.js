import * as authAPI from '@/api/auth'

// 从localStorage获取存储的认证信息
const getStoredAuth = () => {
  try {
    const accessToken = localStorage.getItem('access_token')
    const refreshToken = localStorage.getItem('refresh_token')
    const user = localStorage.getItem('user')

    return {
      accessToken,
      refreshToken,
      user: user ? JSON.parse(user) : null
    }
  } catch (error) {
    console.error('Error parsing stored auth data:', error)
    // 只有在解析用户数据失败时才清除数据
    if (localStorage.getItem('user')) {
      localStorage.removeItem('user')
    }
    return {
      accessToken: localStorage.getItem('access_token'),
      refreshToken: localStorage.getItem('refresh_token'),
      user: null
    }
  }
}

const storedAuth = getStoredAuth()

const state = {
  accessToken: storedAuth.accessToken,
  refreshToken: storedAuth.refreshToken,
  user: storedAuth.user,
  isAuthenticated: !!storedAuth.accessToken,
  loginLoading: false,
  // 会话超时相关
  sessionTimeout: 10 * 60 * 1000, // 10分钟，单位毫秒
  lastActivityTime: Date.now(),
  timeoutTimer: null,
  showTimeoutWarning: false
}

const getters = {
  isAuthenticated: state => state.isAuthenticated,
  accessToken: state => state.accessToken,
  refreshToken: state => state.refreshToken,
  currentUser: state => state.user,
  userRole: state => state.user?.role || null,
  userName: state => state.user?.username || '',
  userEmail: state => state.user?.email || '',
  loginLoading: state => state.loginLoading,
  // 会话超时相关
  showTimeoutWarning: state => state.showTimeoutWarning,
  sessionTimeout: state => state.sessionTimeout,
  lastActivityTime: state => state.lastActivityTime
}

const mutations = {
  SET_ACCESS_TOKEN(state, token) {
    state.accessToken = token
    state.isAuthenticated = !!token

    if (token) {
      localStorage.setItem('access_token', token)
    } else {
      localStorage.removeItem('access_token')
    }
  },

  SET_REFRESH_TOKEN(state, token) {
    state.refreshToken = token

    if (token) {
      localStorage.setItem('refresh_token', token)
    } else {
      localStorage.removeItem('refresh_token')
    }
  },

  SET_USER(state, user) {
    state.user = user

    if (user) {
      localStorage.setItem('user', JSON.stringify(user))
    } else {
      localStorage.removeItem('user')
    }
  },

  SET_LOGIN_LOADING(state, loading) {
    state.loginLoading = loading
  },

  CLEAR_AUTH(state) {
    state.accessToken = null
    state.refreshToken = null
    state.user = null
    state.isAuthenticated = false
    state.loginLoading = false

    // 清除会话超时相关状态
    if (state.timeoutTimer) {
      clearTimeout(state.timeoutTimer)
      state.timeoutTimer = null
    }
    state.showTimeoutWarning = false
    state.lastActivityTime = Date.now()

    // 清除localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },

  UPDATE_USER_PROFILE(state, profileData) {
    if (state.user) {
      state.user = { ...state.user, ...profileData }
      localStorage.setItem('user', JSON.stringify(state.user))
    }
  },

  // 会话超时相关mutations
  UPDATE_LAST_ACTIVITY(state) {
    state.lastActivityTime = Date.now()
  },

  SET_TIMEOUT_TIMER(state, timer) {
    // 清除之前的定时器
    if (state.timeoutTimer) {
      clearTimeout(state.timeoutTimer)
    }
    state.timeoutTimer = timer
  },

  SET_TIMEOUT_WARNING(state, show) {
    state.showTimeoutWarning = show
  },

  CLEAR_TIMEOUT_TIMER(state) {
    if (state.timeoutTimer) {
      clearTimeout(state.timeoutTimer)
      state.timeoutTimer = null
    }
  }
}

const actions = {
  /**
   * 用户登录
   * @param {Object} context - Vuex上下文
   * @param {Object} credentials - 登录凭据
   * @returns {Promise<Object>} 登录结果
   */
  async login({ commit, dispatch }, credentials) {
    commit('SET_LOGIN_LOADING', true)

    try {
      // 登录前先清除所有认证信息，确保没有缓存问题
      commit('CLEAR_AUTH')

      const response = await authAPI.login(credentials)
      const { access_token, refresh_token, user } = response

      console.log('登录成功，用户信息:', user)

      // 验证返回的用户信息与请求的用户名是否一致
      if (user.username !== credentials.username) {
        console.error('登录返回的用户信息与请求不匹配')
        return {
          success: false,
          message: '登录异常，请重试'
        }
      }

      // 存储认证信息
      commit('SET_ACCESS_TOKEN', access_token)
      commit('SET_REFRESH_TOKEN', refresh_token)
      commit('SET_USER', user)

      // 启动会话超时监控
      dispatch('startSessionTimeout')

      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
      // 登录失败时也要清除可能的缓存
      commit('CLEAR_AUTH')
      return {
        success: false,
        message: error.response?.data?.detail || '登录失败，请检查用户名和密码'
      }
    } finally {
      commit('SET_LOGIN_LOADING', false)
    }
  },

  /**
   * 用户登出
   * @param {Object} context - Vuex上下文
   */
  async logout({ commit, dispatch, state }) {
    try {
      // 停止会话超时监控
      dispatch('stopSessionTimeout')

      // 如果有访问令牌，调用登出API
      if (state.accessToken) {
        await authAPI.logout()
      }
    } catch (error) {
      console.error('Logout API error:', error)
      // 即使API调用失败，也要清除本地认证信息
    } finally {
      commit('CLEAR_AUTH')
    }
  },

  /**
   * 刷新访问令牌
   * @param {Object} context - Vuex上下文
   * @returns {Promise<boolean>} 刷新成功返回true
   */
  async refreshAccessToken({ commit, state }) {
    try {
      if (!state.refreshToken) {
        return false
      }

      const response = await authAPI.refreshToken(state.refreshToken)
      const { access_token } = response

      commit('SET_ACCESS_TOKEN', access_token)
      return true
    } catch (error) {
      console.error('Token refresh error:', error)
      // 刷新失败，清除认证信息
      commit('CLEAR_AUTH')
      return false
    }
  },

  /**
   * 获取用户个人信息
   * @param {Object} context - Vuex上下文
   * @returns {Promise<Object|null>} 用户信息
   */
  async fetchProfile({ commit, state }) {
    try {
      if (!state.accessToken) {
        return null
      }

      const userProfile = await authAPI.getProfile()
      commit('SET_USER', userProfile)
      return userProfile
    } catch (error) {
      console.error('Fetch profile error:', error)
      return null
    }
  },

  /**
   * 更新用户个人信息
   * @param {Object} context - Vuex上下文
   * @param {Object} profileData - 个人信息数据
   * @returns {Promise<boolean>} 更新成功返回true
   */
  async updateProfile({ commit }, profileData) {
    try {
      const updatedProfile = await authAPI.updateProfile(profileData)
      commit('UPDATE_USER_PROFILE', updatedProfile)
      return true
    } catch (error) {
      console.error('Update profile error:', error)
      throw error
    }
  },

  /**
   * 修改密码
   * @param {Object} context - Vuex上下文
   * @param {Object} passwordData - 密码数据
   * @returns {Promise<boolean>} 修改成功返回true
   */
  async changePassword({ state }, passwordData) {
    try {
      await authAPI.changePassword(passwordData)
      return true
    } catch (error) {
      console.error('Change password error:', error)
      throw error
    }
  },

  /**
   * 验证当前令牌
   * @param {Object} context - Vuex上下文
   * @returns {Promise<boolean>} 验证成功返回true
   */
  async verifyToken({ commit, state }) {
    try {
      if (!state.accessToken) {
        return false
      }

      await authAPI.verifyToken()
      return true
    } catch (error) {
      console.error('Token verification error:', error)
      // 只有在401错误时才清除认证信息，其他错误可能是网络问题
      if (error.response?.status === 401) {
        commit('CLEAR_AUTH')
        return false
      }
      // 网络错误等情况，假设token仍然有效
      return true
    }
  },

  /**
   * 初始化认证状态
   * 应用启动时调用，验证存储的令牌是否有效
   * @param {Object} context - Vuex上下文
   */
  async initAuth({ dispatch, state, commit }) {
    console.log('初始化认证状态，当前用户:', state.user)

    if (state.accessToken && state.user) {
      try {
        // 简化验证逻辑：只验证token是否有效
        const isValid = await dispatch('verifyToken')
        if (!isValid) {
          console.log('Token验证失败，清除认证信息')
          commit('CLEAR_AUTH')
        } else {
          console.log('Token验证成功，保持当前认证状态')
          // 启动会话超时监控
          dispatch('startSessionTimeout')
        }
      } catch (error) {
        console.error('认证初始化过程中发生错误:', error)
        // 网络错误等情况，不清除认证信息，保持当前状态
        console.log('由于网络错误，保持当前认证状态')
        // 仍然启动会话超时监控
        dispatch('startSessionTimeout')
      }
    } else if (state.accessToken && !state.user) {
      // 有token但没有用户信息，尝试获取用户信息
      try {
        const userProfile = await dispatch('fetchProfile')
        if (userProfile) {
          console.log('获取到用户信息:', userProfile)
          commit('SET_USER', userProfile)
          // 启动会话超时监控
          dispatch('startSessionTimeout')
        } else {
          console.log('无法获取用户信息，清除认证信息')
          commit('CLEAR_AUTH')
        }
      } catch (error) {
        console.error('获取用户信息失败:', error)
        commit('CLEAR_AUTH')
      }
    }
    // 如果既没有token也没有用户信息，不需要做任何操作
  },

  /**
   * 启动会话超时监控
   * @param {Object} context - Vuex上下文
   */
  startSessionTimeout({ commit, dispatch, state }) {
    if (!state.isAuthenticated) {
      return
    }

    // 清除之前的定时器
    commit('CLEAR_TIMEOUT_TIMER')

    // 设置新的超时定时器
    const timer = setTimeout(() => {
      dispatch('handleSessionTimeout')
    }, state.sessionTimeout)

    commit('SET_TIMEOUT_TIMER', timer)
  },

  /**
   * 重置会话超时计时器
   * @param {Object} context - Vuex上下文
   */
  resetSessionTimeout({ commit, dispatch, state }) {
    if (!state.isAuthenticated) {
      return
    }

    // 更新最后活动时间
    commit('UPDATE_LAST_ACTIVITY')

    // 重新启动超时监控
    dispatch('startSessionTimeout')
  },

  /**
   * 处理会话超时
   * @param {Object} context - Vuex上下文
   */
  async handleSessionTimeout({ commit, dispatch }) {
    // 显示超时提示
    commit('SET_TIMEOUT_WARNING', true)

    // 延迟3秒后自动退出登录
    setTimeout(async () => {
      commit('SET_TIMEOUT_WARNING', false)
      await dispatch('logout')

      // 跳转到登录页面
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?timeout=1'
      }
    }, 3000)
  },

  /**
   * 停止会话超时监控
   * @param {Object} context - Vuex上下文
   */
  stopSessionTimeout({ commit }) {
    commit('CLEAR_TIMEOUT_TIMER')
  },

  /**
   * 记录用户活动
   * @param {Object} context - Vuex上下文
   */
  recordActivity({ dispatch, state }) {
    if (state.isAuthenticated) {
      dispatch('resetSessionTimeout')
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}