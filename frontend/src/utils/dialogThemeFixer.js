/**
 * 对话框主题修复器
 * 专门针对个人信息对话框等Element Plus对话框的主题问题
 */

/**
 * 强制修复对话框主题
 */
function forceFixDialogTheme() {
  const isDarkTheme = document.documentElement.getAttribute('data-theme') === 'dark'
  if (!isDarkTheme) return

  // 查找所有对话框
  const dialogs = document.querySelectorAll('.el-dialog')
  
  dialogs.forEach(dialog => {
    // 只修复对话框本身的背景
    dialog.style.setProperty('background-color', 'var(--bg-primary)', 'important')
    
    // 精准修复对话框内的特定元素
    
    // 修复表单标签
    const labels = dialog.querySelectorAll('.el-form-item__label, .el-radio__label, .el-checkbox__label')
    labels.forEach(label => {
      label.style.setProperty('color', 'var(--text-primary)', 'important')
      label.style.setProperty('background-color', 'transparent', 'important')
    })
    
    // 修复输入框
    const inputs = dialog.querySelectorAll('.el-input__inner, .el-textarea__inner')
    inputs.forEach(input => {
      input.style.setProperty('background-color', 'var(--bg-primary)', 'important')
      input.style.setProperty('color', 'var(--text-primary)', 'important')
      input.style.setProperty('border-color', 'var(--border-primary)', 'important')
    })
    
    // 修复标签页容器
    const tabsContainers = dialog.querySelectorAll('.el-tabs, .el-tab-pane, .el-tabs__content, .el-tabs__header')
    tabsContainers.forEach(container => {
      container.style.setProperty('background-color', 'var(--bg-primary)', 'important')
    })
    
    // 修复对话框头部和底部
    const headers = dialog.querySelectorAll('.el-dialog__header')
    headers.forEach(header => {
      header.style.setProperty('background-color', 'var(--bg-primary)', 'important')
    })
    
    const bodies = dialog.querySelectorAll('.el-dialog__body')
    bodies.forEach(body => {
      body.style.setProperty('background-color', 'var(--bg-primary)', 'important')
    })
  })
}

/**
 * 监听对话框打开事件
 */
function watchDialogOpen() {
  // 使用MutationObserver监听DOM变化
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'childList') {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // 检查是否是对话框或包含对话框
            if (node.classList?.contains('el-dialog') || 
                node.querySelector?.('.el-dialog')) {
              setTimeout(forceFixDialogTheme, 50)
            }
          }
        })
      }
    })
  })
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  })
  
  return observer
}

/**
 * 初始化对话框主题修复器
 */
function initDialogThemeFixer() {
  console.log('🔧 初始化对话框主题修复器...')
  
  // 立即修复现有对话框
  forceFixDialogTheme()
  
  // 监听新对话框
  const observer = watchDialogOpen()
  
  // 定期检查
  const intervalId = setInterval(forceFixDialogTheme, 1000)
  
  return () => {
    observer.disconnect()
    clearInterval(intervalId)
  }
}

export {
  forceFixDialogTheme,
  initDialogThemeFixer
}