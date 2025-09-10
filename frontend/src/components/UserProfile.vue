<template>
  <el-dialog
    v-model="visible"
    title="个人信息"
    width="500px"
    :before-close="handleClose"
  >
    <el-tabs v-model="activeTab" type="border-card">
      <!-- 个人信息标签页 -->
      <el-tab-pane label="个人信息" name="profile">
        <el-form
          ref="profileForm"
          :model="profileForm"
          :rules="profileRules"
          label-width="80px"
        >
          <el-form-item label="用户名">
            <el-input v-model="currentUser.username" disabled />
          </el-form-item>
          
          <el-form-item label="角色">
            <el-tag :type="getRoleType(currentUser.role)">
              {{ getRoleText(currentUser.role) }}
            </el-tag>
          </el-form-item>
          
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="profileForm.email"
              placeholder="请输入邮箱地址"
              type="email"
            />
          </el-form-item>
          
          <el-form-item label="主题" prop="theme">
            <el-radio-group v-model="profileForm.theme">
              <el-radio label="light">明亮主题</el-radio>
              <el-radio label="dark">暗黑主题</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>
        
        <div class="dialog-footer">
          <el-button @click="handleClose">取消</el-button>
          <el-button
            type="primary"
            :loading="profileLoading"
            @click="handleUpdateProfile"
          >
            保存
          </el-button>
        </div>
      </el-tab-pane>
      
      <!-- 修改密码标签页 -->
      <el-tab-pane label="修改密码" name="password">
        <el-form
          ref="passwordForm"
          :model="passwordForm"
          :rules="passwordRules"
          label-width="80px"
        >
          <el-form-item label="旧密码" prop="oldPassword">
            <el-input
              v-model="passwordForm.oldPassword"
              type="password"
              placeholder="请输入当前密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="新密码" prop="newPassword">
            <el-input
              v-model="passwordForm.newPassword"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>
          
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="passwordForm.confirmPassword"
              type="password"
              placeholder="请再次输入新密码"
              show-password
            />
          </el-form-item>
          
          <el-alert
            title="密码要求"
            type="info"
            :closable="false"
            show-icon
          >
            <ul style="margin: 0; padding-left: 20px;">
              <li>长度至少8位</li>
              <li>包含至少一个大写字母</li>
              <li>包含至少一个小写字母</li>
              <li>包含至少一个数字</li>
            </ul>
          </el-alert>
        </el-form>
        
        <div class="dialog-footer">
          <el-button @click="resetPasswordForm">重置</el-button>
          <el-button
            type="primary"
            :loading="passwordLoading"
            @click="handleChangePassword"
          >
            修改密码
          </el-button>
        </div>
      </el-tab-pane>
    </el-tabs>
  </el-dialog>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

