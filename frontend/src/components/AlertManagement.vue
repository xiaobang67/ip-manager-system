<template>
  <div class="alert-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>警报规则管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建规则
          </el-button>
        </div>
      </template>

      <!-- 筛选器 -->
      <div class="filters">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-select v-model="filters.rule_type" placeholder="规则类型" clearable @change="loadAlertRules">
              <el-option label="使用率" value="utilization"></el-option>
              <el-option label="冲突" value="conflict"></el-option>
              <el-option label="过期" value="expiry"></el-option>
            </el-select>
          </el-col>
          <el-col :span="6">
            <el-select v-model="filters.is_active" placeholder="状态" clearable @change="loadAlertRules">
              <el-option label="启用" :value="true"></el-option>
              <el-option label="禁用" :value="false"></el-option>
            </el-select>
          </el-col>
          <el-col :span="12">
            <el-button @click="resetFilters">重置</el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 警报规则表格 -->
      <el-table :data="alertRules" v-loading="loading" style="width: 100%">
        <el-table-column prop="name" label="规则名称" show-overflow-tooltip></el-table-column>
        <el-table-column prop="rule_type" label="类型" width="100">
          <template #default="scope">
            <el-tag :type="getRuleTypeColor(scope.row.rule_type)">
              {{ getRuleTypeText(scope.row.rule_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="threshold_value" label="阈值" width="100">
          <template #default="scope">
            {{ scope.row.threshold_value ? `${scope.row.threshold_value}%` : 'N/A' }}
          </template>
        </el-table-column>
        <el-table-column prop="subnet_id" label="网段" width="150">
          <template #default="scope">
            {{ getSubnetName(scope.row.subnet_id) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="toggleRuleStatus(scope.row)"
            ></el-switch>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="editRule(scope.row)">
              编辑
            </el-button>
            <el-button type="text" size="small" @click="deleteRule(scope.row)" class="danger">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadAlertRules"
          @current-change="loadAlertRules"
        />
      </div>
    </el-card>

    <!-- 创建/编辑规则对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingRule ? '编辑警报规则' : '创建警报规则'"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="ruleForm" :rules="rules" ref="formRef" label-width="120px">
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称"></el-input>
        </el-form-item>

        <el-form-item label="规则类型" prop="rule_type">
          <el-select v-model="ruleForm.rule_type" placeholder="请选择规则类型" style="width: 100%">
            <el-option label="使用率警报" value="utilization"></el-option>
            <el-option label="冲突警报" value="conflict"></el-option>
            <el-option label="过期警报" value="expiry"></el-option>
          </el-select>
        </el-form-item>

        <el-form-item 
          v-if="ruleForm.rule_type === 'utilization'" 
          label="使用率阈值" 
          prop="threshold_value"
        >
          <el-input-number
            v-model="ruleForm.threshold_value"
            :min="1"
            :max="100"
            :precision="2"
            style="width: 100%"
          >
            <template #append>%</template>
          </el-input-number>
        </el-form-item>

        <el-form-item label="目标网段">
          <el-select
            v-model="ruleForm.subnet_id"
            placeholder="选择网段（留空表示全局规则）"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="subnet in availableSubnets"
              :key="subnet.id"
              :label="`${subnet.network} - ${subnet.description || 'N/A'}`"
              :value="subnet.id"
            ></el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="通知邮箱">
          <el-input
            v-model="emailInput"
            placeholder="输入邮箱地址，按回车添加"
            @keyup.enter="addEmail"
          >
            <template #append>
              <el-button @click="addEmail">添加</el-button>
            </template>
          </el-input>
          <div class="email-tags" v-if="emailList.length > 0">
            <el-tag
              v-for="(email, index) in emailList"
              :key="index"
              closable
              @close="removeEmail(index)"
              style="margin: 5px 5px 0 0"
            >
              {{ email }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="saveRule" :loading="saving">
            {{ saving ? '保存中...' : '保存' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getAlertRules,
  createAlertRule,
  updateAlertRule,
  deleteAlertRule
} from '@/api/monitoring'
import { getSubnets } from '@/api/subnet'

export default {
  name: 'AlertManagement',
  setup() {
    const loading = ref(false)
    const saving = ref(false)
    const showCreateDialog = ref(false)
    const editingRule = ref(null)
    const formRef = ref(null)
    const emailInput = ref('')
    
    const alertRules = ref([])
    const availableSubnets = ref([])
    const emailList = ref([])

    const filters = reactive({
      rule_type: '',
      is_active: null
    })

    const pagination = reactive({
      page: 1,
      size: 20,
      total: 0
    })

    const ruleForm = reactive({
      name: '',
      rule_type: 'utilization',
      threshold_value: 80,
      subnet_id: null,
      notification_emails: ''
    })

    const rules = {
      name: [
        { required: true, message: '请输入规则名称', trigger: 'blur' }
      ],
      rule_type: [
        { required: true, message: '请选择规则类型', trigger: 'change' }
      ],
      threshold_value: [
        { required: true, message: '请输入阈值', trigger: 'blur' },
        { type: 'number', min: 1, max: 100, message: '阈值必须在1-100之间', trigger: 'blur' }
      ]
    }

    // 加载警报规则
    const loadAlertRules = async () => {
      loading.value = true
      try {
        const params = {
          skip: (pagination.page - 1) * pagination.size,
          limit: pagination.size,
          ...filters
        }
        
        const response = await getAlertRules(params)
        alertRules.value = response.data
        // 注意：这里假设API返回了总数，实际可能需要调整
        pagination.total = response.total || response.data.length
      } catch (error) {
        ElMessage.error('加载警报规则失败')
        console.error('Load alert rules error:', error)
      } finally {
        loading.value = false
      }
    }

    // 加载可用网段
    const loadAvailableSubnets = async () => {
      try {
        const response = await getSubnets()
        availableSubnets.value = response.data.items || response.data
      } catch (error) {
        console.error('Load subnets error:', error)
      }
    }

    // 获取规则类型颜色
    const getRuleTypeColor = (type) => {
      const colors = {
        'utilization': 'primary',
        'conflict': 'danger',
        'expiry': 'warning'
      }
      return colors[type] || 'info'
    }

    // 获取规则类型文本
    const getRuleTypeText = (type) => {
      const texts = {
        'utilization': '使用率',
        'conflict': '冲突',
        'expiry': '过期'
      }
      return texts[type] || type
    }

    // 获取网段名称
    const getSubnetName = (subnetId) => {
      if (!subnetId) return '全局'
      const subnet = availableSubnets.value.find(s => s.id === subnetId)
      return subnet ? subnet.network : `网段 ${subnetId}`
    }

    // 格式化日期时间
    const formatDateTime = (dateTime) => {
      return new Date(dateTime).toLocaleString()
    }

    // 切换规则状态
    const toggleRuleStatus = async (rule) => {
      try {
        await updateAlertRule(rule.id, { is_active: rule.is_active })
        ElMessage.success('规则状态已更新')
      } catch (error) {
        ElMessage.error('更新规则状态失败')
        // 恢复原状态
        rule.is_active = !rule.is_active
        console.error('Toggle rule status error:', error)
      }
    }

    // 编辑规则
    const editRule = (rule) => {
      editingRule.value = rule
      Object.assign(ruleForm, {
        name: rule.name,
        rule_type: rule.rule_type,
        threshold_value: rule.threshold_value,
        subnet_id: rule.subnet_id,
        notification_emails: rule.notification_emails
      })

      // 解析邮箱列表
      if (rule.notification_emails) {
        try {
          emailList.value = JSON.parse(rule.notification_emails)
        } catch (error) {
          emailList.value = []
        }
      } else {
        emailList.value = []
      }

      showCreateDialog.value = true
    }

    // 删除规则
    const deleteRule = async (rule) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除警报规则 "${rule.name}" 吗？`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await deleteAlertRule(rule.id)
        ElMessage.success('警报规则已删除')
        loadAlertRules()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除警报规则失败')
          console.error('Delete rule error:', error)
        }
      }
    }

    // 添加邮箱
    const addEmail = () => {
      const email = emailInput.value.trim()
      if (!email) return

      // 简单的邮箱验证
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!emailRegex.test(email)) {
        ElMessage.error('请输入有效的邮箱地址')
        return
      }

      if (emailList.value.includes(email)) {
        ElMessage.error('邮箱已存在')
        return
      }

      emailList.value.push(email)
      emailInput.value = ''
    }

    // 移除邮箱
    const removeEmail = (index) => {
      emailList.value.splice(index, 1)
    }

    // 保存规则
    const saveRule = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        
        saving.value = true

        const ruleData = {
          ...ruleForm,
          notification_emails: emailList.value.length > 0 ? JSON.stringify(emailList.value) : null
        }

        if (editingRule.value) {
          await updateAlertRule(editingRule.value.id, ruleData)
          ElMessage.success('警报规则已更新')
        } else {
          await createAlertRule(ruleData)
          ElMessage.success('警报规则已创建')
        }

        showCreateDialog.value = false
        loadAlertRules()
      } catch (error) {
        ElMessage.error('保存警报规则失败')
        console.error('Save rule error:', error)
      } finally {
        saving.value = false
      }
    }

    // 重置表单
    const resetForm = () => {
      if (formRef.value) {
        formRef.value.resetFields()
      }
      Object.assign(ruleForm, {
        name: '',
        rule_type: 'utilization',
        threshold_value: 80,
        subnet_id: null,
        notification_emails: ''
      })
      emailList.value = []
      emailInput.value = ''
      editingRule.value = null
    }

    // 重置筛选器
    const resetFilters = () => {
      Object.assign(filters, {
        rule_type: '',
        is_active: null
      })
      pagination.page = 1
      loadAlertRules()
    }

    onMounted(() => {
      loadAlertRules()
      loadAvailableSubnets()
    })

    return {
      loading,
      saving,
      showCreateDialog,
      editingRule,
      formRef,
      emailInput,
      alertRules,
      availableSubnets,
      emailList,
      filters,
      pagination,
      ruleForm,
      rules,
      loadAlertRules,
      getRuleTypeColor,
      getRuleTypeText,
      getSubnetName,
      formatDateTime,
      toggleRuleStatus,
      editRule,
      deleteRule,
      addEmail,
      removeEmail,
      saveRule,
      resetForm,
      resetFilters,
      Plus
    }
  }
}
</script>

<style scoped>
.alert-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.email-tags {
  margin-top: 10px;
}

.danger {
  color: #f56c6c;
}

.danger:hover {
  color: #f78989;
}
</style>