import { createStore } from 'vuex'
import auth from './modules/auth'
import theme from './modules/theme'

export default createStore({
  modules: {
    auth,
    theme
  },
  strict: process.env.NODE_ENV !== 'production'
})