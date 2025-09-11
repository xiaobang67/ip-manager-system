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
    return {
      accessToken: null,
      refreshToken: null,
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
  loginLoading: false
}

const getters = {
  isAuthenticated: state => state.isAuthenticated,
  accessToken: state => state.accessToken,
  refreshToken: state => state.refreshToken,
  currentUser: state => state.user,
  userRole: state => state.user?.role || null,
  userName: state => state.user?.username || '',
  userEmail: state => state.user?.email || '',

  loginLoading: state => state.loginLoading
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
  }
}

const actions = {
  /**
   * 用户登录
   * @param {Object} context - Vuex上下文
   * @param {Object} credentials - 登录凭据
   * @returns {Promise<Object>} 登录结果
   */
  async login({ commit }, credentials) {
    commit('SET_LOGIN_LOADING', true)
    
    try {
      const response = await authAPI.login(credentials)
      const { access_token, refresh_token, user } = response
      
      // 存储认证信息
      commit('SET_ACCESS_TOKEN', access_token)
      commit('SET_REFRESH_TOKEN', refresh_token)
      commit('SET_USER', user)
      
      return { success: true }
    } catch (error) {
      console.error('Login error:', error)
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
  async logout({ commit, state }) {
    try {
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
  async initAuth({ dispatch, state }) {
    if (state.accessToken) {
      const isValid = await dispatch('verifyToken')
      if (isValid) {
        // 令牌有效，获取最新的用户信息
        await dispatch('fetchProfile')
      }
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