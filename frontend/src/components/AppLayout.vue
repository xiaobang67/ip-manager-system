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
        <h1 class="app-title">OST网络资源管理系统</h1>
      </div>
      
      <div class="header-right">
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
            
            <el-sub-menu index="subnet-resources">
              <template #title>
                <el-icon><Grid /></el-icon>
                <span>网段资源管理</span>
              </template>
              <el-menu-item index="/subnet-management">
                <el-icon><Grid /></el-icon>
                <template #title>网段管理</template>
              </el-menu-item>
            </el-sub-menu>
            
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
import UserProfile from './UserProfile.vue'

export default {
  name: 'AppLayout',
  components: {
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
  background-color: #ffffff;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12), 0 0 6px rgba(0, 0, 0, 0.04);
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-toggle {
  color: #303133 !important;
  font-size: 18px;
  padding: 8px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.sidebar-toggle:hover {
  background-color: #f0f2f5;
  color: #409eff !important;
}

.app-title {
  color: #303133;
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
  color: #303133 !important;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-button:hover {
  color: #409eff !important;
}

.app-container {
  flex: 1;
  height: calc(100vh - 60px);
}

/* 侧边栏样式 */
.app-sidebar {
  background: #ffffff !important;
  border-right: 1px solid #dcdfe6;
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
  border-bottom: 1px solid #ebeef5;
  background: transparent !important;
}

.system-info {
  text-align: center;
  background: transparent !important;
  padding: 0 8px;
}

.system-title {
  color: #303133;
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 4px;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s ease;
  background: transparent !important;
}

.system-subtitle {
  color: #909399;
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
  color: #606266;
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
  background-color: #f0f2f5;
  color: #409eff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background-color: #409eff;
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
  color: #606266;
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
  background-color: #f0f2f5;
  color: #409eff;
}

.sidebar-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  background-color: #409eff;
  color: white;
}

.sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  margin-right: 12px;
  font-size: 18px;
}

/* 子菜单项样式 */
.sidebar-menu :deep(.el-sub-menu .el-menu-item) {
  background-color: #f5f7fa;
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
  background-color: #ecf5ff;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item.is-active) {
  background-color: #ecf5ff;
  color: #409eff;
  font-weight: 600;
}

.sidebar-menu :deep(.el-sub-menu .el-menu-item .el-icon) {
  margin-right: 8px;
  font-size: 16px;
}

/* ========== 折叠状态下的统一图标管理标准 ========== */

/* 折叠状态下的菜单容器 */
.sidebar-collapsed .sidebar-menu {
  padding: 12px 0 !important;
}

/* 折叠状态下的菜单项 - 绝对精确居中 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item) {
  /* 精确位置和尺寸 */
  margin: 4px 8px !important;
  width: 48px !important;
  height: 48px !important;
  border-radius: 8px !important;
  
  /* 绝对定位居中 - 最精确的方案 */
  position: relative !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  
  /* 完全清除所有可能影响居中的属性 */
  padding: 0 !important;
  box-sizing: border-box !important;
  text-align: center !important;
  
  /* 清除默认样式 */
  left: 0 !important;
  right: 0 !important;
  top: 0 !important;
  bottom: 0 !important;
  transform: none !important;
  
  /* 过渡动画 */
  transition: all 0.3s ease !important;
}

/* 折叠状态下的菜单项图标 - 绝对精确居中 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-icon) {
  /* 精确图标尺寸 */
  font-size: 18px !important;
  width: 18px !important;
  height: 18px !important;
  
  /* 绝对居中定位 */
  position: absolute !important;
  left: 50% !important;
  top: 50% !important;
  transform: translate(-50%, -50%) !important;
  
  /* 完全清除边距 */
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  outline: none !important;
  
  /* 图标内容居中 */
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  
  /* 行高和垂直对齐 */
  line-height: 1 !important;
  vertical-align: middle !important;
  
  /* 字体渲染优化 */
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
  
  /* 确保图标不会被拉伸 */
  flex-shrink: 0 !important;
  flex-grow: 0 !important;
}

/* 隐藏折叠状态下的文字 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item span),
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-menu-item__title) {
  display: none !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
}

/* 折叠状态下的子菜单 - 精确居中标准 */
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu) {
  /* 子菜单容器精确定位 */
  margin: 4px 8px !important;
  width: 48px !important;
  overflow: visible !important;
}

