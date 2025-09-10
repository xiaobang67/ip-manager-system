/**
 * 主题指令
 * 自动为元素应用主题样式
 */

import { themeUtils } from '@/composables/useTheme'

// 主题指令实现
const themeDirective = {
  mounted(el, binding) {
    applyTheme(el, binding)
    
    // 监听主题变化
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
          applyTheme(el, binding)
        }
      })
    })
    
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    })
    
    // 保存observer到元素上，用于清理
    el._themeObserver = observer
  },
  
  updated(el, binding) {
    applyTheme(el, binding)
  },
  
  unmounted(el) {
    // 清理observer
    if (el._themeObserver) {
      el._themeObserver.disconnect()
      delete el._themeObserver
    }
  }
}

// 应用主题到元素
function applyTheme(el, binding) {
  const { value, modifiers, arg } = binding
  
  // 如果传入的是字符串，作为预设主题类型
  if (typeof value === 'string') {
    applyPresetTheme(el, value, modifiers)
  }
  // 如果传入的是对象，作为自定义样式
  else if (typeof value === 'object') {
    applyCustomTheme(el, value, modifiers)
  }
  // 如果没有值，应用默认主题
  else {
    applyDefaultTheme(el, arg, modifiers)
  }
}

// 应用预设主题
function applyPresetTheme(el, themeType, modifiers) {
  const presets = {
    card: {
      backgroundColor: 'var(--bg-primary)',
      borderColor: 'var(--border-primary)',
      color: 'var(--text-primary)',
      borderRadius: 'var(--radius-xl)',
      boxShadow: 'var(--shadow-light)'
    },
    
    input: {
      backgroundColor: 'var(--bg-primary)',
      borderColor: 'var(--border-primary)',
      color: 'var(--text-primary)'
    },
    
    button: {
      backgroundColor: 'var(--bg-primary)',
      borderColor: 'var(--border-primary)',
      color: 'var(--text-secondary)'
    },
    
    text: {
      color: 'var(--text-primary)'
    },
    
    background: {
      backgroundColor: 'var(--bg-primary)'
    },
    
    border: {
      borderColor: 'var(--border-primary)'
    }
  }
  
  const styles = presets[themeType] || presets.text
  applyStylesToElement(el, styles, modifiers)
}

// 应用自定义主题
function applyCustomTheme(el, customStyles, modifiers) {
  const processedStyles = {}
  
  Object.entries(customStyles).forEach(([key, value]) => {
    // 如果值是CSS变量名，转换为var()格式
    if (typeof value === 'string' && !value.startsWith('var(') && !value.startsWith('#') && !value.startsWith('rgb')) {
      processedStyles[key] = `var(--${value})`
    } else {
      processedStyles[key] = value
    }
  })
  
  applyStylesToElement(el, processedStyles, modifiers)
}

// 应用默认主题
function applyDefaultTheme(el, arg, modifiers) {
  // 根据元素类型应用默认主题
  const tagName = el.tagName.toLowerCase()
  const className = el.className
  
  let defaultTheme = 'text'
  
  if (className.includes('el-card') || className.includes('card')) {
    defaultTheme = 'card'
  } else if (className.includes('el-input') || className.includes('input')) {
    defaultTheme = 'input'
  } else if (className.includes('el-button') || className.includes('button')) {
    defaultTheme = 'button'
  } else if (tagName === 'div' || tagName === 'section') {
    defaultTheme = 'background'
  }
  
  applyPresetTheme(el, arg || defaultTheme, modifiers)
}

// 将样式应用到元素
function applyStylesToElement(el, styles, modifiers) {
  Object.entries(styles).forEach(([property, value]) => {
    // 转换驼峰命名为短横线命名
    const cssProperty = property.replace(/([A-Z])/g, '-$1').toLowerCase()
    el.style.setProperty(cssProperty, value)
  })
  
  // 处理修饰符
  if (modifiers.important) {
    Object.entries(styles).forEach(([property, value]) => {
      const cssProperty = property.replace(/([A-Z])/g, '-$1').toLowerCase()
      el.style.setProperty(cssProperty, value, 'important')
    })
  }
  
  if (modifiers.hover) {
    // 添加hover效果
    el.addEventListener('mouseenter', () => {
      el.style.transform = 'translateY(-2px)'
      el.style.boxShadow = 'var(--shadow-base)'
    })
    
    el.addEventListener('mouseleave', () => {
      el.style.transform = ''
      el.style.boxShadow = styles.boxShadow || 'var(--shadow-light)'
    })
  }
}

// 导出指令
export default themeDirective

// 预设主题样式
export const themePresets = {
  // 页面容器
  pageContainer: {
    backgroundColor: 'bg-secondary',
    color: 'text-primary',
    minHeight: '100vh'
  },
  
  // 内容卡片
  contentCard: {
    backgroundColor: 'bg-primary',
    borderColor: 'border-primary',
    color: 'text-primary',
    borderRadius: 'radius-xl',
    boxShadow: 'shadow-light'
  },
  
  // 搜索区域
  searchSection: {
    backgroundColor: 'bg-primary',
    borderColor: 'border-primary',
    color: 'text-primary',
    borderRadius: 'radius-large'
  },
  
  // 统计卡片
  statsCard: {
    backgroundColor: 'bg-primary',
    borderColor: 'border-primary',
    borderRadius: 'radius-large'
  },
  
  // 表格区域
  tableSection: {
    backgroundColor: 'bg-primary',
    borderColor: 'border-primary',
    borderRadius: 'radius-large',
    color: 'text-primary'
  }
}