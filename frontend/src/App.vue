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
    // 监听用户主题偏好变化
    userTheme: {
      handler(newTheme) {
        if (newTheme && newTheme !== this.currentTheme) {
          this.setTheme(newTheme)
        }
      },
      immediate: true
    }
  },
  methods: {
    ...mapActions('theme', ['setTheme']),
    
    initializeTheme() {
      // 如果用户已登录且有主题偏好，使用用户偏好
      if (this.isAuthenticated && this.userTheme) {
        this.setTheme(this.userTheme)
      } else {
        // 否则使用本地存储的主题或默认主题
        const savedTheme = localStorage.getItem('theme') || 'light'
        this.setTheme(savedTheme)
      }
    }
  },
  created() {
    this.initializeTheme()
  },
  mounted() {
    // 应用初始主题
    this.setTheme(this.currentTheme)
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