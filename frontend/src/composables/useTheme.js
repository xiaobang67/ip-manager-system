/**
 * 主题管理 Composable
 * 提供统一的主题管理功能
 */

import { computed, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'

export function useTheme() {
  const store = useStore()

  // 当前主题
  const currentTheme = computed(() => store.getters['theme/currentTheme'])
  const isDarkMode = computed(() => store.getters['theme/isDarkMode'])

  // 主题切换
  const toggleTheme = () => {
    store.dispatch('theme/toggleTheme')
  }

  const setTheme = (theme) => {
    store.dispatch('theme/setTheme', theme)
  }

  // 主题变量获取
  const getThemeVar = (varName) => {
    return getComputedStyle(document.documentElement).getPropertyValue(`--${varName}`)
  }

  // 设置主题变量
  const setThemeVar = (varName, value) => {
    document.documentElement.style.setProperty(`--${varName}`, value)
  }

  // 主题类名
  const themeClass = computed(() => ({
    'theme-light': currentTheme.value === 'light',
    'theme-dark': currentTheme.value === 'dark'
  }))

  // 主题样式对象
  const themeStyles = computed(() => {
    const vars = {}
    
    // 获取所有CSS变量
    const computedStyle = getComputedStyle(document.documentElement)
    
    // 基础颜色
    vars.primary = computedStyle.getPropertyValue('--primary').trim()
    vars.success = computedStyle.getPropertyValue('--success').trim()
    vars.warning = computedStyle.getPropertyValue('--warning').trim()
    vars.danger = computedStyle.getPropertyValue('--danger').trim()
    vars.info = computedStyle.getPropertyValue('--info').trim()
    
    // 背景颜色
    vars.bgPrimary = computedStyle.getPropertyValue('--bg-primary').trim()
    vars.bgSecondary = computedStyle.getPropertyValue('--bg-secondary').trim()
    vars.bgTertiary = computedStyle.getPropertyValue('--bg-tertiary').trim()
    
    // 文本颜色
    vars.textPrimary = computedStyle.getPropertyValue('--text-primary').trim()
    vars.textSecondary = computedStyle.getPropertyValue('--text-secondary').trim()
    vars.textTertiary = computedStyle.getPropertyValue('--text-tertiary').trim()
    
    // 边框颜色
    vars.borderPrimary = computedStyle.getPropertyValue('--border-primary').trim()
    vars.borderSecondary = computedStyle.getPropertyValue('--border-secondary').trim()
    vars.borderTertiary = computedStyle.getPropertyValue('--border-tertiary').trim()
    
    return vars
  })

  // 监听系统主题变化
  const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  
  const handleSystemThemeChange = (e) => {
    // 如果用户没有手动设置主题，跟随系统主题
    const storedTheme = localStorage.getItem('user_theme')
    if (!storedTheme) {
      const systemTheme = e.matches ? 'dark' : 'light'
      setTheme(systemTheme)
    }
  }

  onMounted(() => {
    mediaQuery.addEventListener('change', handleSystemThemeChange)
  })

  onUnmounted(() => {
    mediaQuery.removeEventListener('change', handleSystemThemeChange)
  })

  return {
    currentTheme,
    isDarkMode,
    toggleTheme,
    setTheme,
    getThemeVar,
    setThemeVar,
    themeClass,
    themeStyles
  }
}

/**
 * 主题工具函数
 */
export const themeUtils = {
  // 应用主题到元素
  applyThemeToElement(element, themeVars = {}) {
    Object.entries(themeVars).forEach(([key, value]) => {
      element.style.setProperty(`--${key}`, value)
    })
  },

  // 获取主题颜色
  getThemeColor(colorName) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(`--${colorName}`)
      .trim()
  },

  // 生成主题样式对象
  createThemeStyles(styleMap) {
    const styles = {}
    Object.entries(styleMap).forEach(([key, varName]) => {
      styles[key] = `var(--${varName})`
    })
    return styles
  },

  // 检查是否为暗黑主题
  isDarkTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark'
  },

  // 主题颜色混合
  mixColors(color1, color2, ratio = 0.5) {
    // 简单的颜色混合实现
    // 实际项目中可以使用更复杂的颜色处理库
    return color1 // 占位实现
  }
}

/**
 * 主题常量
 */
export const THEME_CONSTANTS = {
  THEMES: {
    LIGHT: 'light',
    DARK: 'dark'
  },
  
  STORAGE_KEY: 'user_theme',
  
  CSS_VARS: {
    // 基础颜色
    PRIMARY: 'primary',
    SUCCESS: 'success',
    WARNING: 'warning',
    DANGER: 'danger',
    INFO: 'info',
    
    // 背景颜色
    BG_PRIMARY: 'bg-primary',
    BG_SECONDARY: 'bg-secondary',
    BG_TERTIARY: 'bg-tertiary',
    BG_OVERLAY: 'bg-overlay',
    
    // 文本颜色
    TEXT_PRIMARY: 'text-primary',
    TEXT_SECONDARY: 'text-secondary',
    TEXT_TERTIARY: 'text-tertiary',
    TEXT_QUATERNARY: 'text-quaternary',
    
    // 边框颜色
    BORDER_PRIMARY: 'border-primary',
    BORDER_SECONDARY: 'border-secondary',
    BORDER_TERTIARY: 'border-tertiary',
    BORDER_QUATERNARY: 'border-quaternary',
    
    // 填充颜色
    FILL_PRIMARY: 'fill-primary',
    FILL_SECONDARY: 'fill-secondary',
    FILL_TERTIARY: 'fill-tertiary',
    FILL_QUATERNARY: 'fill-quaternary'
  }
}