/* 折叠状态下的子菜单标题 - 精确居中标准 */
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title) {
  /* 精确位置和尺寸 */
  width: 48px !important;
  height: 48px !important;
  border-radius: 8px !important;
  
  /* 精确居中布局 */
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  
  /* 清除所有内边距和外边距 */
  padding: 0 !important;
  box-sizing: border-box !important;
  
  /* 定位重置 */
  position: relative !important;
  left: auto !important;
  right: auto !important;
  top: auto !important;
  bottom: auto !important;
  
  /* 过渡动画 */
  transition: all 0.3s ease !important;
}

/* 折叠状态下的子菜单图标 - 绝对精确居中（与菜单项保持一致） */
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title .el-icon) {
  /* 精确图标尺寸 - 与普通菜单项保持一致 */
  font-size: 18px !important;
  width: 18px !important;
  height: 18px !important;
  
  /* 绝对居中定位 - 与菜单项图标保持一致 */
  position: absolute !important;
  left: 50% !important;
  top: 50% !important;
  transform: translate(-50%, -50%) !important;
  
  /* 完全清除边距 */
  margin: 0 !important;
  padding: 0 !important;
  border: none !important;
  outline: none !important;
  
  /* 图标内容居中 */
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  text-align: center !important;
  
  /* 行高和垂直对齐 */
  line-height: 1 !important;
  vertical-align: middle !important;
  
  /* 字体渲染优化 */
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
  
  /* 确保图标不会被拉伸 */
  flex-shrink: 0 !important;
  flex-grow: 0 !important;
}

/* 隐藏折叠状态下的子菜单文字和箭头 */
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title span),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title .el-sub-menu__icon-arrow) {
  display: none !important;
  opacity: 0 !important;
  width: 0 !important;
  height: 0 !important;
  overflow: hidden !important;
}

/* 折叠状态下的悬停效果 - 统一标准 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item:hover),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title:hover) {
  background-color: #f0f2f5 !important;
  transform: scale(1.05) !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

/* 折叠状态下的激活状态 - 统一标准 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item.is-active),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu.is-active .el-sub-menu__title) {
  background-color: #409eff !important;
  color: white !important;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.4) !important;
}

.sidebar-collapsed .sidebar-menu :deep(.el-menu-item.is-active .el-icon),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu.is-active .el-sub-menu__title .el-icon) {
  color: white !important;
}

/* 折叠状态下的子菜单弹出层隐藏 */
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu .el-menu) {
  display: none !important;
}

/* 折叠状态下的工具提示支持 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title) {
  cursor: pointer !important;
  position: relative !important;
}

/* 确保折叠状态下的图标在所有浏览器中都居中 */
.sidebar-collapsed .sidebar-menu :deep(.el-menu-item),
.sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title) {
  /* Flexbox 居中 */
  display: -webkit-box !important;
  display: -ms-flexbox !important;
  display: flex !important;
  -webkit-box-pack: center !important;
  -ms-flex-pack: center !important;
  justify-content: center !important;
  -webkit-box-align: center !important;
  -ms-flex-align: center !important;
  align-items: center !important;
  
  /* Grid 居中备选方案 */
  place-items: center !important;
  place-content: center !important;
}

/* 特殊情况处理：确保图标在不同设备上的一致性 */
@media (max-width: 1024px) {
  .sidebar-collapsed .sidebar-menu :deep(.el-menu-item),
  .sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title) {
    width: 44px !important;
    height: 44px !important;
  }
  
  .sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-icon),
  .sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title .el-icon) {
    font-size: 18px !important;
    width: 18px !important;
    height: 18px !important;
  }
}

/* 高分辨率屏幕优化 */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 192dpi) {
  .sidebar-collapsed .sidebar-menu :deep(.el-menu-item .el-icon),
  .sidebar-collapsed .sidebar-menu :deep(.el-sub-menu__title .el-icon) {
    -webkit-font-smoothing: antialiased !important;
    -moz-osx-font-smoothing: grayscale !important;
  }
}

/* 主要内容区域 */
.app-main {
  background-color: #f5f7fa;
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