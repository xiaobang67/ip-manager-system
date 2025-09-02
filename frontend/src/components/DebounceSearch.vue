<template>
  <div class="debounce-search">
    <el-input
      v-model="searchValue"
      :placeholder="placeholder"
      :size="size"
      :disabled="disabled"
      :clearable="clearable"
      :prefix-icon="prefixIcon"
      class="search-input"
      @clear="handleClear"
      @focus="handleFocus"
      @blur="handleBlur"
    >
      <template #suffix>
        <el-icon v-if="isSearching" class="is-loading">
          <Loading />
        </el-icon>
        <el-icon v-else-if="showSearchIcon" class="search-icon">
          <Search />
        </el-icon>
      </template>
    </el-input>
    
    <!-- 搜索建议下拉框 -->
    <div 
      v-if="showSuggestions && suggestions.length > 0"
      class="search-suggestions"
      :class="{ 'is-visible': suggestionsVisible }"
    >
      <div
        v-for="(suggestion, index) in suggestions"
        :key="index"
        class="suggestion-item"
        :class="{ 'is-active': index === activeSuggestionIndex }"
        @click="selectSuggestion(suggestion)"
        @mouseenter="activeSuggestionIndex = index"
      >
        <slot name="suggestion" :suggestion="suggestion" :index="index">
          <span class="suggestion-text">{{ suggestion.text || suggestion }}</span>
          <span v-if="suggestion.count" class="suggestion-count">{{ suggestion.count }}</span>
        </slot>
      </div>
    </div>
    
    <!-- 搜索历史 -->
    <div 
      v-if="showHistory && searchHistory.length > 0 && isFocused && !searchValue"
      class="search-history"
    >
      <div class="history-header">
        <span>搜索历史</span>
        <el-button 
          text 
          size="small" 
          @click="clearHistory"
        >
          清空
        </el-button>
      </div>
      <div
        v-for="(historyItem, index) in searchHistory"
        :key="index"
        class="history-item"
        @click="selectHistory(historyItem)"
      >
        <el-icon class="history-icon"><Clock /></el-icon>
        <span class="history-text">{{ historyItem }}</span>
        <el-icon 
          class="history-remove" 
          @click.stop="removeHistory(index)"
        >
          <Close />
        </el-icon>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { Search, Loading, Clock, Close } from '@element-plus/icons-vue'
import { debounce } from 'lodash-es'

