const state = {
  currentTheme: 'light' // 默认主题，将从用户信息中获取
}

const getters = {
  currentTheme: state => state.currentTheme,
  isDarkMode: state => state.currentTheme === 'dark'
}

const mutations = {
  SET_THEME(state, theme) {
    state.currentTheme = theme
    
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
        // 即使同步失败，主题切换仍然有效
      }
    }
  },
  
  setTheme({ commit }, theme) {
    commit('SET_THEME', theme)
  },
  
  // 从用户信息初始化主题
  initThemeFromUser({ commit }, userTheme) {
    if (userTheme && ['light', 'dark'].includes(userTheme)) {
      commit('SET_THEME', userTheme)
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