/**
 * 主题更新工具
 * 用于批量更新现有组件使用新的统一主题系统
 */

// 旧主题变量到新主题变量的映射
const THEME_VAR_MAPPING = {
  // 背景颜色映射
  '--bg-color': '--bg-primary',
  '--bg-color-page': '--bg-secondary',
  '--bg-color-overlay': '--bg-overlay',
  
  // 文本颜色映射
  '--text-color-primary': '--text-primary',
  '--text-color-regular': '--text-secondary',
  '--text-color-secondary': '--text-tertiary',
  '--text-color-placeholder': '--text-quaternary',
  
  // 边框颜色映射
  '--border-color': '--border-primary',
  '--border-color-light': '--border-secondary',
  '--border-color-lighter': '--border-tertiary',
  '--border-color-extra-light': '--border-quaternary',
  
  // 填充颜色映射
  '--fill-color': '--fill-primary',
  '--fill-color-light': '--fill-secondary',
  '--fill-color-lighter': '--fill-tertiary',
  '--fill-color-extra-light': '--fill-quaternary',
  '--fill-color-blank': '--bg-primary',
  
  // 状态颜色映射
  '--primary-color': '--primary',
  '--success-color': '--success',
  '--warning-color': '--warning',
  '--danger-color': '--danger',
  '--info-color': '--info',
  
  // 阴影映射
  '--box-shadow': '--shadow-light',
  '--box-shadow-light': '--shadow-base',
  '--box-shadow-base': '--shadow-light',
  '--box-shadow-dark': '--shadow-dark',
  
  // 遮罩映射
  '--mask-color': '--bg-mask',
  '--overlay-color': '--bg-mask'
}

// 常用的主题类名映射
const THEME_CLASS_MAPPING = {
  // 页面容器
  'page-container': 'theme-container',
  'content-container': 'theme-card',
  
  // 搜索区域
  'filter-section': 'theme-search-section',
  'search-section': 'theme-search-section',
  
  // 统计卡片
  'stats-card': 'theme-stats-card',
  'stats-section': 'theme-stats-card',
  
  // 表格区域
  'table-section': 'theme-table-section',
  
  // 文本样式
  'text-primary': 'theme-text-primary',
  'text-secondary': 'theme-text-secondary',
  'text-tertiary': 'theme-text-tertiary'
}

/**
 * 更新CSS文件中的主题变量
 * @param {string} cssContent - CSS文件内容
 * @returns {string} - 更新后的CSS内容
 */
