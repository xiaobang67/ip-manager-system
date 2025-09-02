<template>
  <el-dialog
    :model-value="visible"
    :title="dialogTitle"
    width="600px"
    @update:model-value="$emit('update:visible', $event)"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      @submit.prevent
    >
      <el-form-item label="网段" prop="network">
        <el-input
          v-model="form.network"
          placeholder="请输入CIDR格式，如 192.168.1.0/24"
          @blur="validateNetwork"
        />
        <div v-if="networkValidation.message" :class="networkValidation.isValid ? 'validation-success' : 'validation-error'">
          {{ networkValidation.message }}
        </div>
      </el-form-item>

      <el-form-item label="子网掩码" prop="netmask">
        <el-input
          v-model="form.netmask"
          placeholder="请输入子网掩码，如 255.255.255.0"
        />
      </el-form-item>

      <el-form-item label="网关" prop="gateway">
        <el-input
          v-model="form.gateway"
          placeholder="请输入网关地址（可选）"
        />
      </el-form-item>

      <el-form-item label="VLAN ID" prop="vlan_id">
        <el-input-number
          v-model="form.vlan_id"
          :min="1"
          :max="4094"
          placeholder="请输入VLAN ID（可选）"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="位置" prop="location">
        <el-input
          v-model="form.location"
          placeholder="请输入位置信息（可选）"
        />
      </el-form-item>

      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="请输入网段描述（可选）"
        />
      </el-form-item>

      <!-- 重叠网段警告 -->
      <el-alert
        v-if="networkValidation.overlapping_subnets && networkValidation.overlapping_subnets.length > 0"
        title="网段重叠警告"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <p>检测到与以下网段重叠：</p>
          <ul>
            <li v-for="subnet in networkValidation.overlapping_subnets" :key="subnet.id">
              {{ subnet.network }} - {{ subnet.description || '无描述' }}
            </li>
          </ul>
        </template>
      </el-alert>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!networkValidation.isValid"
          @click="handleSubmit"
        >
          {{ mode === 'create' ? '创建' : '更新' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { subnetApi } from '@/api/subnet'
import { debounce } from '@/utils/debounce'

export default {
  name: 'SubnetDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    subnet: {
      type: Object,
      default: null
    },
    mode: {
      type: String,
      default: 'create' // 'create' | 'edit'
    }
  },
  emits: ['update:visible', 'success'],
  setup(props, { emit }) {
    const formRef = ref()
    const submitting = ref(false)
    
    // 表单数据
    const form = reactive({
      network: '',
      netmask: '',
      gateway: '',
      vlan_id: null,
      location: '',
      description: ''
    })

    // 网段验证状态
    const networkValidation = reactive({
      isValid: false,
      message: '',
      overlapping_subnets: []
    })

    // 表单验证规则
    const rules = {
      network: [
        { required: true, message: '请输入网段', trigger: 'blur' },
        {
          pattern: /^(\d{1,3}\.){3}\d{1,3}\/\d{1,2}$/,
          message: '请输入正确的CIDR格式',
          trigger: 'blur'
        }
      ],
      netmask: [
        { required: true, message: '请输入子网掩码', trigger: 'blur' },
        {
          pattern: /^(\d{1,3}\.){3}\d{1,3}$/,
          message: '请输入正确的子网掩码格式',
          trigger: 'blur'
        }
      ],
      gateway: [
        {
          pattern: /^(\d{1,3}\.){3}\d{1,3}$/,
          message: '请输入正确的IP地址格式',
          trigger: 'blur'
        }
      ],
      vlan_id: [
        {
          type: 'number',
          min: 1,
          max: 4094,
          message: 'VLAN ID必须在1-4094范围内',
          trigger: 'blur'
        }
      ]
    }

    // 计算属性
    const dialogTitle = computed(() => {
      return props.mode === 'create' ? '创建网段' : '编辑网段'
    })

    // 网段验证（防抖）
    const validateNetwork = debounce(async () => {
      if (!form.network) {
        networkValidation.isValid = false
        networkValidation.message = ''
        networkValidation.overlapping_subnets = []
        return
      }

      try {
        const response = await subnetApi.validateSubnet({
          network: form.network,
          exclude_id: props.mode === 'edit' ? props.subnet?.id : null
        })

        networkValidation.isValid = response.data.is_valid
        networkValidation.message = response.data.message
        networkValidation.overlapping_subnets = response.data.overlapping_subnets || []
      } catch (error) {
        networkValidation.isValid = false
        networkValidation.message = '网段验证失败'
        networkValidation.overlapping_subnets = []
      }
    }, 500)

    // 初始化表单
    const initForm = () => {
      if (props.subnet && props.mode === 'edit') {
        Object.assign(form, {
          network: props.subnet.network || '',
          netmask: props.subnet.netmask || '',
          gateway: props.subnet.gateway || '',
          vlan_id: props.subnet.vlan_id || null,
          location: props.subnet.location || '',
          description: props.subnet.description || ''
        })
      } else {
        Object.assign(form, {
          network: '',
          netmask: '',
          gateway: '',
          vlan_id: null,
          location: '',
          description: ''
        })
      }
      
      // 重置验证状态
      networkValidation.isValid = false
      networkValidation.message = ''
      networkValidation.overlapping_subnets = []
    }

    // 提交表单
    const handleSubmit = async () => {
      if (!formRef.value) return

      try {
        await formRef.value.validate()
        
        if (!networkValidation.isValid) {
          ElMessage.error('请先解决网段验证问题')
          return
        }

        submitting.value = true

        const submitData = {
          network: form.network,
          netmask: form.netmask,
          gateway: form.gateway || null,
          vlan_id: form.vlan_id || null,
          location: form.location || null,
          description: form.description || null
        }

        if (props.mode === 'create') {
          await subnetApi.createSubnet(submitData)
          ElMessage.success('网段创建成功')
        } else {
          await subnetApi.updateSubnet(props.subnet.id, submitData)
          ElMessage.success('网段更新成功')
        }

        emit('success')
        handleClose()
      } catch (error) {
        if (error.response?.data?.detail) {
          if (Array.isArray(error.response.data.detail)) {
            // 处理验证错误数组
            const errorMessages = error.response.data.detail.map(err => err.msg).join(', ')
            ElMessage.error(errorMessages)
          } else {
            ElMessage.error(error.response.data.detail)
          }
        } else {
          ElMessage.error('操作失败: ' + error.message)
        }
      } finally {
        submitting.value = false
      }
    }

    // 关闭对话框
    const handleClose = () => {
      emit('update:visible', false)
      nextTick(() => {
        formRef.value?.resetFields()
        initForm()
      })
    }

    // 监听对话框显示状态
    watch(() => props.visible, (visible) => {
      if (visible) {
        nextTick(() => {
          initForm()
          if (props.mode === 'edit' && form.network) {
            validateNetwork()
          }
        })
      }
    })

    // 监听网段输入变化
    watch(() => form.network, () => {
      if (form.network) {
        validateNetwork()
      } else {
        networkValidation.isValid = false
        networkValidation.message = ''
        networkValidation.overlapping_subnets = []
      }
    })

    return {
      formRef,
      submitting,
      form,
      rules,
      networkValidation,
      dialogTitle,
      validateNetwork,
      handleSubmit,
      handleClose
    }
  }
}
</script>

<style scoped>
.validation-success {
  color: #67c23a;
  font-size: 12px;
  margin-top: 4px;
}

.validation-error {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}

.dialog-footer {
  text-align: right;
}

:deep(.el-alert) {
  margin-top: 10px;
}

:deep(.el-alert ul) {
  margin: 8px 0 0 20px;
  padding: 0;
}

:deep(.el-alert li) {
  margin: 4px 0;
}
</style>