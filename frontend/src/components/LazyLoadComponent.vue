<template>
  <div 
    ref="containerRef"
    class="lazy-load-container"
    :class="{ 'is-loading': isLoading, 'is-loaded': isLoaded }"
  >
    <!-- 占位符内容 -->
    <div 
      v-if="!isLoaded && showPlaceholder" 
      class="lazy-load-placeholder"
      :style="placeholderStyle"
    >
      <slot name="placeholder">
        <div class="default-placeholder">
          <el-skeleton :rows="skeletonRows" animated />
        </div>
      </slot>
    </div>
    
    <!-- 加载中状态 -->
    <div 
      v-if="isLoading" 
      class="lazy-load-loading"
    >
      <slot name="loading">
        <div class="default-loading">
          <el-loading-spinner />
          <span>加载中...</span>
        </div>
      </slot>
    </div>
    
    <!-- 实际内容 -->
    <div 
      v-if="isLoaded && !hasError"
      class="lazy-load-content"
      :class="{ 'fade-in': useTransition }"
    >
      <slot />
    </div>
    
    <!-- 错误状态 -->
    <div 
      v-if="hasError" 
      class="lazy-load-error"
    >
      <slot name="error" :error="error" :retry="retry">
        <div class="default-error">
          <el-icon class="error-icon"><Warning /></el-icon>
          <p>加载失败</p>
          <el-button size="small" @click="retry">重试</el-button>
        </div>
      </slot>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Warning } from '@element-plus/icons-vue'

export default {
  name: 'LazyLoadComponent',
  components: {
    Warning
  },
  props: {
    // 是否立即加载（不等待进入视口）
    immediate: {
      type: Boolean,
      default: false
    },
    // 视口边距（提前多少像素开始加载）
    rootMargin: {
      type: String,
      default: '50px'
    },
    // 交叉比例阈值
    threshold: {
      type: Number,
      default: 0.1
    },
    // 是否只触发一次
    once: {
      type: Boolean,
      default: true
    },
    // 是否显示占位符
    showPlaceholder: {
      type: Boolean,
      default: true
    },
    // 占位符高度
    placeholderHeight: {
      type: [String, Number],
      default: '200px'
    },
    // 骨架屏行数
    skeletonRows: {
      type: Number,
      default: 3
    },
    // 是否使用过渡动画
    useTransition: {
      type: Boolean,
      default: true
    },
    // 加载函数
    loadFunction: {
      type: Function,
      default: null
    },
    // 最大重试次数
    maxRetries: {
      type: Number,
      default: 3
    },
    // 重试延迟（毫秒）
    retryDelay: {
      type: Number,
      default: 1000
    }
  },
  emits: ['load', 'loaded', 'error', 'visible'],
  setup(props, { emit }) {
    const containerRef = ref(null)
    const isLoading = ref(false)
    const isLoaded = ref(false)
    const hasError = ref(false)
    const error = ref(null)
    const retryCount = ref(0)
    const observer = ref(null)
    
    // 占位符样式
    const placeholderStyle = ref({
      height: typeof props.placeholderHeight === 'number' 
        ? `${props.placeholderHeight}px` 
        : props.placeholderHeight
    })
    
    // 创建 Intersection Observer
    const createObserver = () => {
      if (!window.IntersectionObserver) {
        // 不支持 IntersectionObserver，直接加载
        handleLoad()
        return
      }
      
      observer.value = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              emit('visible')
              handleLoad()
              
              if (props.once && observer.value) {
                observer.value.disconnect()
              }
            }
          })
        },
        {
          rootMargin: props.rootMargin,
          threshold: props.threshold
        }
      )
      
      if (containerRef.value) {
        observer.value.observe(containerRef.value)
      }
    }
    
    // 处理加载
    const handleLoad = async () => {
      if (isLoading.value || isLoaded.value) {
        return
      }
      
      isLoading.value = true
      hasError.value = false
      error.value = null
      
      emit('load')
      
      try {
        if (props.loadFunction) {
          await props.loadFunction()
        }
        
        // 模拟最小加载时间，避免闪烁
        await new Promise(resolve => setTimeout(resolve, 100))
        
        isLoaded.value = true
        emit('loaded')
        
      } catch (err) {
        console.error('Lazy load error:', err)
        error.value = err
        hasError.value = true
        emit('error', err)
        
      } finally {
        isLoading.value = false
      }
    }
    
    // 重试加载
    const retry = async () => {
      if (retryCount.value >= props.maxRetries) {
        return
      }
      
      retryCount.value++
      
      // 延迟重试
      if (props.retryDelay > 0) {
        await new Promise(resolve => setTimeout(resolve, props.retryDelay))
      }
      
      await handleLoad()
    }
    
    // 重置状态
    const reset = () => {
      isLoading.value = false
      isLoaded.value = false
      hasError.value = false
      error.value = null
      retryCount.value = 0
    }
    
    // 手动触发加载
    const load = () => {
      handleLoad()
    }
    
    onMounted(() => {
      nextTick(() => {
        if (props.immediate) {
          handleLoad()
        } else {
          createObserver()
        }
      })
    })
    
    onUnmounted(() => {
      if (observer.value) {
        observer.value.disconnect()
      }
    })
    
    // 监听 loadFunction 变化
    watch(() => props.loadFunction, () => {
      if (isLoaded.value) {
        reset()
        if (props.immediate) {
          handleLoad()
        }
      }
    })
    
    return {
      containerRef,
      isLoading,
      isLoaded,
      hasError,
      error,
      placeholderStyle,
      retry,
      reset,
      load
    }
  }
}
</script>

<style scoped>
.lazy-load-container {
  position: relative;
  width: 100%;
}

.lazy-load-placeholder {
  width: 100%;
}

.default-placeholder {
  padding: 20px;
}

.lazy-load-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: var(--el-text-color-secondary);
}

.default-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.lazy-load-content {
  width: 100%;
}

.lazy-load-content.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

.lazy-load-error {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.default-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--el-text-color-secondary);
}

.error-icon {
  font-size: 32px;
  color: var(--el-color-warning);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 加载状态样式 */
.is-loading {
  pointer-events: none;
}

.is-loaded {
  /* 已加载状态的样式 */
}
</style>