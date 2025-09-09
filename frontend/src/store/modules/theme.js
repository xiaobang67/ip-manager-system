// 从localStorage获取存储的主题，如果没有则使用默认值
const getStoredTheme = () => {
  try {
    return localStorage.getItem('user_theme') || 'light'
  } catch (error) {
    console.error('Error reading theme from localStorage:', error)
    return 'light'
  }
}

const state = {
  currentTheme: getStoredTheme()
}

const getters = {
  currentTheme: state => state.currentTheme,
  isDarkMode: state => state.currentTheme === 'dark'
}

const mutations = {
  SET_THEME(state, theme) {
    state.currentTheme = theme
    
    // 保存到localStorage
    try {
      localStorage.setItem('user_theme', theme)
    } catch (error) {
      console.error('Error saving theme to localStorage:', error)
    }
    
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme)
    
    // Update Element Plus theme
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
}

const actions = {
  async toggleTheme({ commit, state, rootGetters, dispatch }) {
    const newTheme = state.currentTheme === 'light' ? 'dark' : 'light'
    commit('SET_THEME', newTheme)
    
    // 如果用户已登录，同步到后端
    if (rootGetters['auth/isAuthenticated']) {
      try {
        await dispatch('auth/updateProfile', { theme: newTheme }, { root: true })
      } catch (error) {
        console.error('Failed to sync theme to server:', error)
        // 即使同步失败，主题切换仍然有效，因为已经保存到localStorage
      }
    }
  },
  
  setTheme({ commit }, theme) {
    if (theme && ['light', 'dark'].includes(theme)) {
      commit('SET_THEME', theme)
    }
  },
  
  // 从用户信息初始化主题
  initThemeFromUser({ commit, state }, userTheme) {
    if (userTheme && ['light', 'dark'].includes(userTheme) && userTheme !== state.currentTheme) {
      commit('SET_THEME', userTheme)
    }
  },
  
  // 初始化主题，确保DOM样式正确应用
  initTheme({ commit, state }) {
    // 重新应用当前主题到DOM，确保页面刷新后样式正确
    commit('SET_THEME', state.currentTheme)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}