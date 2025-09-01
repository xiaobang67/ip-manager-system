<template>
  <div class="layout-container">
    <el-container style="height: 100vh;">
      <!-- 侧边栏 -->
      <el-aside 
        :width="sidebarCollapsed ? '64px' : '220px'" 
        class="sidebar"
        :class="{ 'sidebar-collapsed': sidebarCollapsed }"
      >
        <div class="logo-container">
          <div class="logo" :class="{ 'logo-collapsed': sidebarCollapsed }">
            <el-icon><Monitor /></el-icon>
            <span v-show="!sidebarCollapsed" class="logo-text">IP管理系统</span>
          </div>
        </div>
        
        <el-menu
          :default-active="activeMenuPath"
          class="sidebar-menu"
          mode="vertical"
          :collapse="sidebarCollapsed"
          :collapse-transition="false"
          router
        >
          <el-menu-item index="/dashboard">
            <el-icon><Odometer /></el-icon>
            <template #title>仪表盘</template>
          </el-menu-item>
          
          <el-sub-menu index="ip-management">
            <template #title>
              <el-icon><Monitor /></el-icon>
              <span>IP管理</span>
            </template>
            <el-menu-item index="/ip-management/addresses">
              <el-icon><Location /></el-icon>
              <template #title>IP地址管理</template>
            </el-menu-item>
            <el-menu-item index="/ip-management/segments">
              <el-icon><Connection /></el-icon>
              <template #title>网段管理</template>
            </el-menu-item>
            <el-menu-item index="/ip-management/reserved">
              <el-icon><Lock /></el-icon>
              <template #title>地址保留</template>
            </el-menu-item>
          </el-sub-menu>
          
          <el-sub-menu index="organization">
            <template #title>
              <el-icon><OfficeBuilding /></el-icon>
              <span>组织管理</span>
            </template>
            <el-menu-item index="/organization/departments">
              <el-icon><OfficeBuilding /></el-icon>
              <template #title>部门管理</template>
            </el-menu-item>
            <el-menu-item index="/organization/users">
              <el-icon><User /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
          </el-sub-menu>
          
          <!-- 系统管理菜单（仅管理员可见） -->
          <el-sub-menu v-if="authStore.isAdmin" index="system">
            <template #title>
              <el-icon><Setting /></el-icon>
              <span>系统管理</span>
            </template>
            <el-menu-item index="/system/users">
              <el-icon><User /></el-icon>
              <template #title>用户管理</template>
            </el-menu-item>
            <el-menu-item index="/system/groups">
              <el-icon><UserFilled /></el-icon>
              <template #title>组管理</template>
            </el-menu-item>
            <el-menu-item v-if="authStore.isSuperuser" index="/system/settings">
              <el-icon><Tools /></el-icon>
              <template #title>系统设置</template>
            </el-menu-item>
          </el-sub-menu>
          
          <el-menu-item index="/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <template #title>统计报表</template>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主要内容区域 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <el-button 
              text 
              @click="toggleSidebar"
              class="collapse-btn"
            >
              <el-icon size="18">
                <component :is="sidebarCollapsed ? 'Expand' : 'Fold'" />
              </el-icon>
            </el-button>
            
            <el-breadcrumb separator="/" class="breadcrumb">
              <el-breadcrumb-item 
                v-for="breadcrumb in breadcrumbs" 
                :key="breadcrumb.path"
                :to="breadcrumb.path"
              >
                {{ breadcrumb.title }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-button text>
              <el-icon><Bell /></el-icon>
            </el-button>
            <el-dropdown @command="handleUserMenuCommand">
              <span class="user-dropdown">
                <el-avatar size="small">{{ userAvatar }}</el-avatar>
                <span class="username">{{ authStore.userDisplayName }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">
                    <el-icon><User /></el-icon>
                    个人设置
                  </el-dropdown-item>
                  <el-dropdown-item command="changePassword">
                    <el-icon><Lock /></el-icon>
                    修改密码
                  </el-dropdown-item>
                  <el-dropdown-item divided command="logout">
                    <el-icon><SwitchButton /></el-icon>
                    退出登录
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>
        
        <!-- 主要内容 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import {
  Monitor,
  Odometer,
  Location,
  Connection,
  Lock,
  OfficeBuilding,
  User,
  UserFilled,
  DataAnalysis,
  Setting,
  Tools,
  Fold,
  Expand,
  Bell,
  ArrowDown,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const authStore = useAuthStore()
const sidebarCollapsed = ref(false)

// 计算当前激活的菜单路径
const activeMenuPath = computed(() => {
  return route.path
})

// 计算用户头像显示字母
const userAvatar = computed(() => {
  const user = authStore.user
  if (!user) return 'U'
  return (user.display_name || user.real_name || user.username).charAt(0).toUpperCase()
})

// 处理用户菜单命令
const handleUserMenuCommand = async (command: string) => {
  switch (command) {
    case 'profile':
      ElMessage.info('个人设置功能开发中...')
      break
    case 'changePassword':
      showChangePasswordDialog()
      break
    case 'logout':
      await handleLogout()
      break
  }
}

// 显示修改密码对话框
const showChangePasswordDialog = () => {
  ElMessage.info('修改密码功能开发中...')
}

// 处理登出
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认登出',
      { type: 'warning' }
    )
    
    await authStore.logout()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('登出失败:', error)
    }
  }
}

