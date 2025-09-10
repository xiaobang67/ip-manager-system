#!/usr/bin/env node

/**
 * 主题系统批量更新脚本
 * 用于将现有组件迁移到新的统一主题系统
 */

const fs = require('fs')
const path = require('path')
const { updateVueThemeVars, updateCSSThemeVars, generateMigrationReport } = require('./src/utils/themeUpdater.js')

// 需要更新的文件类型
const FILE_EXTENSIONS = ['.vue', '.css']

// 需要扫描的目录
const SCAN_DIRECTORIES = [
  './src/components',
  './src/views',
  './src/styles'
]

/**
 * 递归获取目录下的所有文件
 */
function getAllFiles(dirPath, fileList = []) {
  const files = fs.readdirSync(dirPath)
  
  files.forEach(file => {
    const filePath = path.join(dirPath, file)
    const stat = fs.statSync(filePath)
    
    if (stat.isDirectory()) {
      getAllFiles(filePath, fileList)
    } else {
      const ext = path.extname(file)
      if (FILE_EXTENSIONS.includes(ext)) {
        fileList.push(filePath)
      }
    }
  })
  
  return fileList
}

/**
 * 更新单个文件
 */
function updateFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8')
    const ext = path.extname(filePath)
    
    let updatedContent = content
    
    if (ext === '.vue') {
      updatedContent = updateVueThemeVars(content)
    } else if (ext === '.css') {
      updatedContent = updateCSSThemeVars(content)
    }
    
    // 生成迁移报告
    const report = generateMigrationReport(content, filePath)
    
    return {
      filePath,
      hasChanges: updatedContent !== content,
      updatedContent,
      report
    }
  } catch (error) {
    console.error(`Error processing file ${filePath}:`, error.message)
    return null
  }
}

/**
 * 主函数
 */
function main() {
  console.log('🎨 开始批量更新主题系统...\n')
  
  // 获取所有需要更新的文件
  let allFiles = []
  SCAN_DIRECTORIES.forEach(dir => {
    if (fs.existsSync(dir)) {
      const files = getAllFiles(dir)
      allFiles = allFiles.concat(files)
    }
  })
  
  console.log(`📁 找到 ${allFiles.length} 个文件需要检查\n`)
  
  // 更新文件
  const results = []
  let updatedCount = 0
  let errorCount = 0
  
  allFiles.forEach(filePath => {
    const result = updateFile(filePath)
    if (result) {
      results.push(result)
      if (result.hasChanges) {
        updatedCount++
        console.log(`✅ 更新: ${result.filePath}`)
        
        // 显示发现的问题
        if (result.report.oldVarsFound.length > 0) {
          console.log(`   - 发现旧变量: ${result.report.oldVarsFound.join(', ')}`)
        }
        if (result.report.oldClassesFound.length > 0) {
          console.log(`   - 发现旧类名: ${result.report.oldClassesFound.join(', ')}`)
        }
        if (result.report.suggestions.length > 0) {
          console.log(`   - 建议: ${result.report.suggestions.join(', ')}`)
        }
        
        // 写入更新后的内容（可选，默认不写入，只显示预览）
        if (process.argv.includes('--write')) {
          fs.writeFileSync(result.filePath, result.updatedContent, 'utf8')
          console.log(`   ✍️  已写入文件`)
        }
        
        console.log('')
      }
    } else {
      errorCount++
    }
  })
  
  // 显示统计信息
  console.log('\n📊 更新统计:')
  console.log(`- 检查文件: ${allFiles.length}`)
  console.log(`- 需要更新: ${updatedCount}`)
  console.log(`- 处理错误: ${errorCount}`)
  
  // 生成详细报告
  if (process.argv.includes('--report')) {
    const reportPath = './theme-migration-report.json'
    fs.writeFileSync(reportPath, JSON.stringify(results, null, 2))
    console.log(`\n📋 详细报告已保存到: ${reportPath}`)
  }
  
  // 显示使用说明
  if (!process.argv.includes('--write')) {
    console.log('\n💡 提示:')
    console.log('- 当前为预览模式，不会修改文件')
    console.log('- 使用 --write 参数实际写入文件')
    console.log('- 使用 --report 参数生成详细报告')
    console.log('\n示例: node update-theme-system.js --write --report')
  }
  
  console.log('\n🎉 主题系统更新完成!')
}

// 运行脚本
if (require.main === module) {
  main()
}

module.exports = {
  getAllFiles,
  updateFile,
  main
}