export default {
  name: 'UserProfile',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      activeTab: 'profile',
      profileLoading: false,
      passwordLoading: false,
      
      profileForm: {
        email: '',
        theme: 'light'
      },
      
      passwordForm: {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      
      profileRules: {
        email: [
          { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
        ]
      },
      
      passwordRules: {
        oldPassword: [
          { required: true, message: '请输入当前密码', trigger: 'blur' }
        ],
        newPassword: [
          { required: true, message: '请输入新密码', trigger: 'blur' },
          { min: 8, message: '密码长度至少8位', trigger: 'blur' },
          { validator: this.validatePassword, trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请确认新密码', trigger: 'blur' },
          { validator: this.validateConfirmPassword, trigger: 'blur' }
        ]
      }
    }
  },
  
  computed: {
    ...mapGetters('auth', ['currentUser']),
    
    visible: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  
  watch: {
    visible(newVal) {
      if (newVal) {
        this.initForms()
      }
    }
  },
  
  methods: {
    ...mapActions('auth', ['updateProfile', 'changePassword']),
    
    initForms() {
      // 初始化个人信息表单
      this.profileForm = {
        email: this.currentUser.email || '',
        theme: this.currentUser.theme || 'light'
      }
      
      // 重置密码表单
      this.resetPasswordForm()
    },
    
    resetPasswordForm() {
      this.passwordForm = {
        oldPassword: '',
        newPassword: '',
        confirmPassword: ''
      }
      
      // 清除表单验证
      this.$nextTick(() => {
        if (this.$refs.passwordForm) {
          this.$refs.passwordForm.clearValidate()
        }
      })
    },
    
    validatePassword(rule, value, callback) {
      if (!value) {
        callback(new Error('请输入新密码'))
        return
      }
      
      // 检查密码强度
      const hasUpper = /[A-Z]/.test(value)
      const hasLower = /[a-z]/.test(value)
      const hasNumber = /\d/.test(value)
      
      if (!hasUpper) {
        callback(new Error('密码必须包含至少一个大写字母'))
        return
      }
      
      if (!hasLower) {
        callback(new Error('密码必须包含至少一个小写字母'))
        return
      }
      
      if (!hasNumber) {
        callback(new Error('密码必须包含至少一个数字'))
        return
      }
      
      callback()
    },
    
    validateConfirmPassword(rule, value, callback) {
      if (!value) {
        callback(new Error('请确认新密码'))
        return
      }
      
      if (value !== this.passwordForm.newPassword) {
        callback(new Error('两次输入的密码不一致'))
        return
      }
      
      callback()
    },
    
    async handleUpdateProfile() {
      try {
        const valid = await this.$refs.profileForm.validate()
        if (!valid) return
        
        this.profileLoading = true
        
        await this.updateProfile(this.profileForm)
        
        this.$message.success('个人信息更新成功')
        
        // 如果主题发生变化，应用新主题
        if (this.profileForm.theme !== this.currentUser.theme) {
          this.$store.dispatch('theme/setTheme', this.profileForm.theme)
        }
        
      } catch (error) {
        console.error('Update profile error:', error)
        this.$message.error(error.response?.data?.detail || '更新个人信息失败')
      } finally {
        this.profileLoading = false
      }
    },
    
    async handleChangePassword() {
      try {
        const valid = await this.$refs.passwordForm.validate()
        if (!valid) return
        
        this.passwordLoading = true
        
        await this.changePassword({
          old_password: this.passwordForm.oldPassword,
          new_password: this.passwordForm.newPassword
        })
        
        this.$message.success('密码修改成功')
        this.resetPasswordForm()
        this.activeTab = 'profile'
        
      } catch (error) {
        console.error('Change password error:', error)
        this.$message.error(error.response?.data?.detail || '密码修改失败')
      } finally {
        this.passwordLoading = false
      }
    },
    
    handleClose() {
      this.visible = false
      this.activeTab = 'profile'
      this.resetPasswordForm()
    },
    
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
        admin: '超级管理员',
        manager: '管理员',
        user: '普通用户'
      }
      return roleTexts[role] || '未知角色'
    }
  }
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-lg);
  border-top: 1px solid var(--border-tertiary);
}

:deep(.el-tabs__content) {
  padding: var(--spacing-lg) 0;
}

:deep(.el-alert ul) {
  margin: 0;
  padding-left: var(--spacing-lg);
}

/* 使用新的主题系统变量 - 所有样式都会自动适配主题 */
:deep(.el-form-item__label) {
  color: var(--text-primary) !important;
  font-weight: 500 !important;
  opacity: 1 !important;
  visibility: visible !important;
}

:deep(.el-dialog__body) {
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
}

:deep(.el-tabs__content) {
  color: var(--text-primary) !important;
}

:deep(.el-form-item) {
  color: var(--text-primary) !important;
}

:deep(.el-input__wrapper) {
  background-color: var(--bg-primary) !important;
  border-color: var(--border-primary) !important;
}

:deep(.el-input__inner) {
  color: var(--text-primary) !important;
  background-color: transparent !important;
}

:deep(.el-radio__label) {
  color: var(--text-secondary) !important;
}

:deep(.el-tag) {
  background-color: var(--fill-primary) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-secondary) !important;
}

:deep(.el-tag.el-tag--danger) {
  background-color: var(--danger) !important;
  border-color: var(--danger) !important;
  color: var(--text-inverse) !important;
}

:deep(.el-tag.el-tag--warning) {
  background-color: var(--warning) !important;
  border-color: var(--warning) !important;
  color: var(--text-inverse) !important;
}

:deep(.el-tag.el-tag--info) {
  background-color: var(--info) !important;
  border-color: var(--info) !important;
  color: var(--text-inverse) !important;
}
</style>