<template>
  <div class="theme-test-page" v-theme="pageContainer">
    <!-- 页面标题 -->
    <div class="header-section" v-theme="contentCard">
      <h1>主题系统测试页面</h1>
      <p>测试统一主题系统在各种组件中的表现</p>
      
      <!-- 主题切换按钮 -->
      <div class="theme-controls">
        <el-button @click="toggleTheme">
          切换到{{ isDarkMode ? '明亮' : '暗黑' }}主题
        </el-button>
        <el-tag :type="isDarkMode ? 'info' : 'warning'">
          当前主题: {{ currentTheme }}
        </el-tag>
      </div>
    </div>

    <!-- 基础组件测试 -->
    <div class="test-section" v-theme="contentCard">
      <h2>基础组件测试</h2>
      
      <!-- 表单组件 -->
      <div class="form-test">
        <h3>表单组件</h3>
        <el-form :model="testForm" label-width="100px">
          <el-form-item label="用户名">
            <el-input v-model="testForm.username" placeholder="请输入用户名" />
          </el-form-item>
          
          <el-form-item label="邮箱">
            <el-input v-model="testForm.email" type="email" placeholder="请输入邮箱" />
          </el-form-item>
          
          <el-form-item label="角色">
            <el-select v-model="testForm.role" placeholder="请选择角色">
              <el-option label="管理员" value="admin" />
              <el-option label="用户" value="user" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="主题偏好">
            <el-radio-group v-model="testForm.theme">
              <el-radio label="light">明亮主题</el-radio>
              <el-radio label="dark">暗黑主题</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item label="描述">
            <el-input 
              v-model="testForm.description" 
              type="textarea" 
              :rows="3"
              placeholder="请输入描述"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- 按钮组件 -->
      <div class="button-test">
        <h3>按钮组件</h3>
        <div class="button-group">
          <el-button>默认按钮</el-button>
          <el-button type="primary">主要按钮</el-button>
          <el-button type="success">成功按钮</el-button>
          <el-button type="warning">警告按钮</el-button>
          <el-button type="danger">危险按钮</el-button>
          <el-button type="info">信息按钮</el-button>
        </div>
      </div>

      <!-- 标签组件 -->
      <div class="tag-test">
        <h3>标签组件</h3>
        <div class="tag-group">
          <el-tag>默认标签</el-tag>
          <el-tag type="success">成功标签</el-tag>
          <el-tag type="warning">警告标签</el-tag>
          <el-tag type="danger">危险标签</el-tag>
          <el-tag type="info">信息标签</el-tag>
        </div>
      </div>
    </div>

    <!-- 统计卡片测试 -->
    <div class="theme-stats-card">
      <h2>统计卡片测试</h2>
      <div class="stats-grid">
        <div class="theme-stats-card" v-theme="statsCard">
          <div class="stats-value">1,234</div>
          <div class="stats-label">总用户数</div>
        </div>
        
        <div class="theme-stats-card" v-theme="statsCard">
          <div class="stats-value">567</div>
          <div class="stats-label">在线用户</div>
        </div>
        
        <div class="theme-stats-card" v-theme="statsCard">
          <div class="stats-value">89</div>
          <div class="stats-label">今日新增</div>
        </div>
        
        <div class="theme-stats-card" v-theme="statsCard">
          <div class="stats-value">12</div>
          <div class="stats-label">系统告警</div>
        </div>
      </div>
    </div>

    <!-- 表格测试 -->
    <div class="theme-table-section" v-theme="tableSection">
      <h2>表格测试</h2>
      <el-table :data="tableData" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="scope">
            <el-tag :type="getRoleType(scope.row.role)">
              {{ getRoleText(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'active' ? 'success' : 'info'">
              {{ scope.row.status === 'active' ? '活跃' : '非活跃' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createTime" label="创建时间" />
      </el-table>
    </div>

    <!-- 对话框测试 -->
    <div class="dialog-section" v-theme="contentCard">
      <h2>对话框测试</h2>
      <el-button type="primary" @click="showDialog = true">
        打开对话框
      </el-button>
      
      <el-dialog v-model="showDialog" title="测试对话框" width="500px">
        <div class="dialog-content">
          <p>这是一个测试对话框，用于验证主题系统在对话框中的表现。</p>
          
          <el-form :model="dialogForm" label-width="80px">
            <el-form-item label="标题">
              <el-input v-model="dialogForm.title" placeholder="请输入标题" />
            </el-form-item>
            
            <el-form-item label="内容">
              <el-input 
                v-model="dialogForm.content" 
                type="textarea" 
                :rows="3"
                placeholder="请输入内容"
              />
            </el-form-item>
          </el-form>
        </div>
        
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="showDialog = false">取消</el-button>
            <el-button type="primary" @click="showDialog = false">确定</el-button>
          </div>
        </template>
      </el-dialog>
    </div>

    <!-- 主题变量展示 -->
    <div class="theme-vars-section" v-theme="contentCard">
      <h2>主题变量展示</h2>
      <div class="theme-vars-grid">
        <div class="var-item" v-for="(value, key) in themeStyles" :key="key">
          <div class="var-name">{{ key }}</div>
          <div class="var-value" :style="{ backgroundColor: value }">{{ value }}</div>
        </div>
      </div>
    </div>

    <!-- 自定义主题指令测试 -->
    <div class="directive-section">
      <h2>主题指令测试</h2>
      <div class="directive-examples">
        <div v-theme="'card'" class="example-card">
          <h4>v-theme="card"</h4>
          <p>使用card预设主题</p>
        </div>
        
        <div v-theme="{ backgroundColor: 'bg-primary', color: 'text-primary', padding: '20px' }" class="example-card">
          <h4>自定义主题对象</h4>
          <p>使用自定义主题配置</p>
        </div>
        
        <div v-theme.hover="'card'" class="example-card">
          <h4>v-theme.hover="card"</h4>
          <p>带悬停效果的卡片</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useTheme } from '@/composables/useTheme'

export default {
  name: 'ThemeTest',
  setup() {
    const { currentTheme, isDarkMode, toggleTheme, themeStyles } = useTheme()
    
    return {
      currentTheme,
      isDarkMode,
      toggleTheme,
      themeStyles
    }
  },
  
  data() {
    return {
      showDialog: false,
      
      testForm: {
        username: '',
        email: '',
        role: '',
        theme: 'light',
        description: ''
      },
      
      dialogForm: {
        title: '',
        content: ''
      },
      
      tableData: [
        {
          id: 1,
          name: '张三',
          email: 'zhangsan@example.com',
          role: 'admin',
          status: 'active',
          createTime: '2024-01-01 10:00:00'
        },
        {
          id: 2,
          name: '李四',
          email: 'lisi@example.com',
          role: 'user',
          status: 'active',
          createTime: '2024-01-02 11:00:00'
        },
        {
          id: 3,
          name: '王五',
          email: 'wangwu@example.com',
          role: 'user',
          status: 'inactive',
          createTime: '2024-01-03 12:00:00'
        }
      ]
    }
  },
  
  methods: {
    getRoleType(role) {
      const roleTypes = {
        admin: 'danger',
        manager: 'warning',
        user: 'info'
      }
      return roleTypes[role] || 'info'
    },
    
    getRoleText(role) {
      const roleTexts = {
        admin: '管理员',
        manager: '经理',
        user: '用户'
      }
      return roleTexts[role] || '未知'
    }
  }
}
</script>

<style scoped>
.theme-test-page {
  padding: var(--spacing-lg);
  min-height: 100vh;
}

.header-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
}

.header-section h1 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.header-section p {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-secondary);
}

.theme-controls {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.test-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
}

.test-section h2 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.form-test,
.button-test,
.tag-test {
  margin-bottom: var(--spacing-xl);
}

.form-test h3,
.button-test h3,
.tag-test h3 {
  margin: 0 0 var(--spacing-md) 0;
  color: var(--text-primary);
}

.button-group,
.tag-group {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.stats-section {
  margin-bottom: var(--spacing-xl);
}

.stats-section h2 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-lg);
}

.stats-card {
  padding: var(--spacing-xl);
  border-radius: var(--radius-large);
  text-align: center;
  transition: all var(--transition-base);
}

.stats-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--primary);
  margin-bottom: var(--spacing-sm);
}

.stats-label {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.table-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
}

.table-section h2 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.dialog-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
}

.dialog-section h2 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.dialog-content {
  color: var(--text-primary);
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
}

.theme-vars-section {
  margin-bottom: var(--spacing-xl);
  padding: var(--spacing-xl);
  border-radius: var(--radius-xl);
}

.theme-vars-section h2 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.theme-vars-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--spacing-md);
}

.var-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background-color: var(--fill-primary);
  border-radius: var(--radius-base);
}

.var-name {
  font-size: 0.8rem;
  color: var(--text-secondary);
  min-width: 80px;
}

.var-value {
  flex: 1;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--radius-small);
  font-size: 0.8rem;
  color: var(--text-primary);
  border: 1px solid var(--border-primary);
}

.directive-section {
  margin-bottom: var(--spacing-xl);
}

.directive-section h2 {
  margin: 0 0 var(--spacing-lg) 0;
  color: var(--text-primary);
}

.directive-examples {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--spacing-lg);
}

.example-card {
  padding: var(--spacing-lg);
  border-radius: var(--radius-large);
  border: 1px solid var(--border-primary);
}

.example-card h4 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--text-primary);
}

.example-card p {
  margin: 0;
  color: var(--text-secondary);
}
</style>