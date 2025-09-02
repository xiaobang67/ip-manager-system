<template>
  <el-tooltip
    :content="isDarkMode ? '切换到明亮主题' : '切换到暗黑主题'"
    placement="bottom"
  >
    <el-button
      :icon="isDarkMode ? 'Sunny' : 'Moon'"
      circle
      class="theme-toggle-button"
      @click="toggleTheme"
    />
  </el-tooltip>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'ThemeToggle',
  computed: {
    ...mapGetters('theme', ['isDarkMode'])
  },
  methods: {
    ...mapActions('theme', ['toggleTheme']),
    
    async toggleTheme() {
      // 切换主题
      await this.$store.dispatch('theme/toggleTheme')
      
      // 如果用户已登录，同步更新用户偏好设置
      if (this.$store.getters['auth/isAuthenticated']) {
        try {
          const newTheme = this.$store.getters['theme/currentTheme']
          await this.$store.dispatch('auth/updateProfile', { theme: newTheme })
        } catch (error) {
          console.error('Failed to sync theme preference:', error)
          // 即使同步失败，主题切换仍然有效，只是不会保存到服务器
        }
      }
    }
  }
}
</script>

<style scoped>
.theme-toggle-button {
  transition: all 0.3s ease;
}

.theme-toggle-button:hover {
  transform: scale(1.1);
}
</style>