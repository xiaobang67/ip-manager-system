<template>
  <div 
    ref="containerRef" 
    class="virtual-scroll-container"
    :style="{ height: containerHeight + 'px' }"
    @scroll="handleScroll"
  >
    <!-- 虚拟滚动区域 -->
    <div 
      class="virtual-scroll-content"
      :style="{ 
        height: totalHeight + 'px',
        paddingTop: offsetY + 'px'
      }"
    >
      <!-- 渲染可见项目 -->
      <div
        v-for="(item, index) in visibleItems"
        :key="getItemKey(item, startIndex + index)"
        class="virtual-scroll-item"
        :style="{ height: itemHeight + 'px' }"
      >
        <slot 
          :item="item" 
          :index="startIndex + index"
          :isVisible="true"
        />
      </div>
    </div>
    
    <!-- 加载更多指示器 -->
    <div 
      v-if="loading" 
      class="virtual-scroll-loading"
    >
      <el-loading-spinner />
      <span>加载中...</span>
    </div>
    
    <!-- 无更多数据提示 -->
    <div 
      v-if="!hasMore && items.length > 0" 
      class="virtual-scroll-no-more"
    >
      没有更多数据了
    </div>
    
    <!-- 空数据提示 -->
    <div 
      v-if="!loading && items.length === 0" 
      class="virtual-scroll-empty"
    >
      <slot name="empty">
        <el-empty description="暂无数据" />
      </slot>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'

export default {
  name: 'VirtualScrollList',
  props: {
    // 数据项数组
    items: {
      type: Array,
      default: () => []
    },
    // 每项的高度
    itemHeight: {
      type: Number,
      default: 60
    },
    // 容器高度
    containerHeight: {
      type: Number,
      default: 400
    },
    // 缓冲区大小（在可见区域外渲染的项目数）
    bufferSize: {
      type: Number,
      default: 5
    },
    // 获取项目唯一键的函数
    keyField: {
      type: String,
      default: 'id'
    },
    // 是否启用无限滚动
    infiniteScroll: {
      type: Boolean,
      default: false
    },
    // 是否正在加载
    loading: {
      type: Boolean,
      default: false
    },
    // 是否还有更多数据
    hasMore: {
      type: Boolean,
      default: true
    },
    // 触发加载更多的距离阈值
    loadMoreThreshold: {
      type: Number,
      default: 100
    }
  },
  emits: ['load-more', 'scroll'],
  setup(props, { emit }) {
    const containerRef = ref(null)
    const scrollTop = ref(0)
    
    // 计算总高度
    const totalHeight = computed(() => {
      return props.items.length * props.itemHeight
    })
    
    // 计算可见区域的开始和结束索引
    const startIndex = computed(() => {
      const start = Math.floor(scrollTop.value / props.itemHeight) - props.bufferSize
      return Math.max(0, start)
    })
    
    const endIndex = computed(() => {
      const visibleCount = Math.ceil(props.containerHeight / props.itemHeight)
      const end = startIndex.value + visibleCount + props.bufferSize * 2
      return Math.min(props.items.length - 1, end)
    })
    
    // 计算可见项目
    const visibleItems = computed(() => {
      return props.items.slice(startIndex.value, endIndex.value + 1)
    })
    
    // 计算偏移量
    const offsetY = computed(() => {
      return startIndex.value * props.itemHeight
    })
    
    // 获取项目键
    const getItemKey = (item, index) => {
      if (typeof props.keyField === 'function') {
        return props.keyField(item, index)
      }
      return item[props.keyField] || index
    }
    
    // 处理滚动事件
    const handleScroll = (event) => {
      const target = event.target
      scrollTop.value = target.scrollTop
      
      // 发出滚动事件
      emit('scroll', {
        scrollTop: scrollTop.value,
        scrollHeight: target.scrollHeight,
        clientHeight: target.clientHeight
      })
      
      // 检查是否需要加载更多
      if (props.infiniteScroll && props.hasMore && !props.loading) {
        const distanceToBottom = target.scrollHeight - target.scrollTop - target.clientHeight
        if (distanceToBottom <= props.loadMoreThreshold) {
          emit('load-more')
        }
      }
    }
    
    // 滚动到指定索引
    const scrollToIndex = (index) => {
      if (containerRef.value) {
        const targetScrollTop = index * props.itemHeight
        containerRef.value.scrollTop = targetScrollTop
        scrollTop.value = targetScrollTop
      }
    }
    
    // 滚动到顶部
    const scrollToTop = () => {
      scrollToIndex(0)
    }
    
    // 滚动到底部
    const scrollToBottom = () => {
      if (props.items.length > 0) {
        scrollToIndex(props.items.length - 1)
      }
    }
    
    // 获取当前可见范围
    const getVisibleRange = () => {
      return {
        start: startIndex.value,
        end: endIndex.value,
        visibleCount: visibleItems.value.length
      }
    }
    
    // 监听数据变化，重置滚动位置
    watch(() => props.items.length, (newLength, oldLength) => {
      // 如果数据被重置（长度变为0或大幅减少），滚动到顶部
      if (newLength === 0 || (oldLength > 0 && newLength < oldLength / 2)) {
        nextTick(() => {
          scrollToTop()
        })
      }
    })
    
    // 暴露方法给父组件
    const expose = {
      scrollToIndex,
      scrollToTop,
      scrollToBottom,
      getVisibleRange
    }
    
    return {
      containerRef,
      scrollTop,
      totalHeight,
      startIndex,
      endIndex,
      visibleItems,
      offsetY,
      getItemKey,
      handleScroll,
      ...expose
    }
  }
}
</script>

<style scoped>
.virtual-scroll-container {
  overflow-y: auto;
  overflow-x: hidden;
  position: relative;
}

.virtual-scroll-content {
  position: relative;
}

.virtual-scroll-item {
  box-sizing: border-box;
}

.virtual-scroll-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  color: var(--el-text-color-secondary);
}

.virtual-scroll-loading span {
  margin-left: 8px;
}

.virtual-scroll-no-more {
  text-align: center;
  padding: 20px;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.virtual-scroll-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

/* 滚动条样式 */
.virtual-scroll-container::-webkit-scrollbar {
  width: 8px;
}

.virtual-scroll-container::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb {
  background: var(--el-border-color-darker);
  border-radius: 4px;
}

.virtual-scroll-container::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-dark);
}
</style>