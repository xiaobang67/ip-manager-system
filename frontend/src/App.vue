<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'App',
  computed: {
    ...mapGetters('theme', ['currentTheme']),
    ...mapGetters('auth', ['isAuthenticated', 'userTheme'])
  },
  watch: {
    // 监听用户主题偏好变化，同步用户偏好到本地存储
    userTheme: {
      handler(newTheme) {
        if (newTheme && newTheme !== this.currentTheme) {
          this.$store.dispatch('theme/setTheme', newTheme)
        }
      },
      immediate: false // 不立即执行，避免初始化时的冲突
    }
  },
  methods: {
    ...mapActions('theme', ['setTheme']),
    
    initializeTheme() {
      // 主题初始化优先级：
      // 1. localStorage中的主题设置（已在theme store中处理）
      // 2. 如果用户已登录且有不同的主题偏好，同步用户偏好
      if (this.isAuthenticated && this.userTheme && this.userTheme !== this.currentTheme) {
        this.$store.dispatch('theme/setTheme', this.userTheme)
      }
      // 如果没有localStorage存储的主题，theme store已经设置了默认的'light'主题
    }
  },
  mounted() {
    // 在mounted阶段初始化主题，确保DOM已准备好
    this.initializeTheme()
    
    // 确保主题样式立即应用到DOM
    this.$store.dispatch('theme/setTheme', this.currentTheme)
  }
}
</script>

<style>
/* 导入主题样式 */
@import './styles/themes.css';

#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: var(--bg-color-page);
  color: var(--text-color-primary);
  min-height: 100vh;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  background-color: var(--bg-color-page);
}

/* 确保主题切换时的平滑过渡 */
html {
  transition: background-color 0.3s ease;
}
</style>