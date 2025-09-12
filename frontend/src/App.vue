<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App',
  
  mounted() {
    // 监听存储变化，防止多标签页之间的身份冲突
    window.addEventListener('storage', this.handleStorageChange)
  },
  
  beforeUnmount() {
    window.removeEventListener('storage', this.handleStorageChange)
  },
  
  methods: {
    handleStorageChange(event) {
      // 监听localStorage变化，防止多标签页身份冲突
      if (event.key === 'access_token' && event.newValue === null) {
        // 如果access_token被清除，说明用户在其他标签页登出
        console.log('检测到其他标签页登出，清除当前认证状态')
        this.$store.commit('auth/CLEAR_AUTH')
        this.$router.push('/login')
      }
    }
  }
}
</script>

<style>
#app {
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f5f7fa;
  color: #303133;
  min-height: 100vh;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  background-color: #f5f7fa;
}
</style>