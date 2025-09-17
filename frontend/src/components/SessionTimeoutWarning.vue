<template>
  <el-dialog
    v-model="showWarning"
    title="会话即将超时"
    width="400px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    :show-close="false"
    center
  >
    <div class="timeout-warning">
      <el-icon class="warning-icon" size="48" color="#E6A23C">
        <Warning />
      </el-icon>
      <p class="warning-text">
        您已经连续 10 分钟没有操作，会话即将超时。
      </p>
      <p class="warning-subtext">
        系统将在 3 秒后自动退出登录...
      </p>
      <div class="countdown">
        <el-progress
          :percentage="progressPercentage"
          :show-text="false"
          status="warning"
          :stroke-width="8"
        />
        <div class="countdown-text">{{ countdown }} 秒</div>
      </div>
    </div>
  </el-dialog>
</template>

<script>
import { computed, ref, watch, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { Warning } from '@element-plus/icons-vue'

export default {
  name: 'SessionTimeoutWarning',
  components: {
    Warning
  },
  setup() {
    const store = useStore()
    const countdown = ref(3)
    const progressPercentage = ref(100)
    let countdownTimer = null

    const showWarning = computed(() => store.getters['auth/showTimeoutWarning'])

    // 监听警告显示状态
    watch(showWarning, (newValue) => {
      if (newValue) {
        startCountdown()
      } else {
        stopCountdown()
      }
    })

    const startCountdown = () => {
      countdown.value = 3
      progressPercentage.value = 100

      countdownTimer = setInterval(() => {
        countdown.value--
        progressPercentage.value = (countdown.value / 3) * 100

        if (countdown.value <= 0) {
          stopCountdown()
        }
      }, 1000)
    }

    const stopCountdown = () => {
      if (countdownTimer) {
        clearInterval(countdownTimer)
        countdownTimer = null
      }
      countdown.value = 3
      progressPercentage.value = 100
    }

    onUnmounted(() => {
      stopCountdown()
    })

    return {
      showWarning,
      countdown,
      progressPercentage
    }
  }
}
</script>

<style scoped>
.timeout-warning {
  text-align: center;
  padding: 20px;
}

.warning-icon {
  margin-bottom: 16px;
}

.warning-text {
  font-size: 16px;
  color: #606266;
  margin-bottom: 8px;
  line-height: 1.5;
}

.warning-subtext {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

.countdown {
  position: relative;
  margin: 20px auto;
  width: 200px;
}

.countdown-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 18px;
  font-weight: bold;
  color: #E6A23C;
}

:deep(.el-progress-bar__outer) {
  border-radius: 10px;
}

:deep(.el-progress-bar__inner) {
  border-radius: 10px;
}
</style>