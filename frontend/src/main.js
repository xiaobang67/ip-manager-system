import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

// 导入统一主题系统
import './styles/theme-system.css'
// 导入统一全局主题覆盖系统
import './styles/unified-theme-override.css'
import themeDirective from './directives/theme'
// 导入主题强制执行器
import { initThemeEnforcer } from './utils/themeEnforcer'
// 导入对话框主题修复器
import { initDialogThemeFixer } from './utils/dialogThemeFixer'

const app = createApp(App)

// Register Element Plus icons
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 注册主题指令
app.directive('theme', themeDirective)

app.use(store)
app.use(router)
app.use(ElementPlus)

// 初始化认证状态和主题
Promise.all([
  store.dispatch('auth/initAuth'),
  store.dispatch('theme/initTheme')
]).finally(() => {
  app.mount('#app')
  
  // 暂时禁用激进的主题强制执行器，避免所有元素都有黑色背景
  // setTimeout(() => {
  //   initThemeEnforcer()
  //   initDialogThemeFixer()
  //   console.log('🎨 主题强制执行器已启动')
  //   console.log('🔧 对话框主题修复器已启动')
  // }, 1000)
})