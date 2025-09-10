<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <el-header class="app-header">
      <div class="header-left">
        <!-- 侧边栏折叠按钮 -->
        <el-button 
          v-if="isAuthenticated"
          type="text" 
          class="sidebar-toggle"
          @click="toggleSidebar"
        >
          <el-icon><Expand v-if="sidebarCollapsed" /><Fold v-else /></el-icon>
        </el-button>
        <h1 class="app-title">网络资源管理系统</h1>
      </div>
      
      <div class="header-right">
        <!-- 主题切换按钮 -->
        <ThemeToggle />
        
        <!-- 用户菜单 -->
        <el-dropdown v-if="isAuthenticated" @command="handleUserMenuCommand">
          <el-button type="text" class="user-menu-button">
            <el-icon><User /></el-icon>
            {{ userName }}
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <el-icon><Setting /></el-icon>
                个人设置
              </el-dropdown-item>
              <el-dropdown-item divided command="logout">
                <el-icon><SwitchButton /></el-icon>
                退出登录
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        
        <!-- 未登录时的登录按钮 -->
        <el-button v-else type="primary" @click="$router.push('/login')">
          登录
        </el-button>
      </div>
    </el-header>
    
    <!-- 主体容器 -->
    <el-container class="app-container">
      <!-- 侧边导航栏 -->
      <el-aside 
        v-if="isAuthenticated"
        :width="sidebarWidth" 
        class="app-sidebar"
        :class="{ 'sidebar-collapsed': sidebarCollapsed }"
      >
        <div class="sidebar-content">
          <!-- 系统标题区域 -->
          <div class="sidebar-header">
            <div class="system-info">
              <div class="system-title" v-show="!sidebarCollapsed">网络资源管理系统</div>
              <div class="system-subtitle" v-show="!sidebarCollapsed">企业网络资源管理平台</div>
            </div>
          </div>
          
          <!-- 导航菜单 -->
          <el-menu
            :default-active="activeMenu"
            class="sidebar-menu"
            :collapse="sidebarCollapsed"
            :collapse-transition="false"
            router
          >
            <el-menu-item index="/dashboard">
              <el-icon><Monitor /></el-icon>
              <template #title>仪表盘</template>
            </el-menu-item>
            
            <el-sub-menu index="network-resources">
              <template #title>
                <el-icon><Connection /></el-icon>
                <span>网络资源管理</span>
              </template>
              <el-menu-item index="/ip-management">
                <el-icon><Grid /></el-icon>
                <template #title>IP地址管理</template>
              </el-menu-item>
              <el-menu-item index="/device-type-management">
                <el-icon><Monitor /></el-icon>
                <template #title>设备类型管理</template>
              </el-menu-item>
            </el-sub-menu>
            
            <el-menu-item index="/subnet-management">
              <el-icon><Grid /></el-icon>
              <template #title>网段管理</template>
            </el-menu-item>
            
            <el-sub-menu 
              v-if="userRole?.toLowerCase() === 'admin'"
              index="system-management"
            >
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </template>
              <el-menu-item index="/user-management">
                <el-icon><User /></el-icon>
                <template #title>用户管理</template>
              </el-menu-item>
              <el-menu-item index="/department-management">
                <el-icon><OfficeBuilding /></el-icon>
                <template #title>组织管理</template>
              </el-menu-item>
            </el-sub-menu>
            
            <el-menu-item 
              v-if="userRole?.toLowerCase() === 'admin'"
              index="/audit-logs"
            >
              <el-icon><Document /></el-icon>
              <template #title>审计日志</template>
            </el-menu-item>
          </el-menu>
        </div>
      </el-aside>
      
      <!-- 主要内容区域 -->
      <el-main class="app-main" :class="{ 'main-expanded': !isAuthenticated || sidebarCollapsed }">
        <slot />
      </el-main>
    </el-container>
    
    <!-- 用户个人信息对话框 -->
    <UserProfile v-model="showUserProfile" />
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'
import ThemeToggle from './ThemeToggle.vue'
import UserProfile from './UserProfile.vue'

export default {
  name: 'AppLayout',
  components: {
    ThemeToggle,
    UserProfile
  },
  data() {
    return {
      showUserProfile: false,
      sidebarCollapsed: false
    }
  },
  computed: {
    ...mapGetters('auth', ['isAuthenticated', 'userName', 'userRole']),
    
    // 侧边栏宽度
    sidebarWidth() {
      return this.sidebarCollapsed ? '64px' : '240px'
    },
    
    // 当前激活的菜单项
    activeMenu() {
      return this.$route.path
    }
  },
  methods: {
    ...mapActions('auth', ['logout']),
    
    // 切换侧边栏折叠状态
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
      // 保存折叠状态到本地存储
      localStorage.setItem('sidebarCollapsed', this.sidebarCollapsed.toString())
    },
    
    handleUserMenuCommand(command) {
      switch (command) {
        case 'profile':
          this.showUserProfile = true
          break
        case 'logout':
          this.handleLogout()
          break
      }
    },
    
    async handleLogout() {
      try {
        await this.logout()
        this.$message.success('退出登录成功')
        this.$router.push('/login')
      } catch (error) {
        console.error('Logout error:', error)
        this.$message.error('退出登录失败')
      }
    }
  },
  
  mounted() {
    // 从本地存储恢复侧边栏折叠状态
    const savedState = localStorage.getItem('sidebarCollapsed')
    if (savedState !== null) {
      this.sidebarCollapsed = savedState === 'true'
    }
  }
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  box-shadow: var(--shadow-light-base);
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle {
  color: var(--text-primary) !important;
  font-size: 18px;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  background-color: var(--bg-primary-hover);
  color: var(--primary) !important;
}

