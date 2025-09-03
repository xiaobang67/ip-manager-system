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
    ...mapActions('theme', ['toggleTheme'])
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