// 生成面包屑导航
const breadcrumbs = computed(() => {
  const pathArray = route.path.split('/').filter(path => path)
  const breadcrumbItems = []
  
  let currentPath = ''
  pathArray.forEach((path, index) => {
    currentPath += '/' + path
    let title = path
    
    // 根据路径设置标题
    switch (currentPath) {
      case '/dashboard':
        title = '仪表盘'
        break
      case '/ip-management':
        title = 'IP管理'
        break
      case '/ip-management/addresses':
        title = 'IP地址管理'
        break
      case '/ip-management/segments':
        title = '网段管理'
        break
      case '/ip-management/reserved':
        title = '地址保留'
        break
      case '/organization':
        title = '组织管理'
        break
      case '/organization/departments':
        title = '部门管理'
        break
      case '/organization/users':
        title = '用户管理'
        break
      case '/system':
        title = '系统管理'
        break
      case '/system/users':
        title = '用户管理'
        break
      case '/system/groups':
        title = '组管理'
        break
      case '/system/settings':
        title = '系统设置'
        break
      case '/statistics':
        title = '统计报表'
        break
    }
    
    breadcrumbItems.push({
      title,
      path: currentPath
    })
  })
  
  return breadcrumbItems
})

// 切换侧边栏折叠状态
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 检测设备尺寸
const checkDevice = () => {
  if (window.innerWidth <= 768) {
    sidebarCollapsed.value = true
  }
}

// 组件挂载时初始化
onMounted(async () => {
  // 检测设备
  checkDevice()
  
  // 初始化认证状态
  await authStore.initAuth()
})

// 监听窗口大小变化
window.addEventListener('resize', checkDevice)
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.sidebar {
  min-height: 100vh;
  background-color: #304156;
  box-shadow: 2px 0 6px rgba(0, 21, 41, 0.35);
  transition: width 0.28s;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3344;
}

.logo {
  display: flex;
  align-items: center;
  color: #ffffff;
  font-size: 18px;
  font-weight: bold;
  transition: all 0.3s;
}

.logo-collapsed {
  justify-content: center;
}

.logo-text {
  margin-left: 10px;
  transition: all 0.3s;
}

.sidebar-menu {
  border: none;
  background-color: #304156;
  width: 100%;
}

.sidebar-menu .el-menu-item {
  color: #bfcbd9;
  background-color: #304156 !important;
}

.sidebar-menu .el-menu-item:hover {
  background-color: #263445 !important;
  color: #ffffff;
}

.sidebar-menu .el-menu-item.is-active {
  color: #409eff !important;
  background-color: #001529 !important;
}

.sidebar-menu .el-sub-menu__title {
  color: #bfcbd9;
  background-color: #304156 !important;
}

.sidebar-menu .el-sub-menu__title:hover {
  background-color: #263445 !important;
  color: #ffffff;
}

.header {
  background-color: #ffffff;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  margin-right: 20px;
  color: #5a5e66;
}

.breadcrumb {
  font-size: 14px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #303133;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
  overflow: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 64px !important;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .header {
    padding: 0 10px;
  }
  
  .main-content {
    padding: 10px;
  }
}
</style>