/**
 * 主题强制执行器
 * 动态检查和修复所有白色背景问题
 */

// 白色背景的各种表示方式
const WHITE_BACKGROUNDS = [
  'rgb(255, 255, 255)',
  'rgba(255, 255, 255, 1)',
  '#ffffff',
  '#fff',
  'white',
  'hsl(0, 0%, 100%)',
  'hsla(0, 0%, 100%, 1)'
]

// 黑色文字的各种表示方式
const BLACK_TEXTS = [
  'rgb(0, 0, 0)',
  'rgba(0, 0, 0, 1)',
  '#000000',
  '#000',
  'black',
  'hsl(0, 0%, 0%)',
  'hsla(0, 0%, 0%, 1)'
]

// 需要保留原色的元素选择器
const PRESERVE_COLOR_SELECTORS = [
  '.el-button--primary',
  '.el-button--success',
  '.el-button--warning',
  '.el-button--danger',
  '.el-button--info',
  '.el-tag--primary',
  '.el-tag--success',
  '.el-tag--warning',
  '.el-tag--danger',
  '.el-tag--info',
  '.el-progress__text',
  '.el-badge__content'
]

/**
 * 检查元素是否应该保留原色
 */
function shouldPreserveColor(element) {
  return PRESERVE_COLOR_SELECTORS.some(selector => {
    try {
      return element.matches(selector)
    } catch (e) {
      return false
    }
  })
}

/**
 * 检查颜色是否为白色
 */
function isWhiteColor(color) {
  if (!color) return false
  const normalizedColor = color.toLowerCase().replace(/\s/g, '')
  return WHITE_BACKGROUNDS.some(white => 
    normalizedColor === white.toLowerCase().replace(/\s/g, '')
  )
}

/**
 * 检查颜色是否为黑色
 */
function isBlackColor(color) {
  if (!color) return false
  const normalizedColor = color.toLowerCase().replace(/\s/g, '')
  return BLACK_TEXTS.some(black => 
    normalizedColor === black.toLowerCase().replace(/\s/g, '')
  )
}

/**
 * 获取CSS变量值
 */
function getCSSVar(varName) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(`--${varName}`)
    .trim()
}

/**
 * 修复单个元素的主题
 */
function fixElementTheme(element) {
  if (!element || element.nodeType !== Node.ELEMENT_NODE) return

  const computedStyle = getComputedStyle(element)
  const backgroundColor = computedStyle.backgroundColor
  const color = computedStyle.color
  
  // 检查是否为暗黑主题
  const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
  if (!isDarkTheme) return

  let fixed = false

  // 只修复明确有白色背景的元素，且只针对特定的Element Plus组件
  const isElementPlusComponent = element.className && element.className.includes && element.className.includes('el-')
  
  if (isWhiteColor(backgroundColor) && !shouldPreserveColor(element) && isElementPlusComponent) {
    // 只对特定的Element Plus组件修复背景
    if (element.classList.contains('el-dialog') ||
        element.classList.contains('el-form-item__label') ||
        element.classList.contains('el-tabs') ||
        element.classList.contains('el-tab-pane') ||
        element.classList.contains('el-input__inner') ||
        element.classList.contains('el-textarea__inner')) {
      element.style.setProperty('background-color', 'var(--bg-primary)', 'important')
      fixed = true
    }
  }

  // 修复黑色文字（只针对标签等文本元素）
  if (isBlackColor(color) && !shouldPreserveColor(element)) {
    if (element.classList.contains('el-form-item__label') ||
        element.classList.contains('el-radio__label') ||
        element.classList.contains('el-checkbox__label')) {
      element.style.setProperty('color', 'var(--text-primary)', 'important')
      fixed = true
    }
  }

  return fixed
}

/**
 * 扫描并修复所有元素
 */
function scanAndFixAllElements() {
  const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
  if (!isDarkTheme) return

  let fixedCount = 0
  const allElements = document.querySelectorAll('*')
  
  allElements.forEach(element => {
    if (fixElementTheme(element)) {
      fixedCount++
    }
  })

  if (fixedCount > 0) {
    console.log(`🎨 主题强制执行器: 修复了 ${fixedCount} 个元素的主题问题`)
  }

  return fixedCount
}

/**
 * 监听DOM变化并自动修复新元素
 */
