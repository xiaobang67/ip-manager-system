<template>
  <!-- 这个组件没有可见内容，只负责监听用户活动 -->
</template>

<script>
import { onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'

export default {
  name: 'ActivityMonitor',
  setup() {
    const store = useStore()

    // 需要监听的事件类型
    const activityEvents = [
      'mousedown',
      'mousemove',
      'keypress',
      'scroll',
      'touchstart',
      'click',
      'keydown'
    ]

    // 防抖函数，避免频繁触发
    let debounceTimer = null
    const debounceDelay = 1000 // 1秒内只记录一次活动

    const handleActivity = () => {
      // 清除之前的定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }

      // 设置新的定时器
      debounceTimer = setTimeout(() => {
        // 只有在用户已登录时才记录活动
        if (store.getters['auth/isAuthenticated']) {
          store.dispatch('auth/recordActivity')
        }
      }, debounceDelay)
    }

    // 添加事件监听器
    const addEventListeners = () => {
      activityEvents.forEach(event => {
        document.addEventListener(event, handleActivity, true)
      })
    }

    // 移除事件监听器
    const removeEventListeners = () => {
      activityEvents.forEach(event => {
        document.removeEventListener(event, handleActivity, true)
      })
    }

    onMounted(() => {
      addEventListeners()
    })

    onUnmounted(() => {
      removeEventListeners()
      
      // 清除防抖定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }
    })

    return {}
  }
}
</script>