.app-title {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-menu-button {
  color: var(--text-primary) !important;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-button:hover {
  color: var(--primary) !important;
}

.app-container {
  flex: 1;
  height: calc(100vh - 60px);
}

/* 侧边栏样式 */
.app-sidebar {
  background: var(--bg-primary) !important;
  border-right: 1px solid var(--border-primary);
  transition: width 0.3s ease;
  overflow: hidden;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid var(--border-primary-lighter);
  background: transparent !important;
}

.system-info {
  text-align: center;
  background: transparent !important;
  padding: 0 8px;
}

.system-title {
  color: var(--text-primary);
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
  background: transparent !important;
}

.system-subtitle {
  color: var(--text-tertiary);
  font-size: 12px;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
  background: transparent !important;
}

.sidebar-collapsed .system-title,
.sidebar-collapsed .system-subtitle {
  opacity: 0;
}

/* 菜单样式 - 左对齐 */
.sidebar-menu {
  flex: 1;
  border: none;
  background: transparent;
  padding: 12px 0;
}

.sidebar-menu :deep(.el-menu-item) {
  color: var(--text-secondary);
  margin: 4px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  height: 48px;
  font-size: 14px;
  font-weight: 500;
  
  /* 强制左对齐 */
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  padding: 0 16px !important;
  text-align: left !important;
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background-color: var(--fill-primary);
  color: var(--primary);
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: var(--primary);
  color: white;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.sidebar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 12px;
  font-size: 18px;
}

/* 子菜单样式 */
.sidebar-menu :deep(.el-sub-menu) {
  margin: 4px 12px;
  border-radius: 8px;
  overflow: hidden;
}

.sidebar-menu :deep(.el-sub-menu__title) {
  color: var(--text-secondary);
  border-radius: 8px;
  transition: all 0.3s ease;
  height: 48px;
  font-size: 14px;
  font-weight: 500;
  
  /* 子菜单标题左对齐 */
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  padding: 0 16px !important;
  text-align: left !important;
}

.sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: var(--fill-primary);
  color: var(--primary);
}

.sidebar-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  background-color: var(--primary);
  color: white;
}

.sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  margin-right: 12px;
  font-size: 18px;
}

/* 子菜单项样式 */
.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  background-color: var(--bg-primary-soft);
  margin: 2px 8px;
  height: 40px;
  font-size: 13px;
  
  /* 子菜单项左对齐 */
  display: flex !important;
  align-items: center !important;
  justify-content: flex-start !important;
  padding: 0 20px !important;
  text-align: left !important;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item:hover) {
  background-color: var(--fill-primary-light);
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item.is-active) {
  background-color: var(--primary-light-7);
  color: var(--primary);
  font-weight: 600;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item .el-icon) {
  margin-right: 8px;
  font-size: 16px;
}

/* 折叠状态下的菜单样式 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item) {
  margin: 4px 8px !important;
  text-align: center !important;
  padding: 0 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 48px !important;
  height: 48px !important;
  border-radius: 8px !important;
  position: relative !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-icon) {
  margin-right: 0 !important;
  margin-left: 0 !important;
  position: static !important;
  transform: none !important;
  font-size: 18px !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-menu-item span) {
  display: none !important;
}

/* 折叠状态下的子菜单样式 */
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu) {
  margin: 4px 8px !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title) {
  text-align: center !important;
  padding: 0 !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  width: 48px !important;
  height: 48px !important;
  border-radius: 8px !important;
  position: relative !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  margin-right: 0 !important;
  margin-left: 0 !important;
  position: static !important;
  transform: none !important;
  font-size: 18px !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title span) {
  display: none !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
  display: none !important;
}

/* 主要内容区域 */
.app-main {
  background-color: var(--bg-primary-page);
  padding: 24px;
  transition: all 0.3s ease;
  overflow-y: auto;
}

.main-expanded {
  margin-left: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .app-sidebar {
    position: fixed;
    left: 0;
    top: 60px;
    height: calc(100vh - 60px);
    z-index: 999;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .app-sidebar:not(.sidebar-collapsed) {
    transform: translateX(0);
  }
  
  .app-main {
    margin-left: 0 !important;
  }
}

@media (max-width: 768px) {
  .app-header {
    padding: 0 16px;
  }
  
  .app-title {
    font-size: 18px;
  }
  
  .header-right {
    gap: 12px;
  }
  
  .app-main {
    padding: 16px;
  }
  
  .sidebar-header {
    padding: 20px 16px;
  }
  
  .system-title {
    font-size: 16px;
  }
}

@media (max-width: 480px) {
  .app-title {
    display: none;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .app-main {
    padding: 12px;
  }
  
  .sidebar-header {
    padding: 16px 12px;
  }
  
  .system-title {
    font-size: 14px;
  }
  
  .system-subtitle {
    font-size: 11px;
  }
}

/* 暗黑主题适配 */
[data-theme="dark"] .app-sidebar {
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
}

[data-theme="dark"] .sidebar-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

/* 动画效果 */
.sidebar-menu :deep(.el-menu-item) {
  position: relative;
  overflow: hidden;
}

.sidebar-menu :deep(.el-menu-item::before) {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  width: 0;
  height: 100%;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  transition: width 0.3s ease;
}

.sidebar-menu :deep(.el-menu-item:hover::before) {
  width: 100%;
}
</style>