function startThemeObserver() {
  const observer = new MutationObserver((mutations) => {
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
    if (!isDarkTheme) return

    let needsFix = false

    mutations.forEach((mutation) => {
      // 监听属性变化（主题切换）
      if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
        needsFix = true
      }
      
      // 监听新增节点
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // 修复新增的元素及其子元素
            fixElementTheme(node)
            node.querySelectorAll('*').forEach(child => {
              fixElementTheme(child)
            })
          }
        })
      }
    })

    if (needsFix) {
      // 延迟执行，确保主题切换完成
      setTimeout(scanAndFixAllElements, 100)
    }
  })

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
    childList: true,
    subtree: true
  })

  return observer
}

/**
 * 强制修复特定容器内的所有元素
 */
function forceFixContainer(container) {
  if (!container) return

  const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
  if (!isDarkTheme) return

  // 添加强制暗黑主题类
  container.classList.add('force-dark-theme')

  // 修复容器内所有元素
  const elements = container.querySelectorAll('*')
  let fixedCount = 0

  elements.forEach(element => {
    if (fixElementTheme(element)) {
      fixedCount++
    }
  })

  console.log(`🎨 强制修复容器: 修复了 ${fixedCount} 个元素`)
  return fixedCount
}

/**
 * 修复Element Plus对话框
 */
function fixElementPlusDialogs() {
  const dialogs = document.querySelectorAll('.el-dialog, .el-drawer, .el-popover')
  
  dialogs.forEach(dialog => {
    forceFixContainer(dialog)
    
    // 特别处理对话框内的标签页
    const tabs = dialog.querySelectorAll('.el-tabs')
    tabs.forEach(tab => {
      forceFixContainer(tab)
    })
  })
}

/**
 * 初始化主题强制执行器
 */
function initThemeEnforcer() {
  console.log('🎨 初始化主题强制执行器...')

  // 立即扫描一次
  scanAndFixAllElements()

  // 启动观察器
  const observer = startThemeObserver()

  // 定期检查（兜底机制）
  const intervalId = setInterval(() => {
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
    if (isDarkTheme) {
      scanAndFixAllElements()
      fixElementPlusDialogs()
    }
  }, 2000) // 每2秒检查一次

  // 监听Element Plus组件事件
  document.addEventListener('click', (e) => {
    // 当点击可能触发弹出层的元素时，延迟修复
    if (e.target.closest('.el-button, .el-select, .el-dropdown')) {
      setTimeout(() => {
        fixElementPlusDialogs()
        scanAndFixAllElements()
      }, 100)
    }
  })

  // 返回清理函数
  return () => {
    observer.disconnect()
    clearInterval(intervalId)
  }
}

/**
 * 调试工具
 */
const debugTools = {
  // 高亮所有白色背景元素
  highlightWhiteBackgrounds() {
    document.body.classList.add('debug-white-bg')
    console.log('🔍 调试模式: 已高亮所有白色背景元素（红色边框）')
  },

  // 高亮所有Element Plus组件
  highlightElementPlusComponents() {
    document.body.classList.add('debug-el-components')
    console.log('🔍 调试模式: 已高亮所有Element Plus组件（绿色边框）')
  },

  // 关闭调试模式
  disableDebug() {
    document.body.classList.remove('debug-white-bg', 'debug-el-components')
    console.log('🔍 调试模式已关闭')
  },

  // 手动扫描并报告问题
  scanAndReport() {
    const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
    if (!isDarkTheme) {
      console.log('当前不是暗黑主题，无需检查')
      return
    }

    const allElements = document.querySelectorAll('*')
    const whiteBackgrounds = []
    const blackTexts = []

    allElements.forEach(element => {
      const computedStyle = getComputedStyle(element)
      
      if (isWhiteColor(computedStyle.backgroundColor)) {
        whiteBackgrounds.push(element)
      }
      
      if (isBlackColor(computedStyle.color)) {
        blackTexts.push(element)
      }
    })

    console.log(`🔍 扫描结果:`)
    console.log(`- 发现 ${whiteBackgrounds.length} 个白色背景元素`)
    console.log(`- 发现 ${blackTexts.length} 个黑色文字元素`)
    
    if (whiteBackgrounds.length > 0) {
      console.log('白色背景元素:', whiteBackgrounds)
    }
    
    if (blackTexts.length > 0) {
      console.log('黑色文字元素:', blackTexts)
    }

    return {
      whiteBackgrounds,
      blackTexts
    }
  }
}

// 导出
export {
  initThemeEnforcer,
  scanAndFixAllElements,
  forceFixContainer,
  fixElementPlusDialogs,
  debugTools
}

// 如果在浏览器环境中，添加到全局对象
if (typeof window !== 'undefined') {
  window.themeEnforcer = {
    init: initThemeEnforcer,
    scan: scanAndFixAllElements,
    fixContainer: forceFixContainer,
    fixDialogs: fixElementPlusDialogs,
    debug: debugTools
  }
}