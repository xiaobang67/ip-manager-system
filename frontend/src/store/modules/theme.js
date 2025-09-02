const state = {
  currentTheme: localStorage.getItem('theme') || 'light'
}

const getters = {
  currentTheme: state => state.currentTheme,
  isDarkMode: state => state.currentTheme === 'dark'
}

const mutations = {
  SET_THEME(state, theme) {
    state.currentTheme = theme
    localStorage.setItem('theme', theme)
    
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
  toggleTheme({ commit, state }) {
    const newTheme = state.currentTheme === 'light' ? 'dark' : 'light'
    commit('SET_THEME', newTheme)
  },
  
  setTheme({ commit }, theme) {
    commit('SET_THEME', theme)
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}