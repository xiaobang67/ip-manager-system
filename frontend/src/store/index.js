import { createStore } from 'vuex'
import auth from './modules/auth'

export default createStore({
  modules: {
    auth
  },
  strict: process.env.NODE_ENV !== 'production'
})