export default {
  name: 'DebounceSearch',
  components: {
    Search,
    Loading,
    Clock,
    Close
  },
  props: {
    // v-model 绑定值
    modelValue: {
      type: String,
      default: ''
    },
    // 占位符文本
    placeholder: {
      type: String,
      default: '请输入搜索关键词'
    },
    // 输入框尺寸
    size: {
      type: String,
      default: 'default'
    },
    // 是否禁用
    disabled: {
      type: Boolean,
      default: false
    },
    // 是否可清空
    clearable: {
      type: Boolean,
      default: true
    },
    // 前缀图标
    prefixIcon: {
      type: [String, Object],
      default: null
    },
    // 防抖延迟时间（毫秒）
    debounceDelay: {
      type: Number,
      default: 300
    },
    // 最小搜索长度
    minLength: {
      type: Number,
      default: 1
    },
    // 是否显示搜索图标
    showSearchIcon: {
      type: Boolean,
      default: true
    },
    // 是否显示搜索建议
    showSuggestions: {
      type: Boolean,
      default: false
    },
    // 搜索建议列表
    suggestions: {
      type: Array,
      default: () => []
    },
    // 是否显示搜索历史
    showHistory: {
      type: Boolean,
      default: false
    },
    // 搜索历史存储键
    historyStorageKey: {
      type: String,
      default: 'search_history'
    },
    // 最大历史记录数
    maxHistoryCount: {
      type: Number,
      default: 10
    },
    // 是否正在搜索
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'search', 'clear', 'focus', 'blur', 'suggestion-select'],
  setup(props, { emit }) {
    const searchValue = ref(props.modelValue)
    const isSearching = ref(false)
    const isFocused = ref(false)
    const suggestionsVisible = ref(false)
    const activeSuggestionIndex = ref(-1)
    const searchHistory = ref([])
    
    // 创建防抖搜索函数
    const debouncedSearch = debounce((value) => {
      if (value.length >= props.minLength) {
        isSearching.value = true
        emit('search', value)
      } else if (value.length === 0) {
        emit('search', '')
      }
    }, props.debounceDelay)
    
    // 监听搜索值变化
    watch(searchValue, (newValue) => {
      emit('update:modelValue', newValue)
      
      if (newValue !== props.modelValue) {
        debouncedSearch(newValue)
        
        // 显示搜索建议
        if (props.showSuggestions && newValue.length > 0) {
          suggestionsVisible.value = true
          activeSuggestionIndex.value = -1
        } else {
          suggestionsVisible.value = false
        }
      }
    })
    
    // 监听外部值变化
    watch(() => props.modelValue, (newValue) => {
      if (newValue !== searchValue.value) {
        searchValue.value = newValue
      }
    })
    
    // 监听加载状态
    watch(() => props.loading, (newValue) => {
      isSearching.value = newValue
    })
    
    // 处理清空
    const handleClear = () => {
      searchValue.value = ''
      suggestionsVisible.value = false
      emit('clear')
    }
    
    // 处理焦点
    const handleFocus = () => {
      isFocused.value = true
      emit('focus')
    }
    
    // 处理失焦
    const handleBlur = () => {
      // 延迟隐藏，允许点击建议
      setTimeout(() => {
        isFocused.value = false
        suggestionsVisible.value = false
      }, 200)
      emit('blur')
    }
    
    // 选择搜索建议
    const selectSuggestion = (suggestion) => {
      const text = suggestion.text || suggestion
      searchValue.value = text
      suggestionsVisible.value = false
      addToHistory(text)
      emit('suggestion-select', suggestion)
    }
    
    // 键盘导航
    const handleKeydown = (event) => {
      if (!suggestionsVisible.value || props.suggestions.length === 0) {
        return
      }
      
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault()
          activeSuggestionIndex.value = Math.min(
            activeSuggestionIndex.value + 1,
            props.suggestions.length - 1
          )
          break
        case 'ArrowUp':
          event.preventDefault()
          activeSuggestionIndex.value = Math.max(
            activeSuggestionIndex.value - 1,
            -1
          )
          break
        case 'Enter':
          event.preventDefault()
          if (activeSuggestionIndex.value >= 0) {
            selectSuggestion(props.suggestions[activeSuggestionIndex.value])
          } else if (searchValue.value) {
            addToHistory(searchValue.value)
            suggestionsVisible.value = false
          }
          break
        case 'Escape':
          suggestionsVisible.value = false
          activeSuggestionIndex.value = -1
          break
      }
    }
    
    // 加载搜索历史
    const loadHistory = () => {
      try {
        const stored = localStorage.getItem(props.historyStorageKey)
        if (stored) {
          searchHistory.value = JSON.parse(stored)
        }
      } catch (error) {
        console.error('Failed to load search history:', error)
      }
    }
    
    // 保存搜索历史
    const saveHistory = () => {
      try {
        localStorage.setItem(
          props.historyStorageKey,
          JSON.stringify(searchHistory.value)
        )
      } catch (error) {
        console.error('Failed to save search history:', error)
      }
    }
    
    // 添加到搜索历史
    const addToHistory = (term) => {
      if (!props.showHistory || !term.trim()) {
        return
      }
      
      // 移除重复项
      const index = searchHistory.value.indexOf(term)
      if (index > -1) {
        searchHistory.value.splice(index, 1)
      }
      
      // 添加到开头
      searchHistory.value.unshift(term)
      
      // 限制历史记录数量
      if (searchHistory.value.length > props.maxHistoryCount) {
        searchHistory.value = searchHistory.value.slice(0, props.maxHistoryCount)
      }
      
      saveHistory()
    }
    
    // 选择历史记录
    const selectHistory = (historyItem) => {
      searchValue.value = historyItem
      isFocused.value = false
    }
    
    // 移除历史记录
    const removeHistory = (index) => {
      searchHistory.value.splice(index, 1)
      saveHistory()
    }
    
    // 清空历史记录
    const clearHistory = () => {
      searchHistory.value = []
      saveHistory()
    }
    
    onMounted(() => {
      if (props.showHistory) {
        loadHistory()
      }
      
      // 添加键盘事件监听
      document.addEventListener('keydown', handleKeydown)
    })
    
    onUnmounted(() => {
      document.removeEventListener('keydown', handleKeydown)
    })
    
    return {
      searchValue,
      isSearching,
      isFocused,
      suggestionsVisible,
      activeSuggestionIndex,
      searchHistory,
      handleClear,
      handleFocus,
      handleBlur,
      selectSuggestion,
      selectHistory,
      removeHistory,
      clearHistory
    }
  }
}
</script>

<style scoped>
.debounce-search {
  position: relative;
  width: 100%;
}

.search-input {
  width: 100%;
}

.search-icon {
  color: var(--el-text-color-placeholder);
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

/* 搜索建议样式 */
.search-suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  box-shadow: var(--el-box-shadow-light);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
  opacity: 0;
  transform: translateY(-10px);
  transition: all 0.2s ease;
}

.search-suggestions.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.suggestion-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.suggestion-item:hover,
.suggestion-item.is-active {
  background-color: var(--el-fill-color-light);
}

.suggestion-text {
  flex: 1;
  color: var(--el-text-color-primary);
}

.suggestion-count {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

/* 搜索历史样式 */
.search-history {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: var(--el-bg-color-overlay);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  box-shadow: var(--el-box-shadow-light);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.history-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.history-item:hover {
  background-color: var(--el-fill-color-light);
}

.history-icon {
  margin-right: 8px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
}

.history-text {
  flex: 1;
  color: var(--el-text-color-primary);
}

.history-remove {
  margin-left: 8px;
  color: var(--el-text-color-placeholder);
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.history-item:hover .history-remove {
  opacity: 1;
}

.history-remove:hover {
  color: var(--el-color-danger);
}
</style>