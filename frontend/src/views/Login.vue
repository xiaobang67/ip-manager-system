<template>
  <div class="login-container">
    <!-- 主题切换按钮 -->
    <div class="theme-toggle-wrapper">
      <ThemeToggle />
    </div>
    
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>网络资源管理系统</h2>
          <p>请登录您的账户</p>
        </div>
      </template>
      
      <el-form
        ref="loginForm"
        :model="loginData"
        :rules="rules"
        label-width="0"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginData.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginData.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="login-button"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import { mapActions } from 'vuex'
import ThemeToggle from '@/components/ThemeToggle.vue'

export default {
  name: 'Login',
  components: {
    ThemeToggle
  },
  data() {
    return {
      loginData: {
        username: '',
        password: ''
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' }
        ]
      }
    }
  },
  computed: {
    loading() {
      return this.$store.getters['auth/loginLoading']
    }
  },
  methods: {
    ...mapActions('auth', ['login']),
    
    async handleLogin() {
      try {
        const valid = await this.$refs.loginForm.validate()
        if (!valid) return
        
        const result = await this.login(this.loginData)
        
        if (result.success) {
          this.$message.success('登录成功')
          // 跳转到之前访问的页面或默认页面
          const redirect = this.$route.query.redirect || '/dashboard'
          this.$router.push(redirect)
        } else {
          this.$message.error(result.message)
        }
      } catch (error) {
        console.error('Login error:', error)
        this.$message.error('登录失败，请重试')
      }
    }
  },
  
  // 如果已经登录，直接跳转到仪表盘
  created() {
    if (this.$store.getters['auth/isAuthenticated']) {
      this.$router.push('/dashboard')
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-dark) 100%);
  position: relative;
}

.theme-toggle-wrapper {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 10;
}

.login-card {
  width: 400px;
  box-shadow: var(--box-shadow-light);
  background-color: var(--bg-color);
  border-color: var(--border-color);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 8px 0;
  color: var(--text-color-primary);
}

.card-header p {
  margin: 0;
  color: var(--text-color-secondary);
  font-size: 14px;
}

.login-form {
  padding: 0 20px 20px;
}

.login-button {
  width: 100%;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    width: 90%;
    margin: 0 20px;
  }
  
  .theme-toggle-wrapper {
    top: 16px;
    right: 16px;
  }
}
</style>