export function updateCSSThemeVars(cssContent) {
  let updatedContent = cssContent
  
  // 替换CSS变量
  Object.entries(THEME_VAR_MAPPING).forEach(([oldVar, newVar]) => {
    const regex = new RegExp(`var\\(${oldVar.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')}\\)`, 'g')
    updatedContent = updatedContent.replace(regex, `var(${newVar})`)
    
    // 也替换直接使用的变量名
    const directRegex = new RegExp(oldVar.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&'), 'g')
    updatedContent = updatedContent.replace(directRegex, newVar)
  })
  
  return updatedContent
}

/**
 * 更新Vue组件中的主题变量
 * @param {string} vueContent - Vue文件内容
 * @returns {string} - 更新后的Vue内容
 */
export function updateVueThemeVars(vueContent) {
  let updatedContent = vueContent
  
  // 更新<style>标签中的CSS变量
  updatedContent = updatedContent.replace(/<style[^>]*>([\s\S]*?)<\/style>/gi, (match, styleContent) => {
    const updatedStyleContent = updateCSSThemeVars(styleContent)
    return match.replace(styleContent, updatedStyleContent)
  })
  
  // 更新模板中的类名
  Object.entries(THEME_CLASS_MAPPING).forEach(([oldClass, newClass]) => {
    const regex = new RegExp(`class="([^"]*\\s)?${oldClass.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&')}(\\s[^"]*)?"`,'g')
    updatedContent = updatedContent.replace(regex, (match, prefix = '', suffix = '') => {
      return `class="${prefix}${newClass}${suffix}"`
    })
  })
  
  return updatedContent
}

/**
 * 生成主题迁移报告
 * @param {string} content - 文件内容
 * @param {string} filePath - 文件路径
 * @returns {Object} - 迁移报告
 */
export function generateMigrationReport(content, filePath) {
  const report = {
    filePath,
    oldVarsFound: [],
    oldClassesFound: [],
    suggestions: []
  }
  
  // 检查旧的CSS变量
  Object.keys(THEME_VAR_MAPPING).forEach(oldVar => {
    if (content.includes(oldVar)) {
      report.oldVarsFound.push(oldVar)
    }
  })
  
  // 检查旧的类名
  Object.keys(THEME_CLASS_MAPPING).forEach(oldClass => {
    const regex = new RegExp(`class="[^"]*${oldClass}[^"]*"`, 'g')
    if (regex.test(content)) {
      report.oldClassesFound.push(oldClass)
    }
  })
  
  // 生成建议
  if (report.oldVarsFound.length > 0) {
    report.suggestions.push('建议使用新的统一主题变量系统')
  }
  
  if (report.oldClassesFound.length > 0) {
    report.suggestions.push('建议使用新的主题类名或v-theme指令')
  }
  
  // 检查是否可以使用v-theme指令
  if (content.includes('el-card') || content.includes('el-dialog') || content.includes('el-form')) {
    report.suggestions.push('可以考虑使用v-theme指令简化主题应用')
  }
  
  return report
}

/**
 * 自动应用主题指令建议
 * @param {string} vueContent - Vue文件内容
 * @returns {string} - 更新后的内容
 */
export function applyThemeDirectiveSuggestions(vueContent) {
  let updatedContent = vueContent
  
  // 为常见元素添加v-theme指令
  const elementMappings = [
    {
      pattern: /<div\s+class="[^"]*page-container[^"]*"/g,
      replacement: '<div v-theme="pageContainer" class="page-container"'
    },
    {
      pattern: /<div\s+class="[^"]*content-container[^"]*"/g,
      replacement: '<div v-theme="contentCard" class="content-container"'
    },
    {
      pattern: /<div\s+class="[^"]*filter-section[^"]*"/g,
      replacement: '<div v-theme="searchSection" class="filter-section"'
    },
    {
      pattern: /<div\s+class="[^"]*stats-card[^"]*"/g,
      replacement: '<div v-theme="statsCard" class="stats-card"'
    },
    {
      pattern: /<div\s+class="[^"]*table-section[^"]*"/g,
      replacement: '<div v-theme="tableSection" class="table-section"'
    }
  ]
  
  elementMappings.forEach(({ pattern, replacement }) => {
    updatedContent = updatedContent.replace(pattern, replacement)
  })
  
  return updatedContent
}

/**
 * 批量更新文件的主题系统
 * @param {Array} files - 文件列表 [{path, content}]
 * @returns {Array} - 更新结果
 */
export function batchUpdateThemeSystem(files) {
  const results = []
  
  files.forEach(file => {
    const { path, content } = file
    const fileExtension = path.split('.').pop().toLowerCase()
    
    let updatedContent = content
    let report = generateMigrationReport(content, path)
    
    // 根据文件类型应用不同的更新策略
    if (fileExtension === 'vue') {
      updatedContent = updateVueThemeVars(content)
      updatedContent = applyThemeDirectiveSuggestions(updatedContent)
    } else if (fileExtension === 'css') {
      updatedContent = updateCSSThemeVars(content)
    }
    
    results.push({
      path,
      originalContent: content,
      updatedContent,
      report,
      hasChanges: updatedContent !== content
    })
  })
  
  return results
}

/**
 * 生成主题系统使用指南
 * @returns {string} - 使用指南
 */
export function generateThemeGuide() {
  return `
# 统一主题系统使用指南

## 1. CSS变量使用

### 背景颜色
- --bg-primary: 主要背景色（卡片、对话框等）
- --bg-secondary: 次要背景色（页面背景）
- --bg-tertiary: 第三级背景色
- --bg-overlay: 覆盖层背景色

### 文本颜色
- --text-primary: 主要文本色
- --text-secondary: 次要文本色
- --text-tertiary: 第三级文本色
- --text-quaternary: 占位符文本色
- --text-inverse: 反色文本（通常为白色）

### 边框颜色
- --border-primary: 主要边框色
- --border-secondary: 次要边框色
- --border-tertiary: 第三级边框色
- --border-quaternary: 第四级边框色

### 状态颜色
- --primary: 主色调
- --success: 成功色
- --warning: 警告色
- --danger: 危险色
- --info: 信息色

## 2. 主题指令使用

### 基础用法
\`\`\`html
<!-- 应用预设主题 -->
<div v-theme="card">内容</div>
<div v-theme="input">输入框</div>
<div v-theme="button">按钮</div>

<!-- 自定义主题 -->
<div v-theme="{backgroundColor: 'bg-primary', color: 'text-primary'}">内容</div>
\`\`\`

### 修饰符
\`\`\`html
<!-- 重要样式 -->
<div v-theme.important="card">内容</div>

<!-- 悬停效果 -->
<div v-theme.hover="card">内容</div>
\`\`\`

## 3. Composable使用

\`\`\`javascript
import { useTheme } from '@/composables/useTheme'

export default {
  setup() {
    const { currentTheme, isDarkMode, toggleTheme, themeStyles } = useTheme()
    
    return {
      currentTheme,
      isDarkMode,
      toggleTheme,
      themeStyles
    }
  }
}
\`\`\`

## 4. 预设类名

- .theme-container: 页面容器
- .theme-card: 内容卡片
- .theme-search-section: 搜索区域
- .theme-stats-card: 统计卡片
- .theme-table-section: 表格区域
- .theme-text-primary: 主要文本
- .theme-bg-primary: 主要背景

## 5. 最佳实践

1. 优先使用CSS变量而不是硬编码颜色
2. 使用v-theme指令简化重复的主题应用
3. 利用预设类名保持一致性
4. 在组件中使用useTheme composable获取主题状态
5. 避免在样式中使用!important，除非必要
`
}

export default {
  updateCSSThemeVars,
  updateVueThemeVars,
  generateMigrationReport,
  applyThemeDirectiveSuggestions,
  batchUpdateThemeSystem,
  generateThemeGuide,
  THEME_VAR_MAPPING,
  THEME_CLASS_MAPPING
}