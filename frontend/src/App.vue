<template>
  <div id="app">
    <router-view />
    
    <!-- 会话超时警告组件 -->
    <SessionTimeoutWarning />
    
    <!-- 用户活动监听器 -->
    <ActivityMonitor />
  </div>
</template>

<script>
import { onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import SessionTimeoutWarning from '@/components/SessionTimeoutWarning.vue'
import ActivityMonitor from '@/components/ActivityMonitor.vue'

export default {
  name: 'App',
  components: {
    SessionTimeoutWarning,
    ActivityMonitor
  },
  
  setup() {
    const store = useStore()

    const handleStorageChange = (event) => {
      // 监听localStorage变化，防止多标签页身份冲突
      if (event.key === 'access_token' && event.newValue === null) {
        // 如果access_token被清除，说明用户在其他标签页登出
        console.log('检测到其他标签页登出，清除当前认证状态')
        store.commit('auth/CLEAR_AUTH')
        // 使用Vue Router的编程式导航
        window.location.href = '/login'
      }
    }

    onMounted(() => {
      // 监听存储变化，防止多标签页之间的身份冲突
      window.addEventListener('storage', handleStorageChange)
      
      // 初始化认证状态（包括启动会话超时监控）
      store.dispatch('auth/initAuth')
    })

    onUnmounted(() => {
      window.removeEventListener('storage', handleStorageChange)
    })

    return {}
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