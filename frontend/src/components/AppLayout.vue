<template>
  <div class="app-layout">
    <!-- 顶部导航栏 -->
    <el-header class="app-header">
      <div class="header-left">
        <h1 class="app-title">IP地址管理系统</h1>
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
    
    <!-- 主要内容区域 -->
    <el-main class="app-main">
      <slot />
    </el-main>
    
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
      showUserProfile: false
    }
  },
  computed: {
    ...mapGetters('auth', ['isAuthenticated', 'userName'])
  },
  methods: {
    ...mapActions('auth', ['logout']),
    
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
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  box-shadow: var(--box-shadow-base);
}

.header-left {
  display: flex;
  align-items: center;
}

.app-title {
  color: var(--text-color-primary);
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
  color: var(--text-color-primary) !important;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-menu-button:hover {
  color: var(--primary-color) !important;
}

.app-main {
  flex: 1;
  background-color: var(--bg-color-page);
  padding: 20px;
}

/* 响应式设计 */
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
}
</style>