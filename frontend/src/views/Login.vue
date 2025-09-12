<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>欧税通网络资源管理平台</h2>
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
          <el-checkbox v-model="rememberPassword" class="remember-checkbox">
            记住密码
          </el-checkbox>
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

export default {
  name: 'Login',
  data() {
    return {
      loginData: {
        username: '',
        password: ''
      },
      rememberPassword: false,
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
    
    // 保存登录凭据到本地存储
    saveCredentials() {
      if (this.rememberPassword) {
        const credentials = {
          username: this.loginData.username,
          password: this.loginData.password,
          remember: true
        }
        localStorage.setItem('loginCredentials', JSON.stringify(credentials))
      } else {
        localStorage.removeItem('loginCredentials')
      }
    },
    
    // 从本地存储加载登录凭据
    loadCredentials() {
      try {
        const saved = localStorage.getItem('loginCredentials')
        if (saved) {
          const credentials = JSON.parse(saved)
          if (credentials.remember) {
            this.loginData.username = credentials.username || ''
            this.loginData.password = credentials.password || ''
            this.rememberPassword = true
          }
        }
      } catch (error) {
        console.error('Failed to load saved credentials:', error)
        localStorage.removeItem('loginCredentials')
      }
    },
    
    async handleLogin() {
      try {
        const valid = await this.$refs.loginForm.validate()
        if (!valid) return
        
        const result = await this.login(this.loginData)
        
        if (result.success) {
          // 保存凭据（如果用户选择记住密码）
          this.saveCredentials()
          
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
    } else {
      // 加载保存的登录凭据
      this.loadCredentials()
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
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  position: relative;
}

.login-card {
  width: 400px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  background-color: #ffffff;
  border-color: #dcdfe6;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 8px 0;
  color: #303133;
}

.card-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.login-form {
  padding: 0 20px 20px;
}

.login-button {
  width: 100%;
}

.remember-checkbox {
  width: 100%;
  margin-bottom: 10px;
}

.remember-checkbox :deep(.el-checkbox__label) {
  color: #606266;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    width: 90%;
    margin: 0 20px;
  }
}
</style>