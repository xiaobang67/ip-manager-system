<template>
  <div class="custom-field-manager">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>自定义字段管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            添加字段
          </el-button>
        </div>
      </template>

      <!-- 字段列表 -->
      <el-table :data="fields" style="width: 100%">
        <el-table-column prop="field_name" label="字段名称" />
        <el-table-column prop="entity_type" label="实体类型">
          <template #default="scope">
            <el-tag :type="scope.row.entity_type === 'ip' ? 'primary' : 'success'">
              {{ scope.row.entity_type === 'ip' ? 'IP地址' : '网段' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="field_type" label="字段类型">
          <template #default="scope">
            <el-tag>{{ getFieldTypeLabel(scope.row.field_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_required" label="是否必填">
          <template #default="scope">
            <el-tag :type="scope.row.is_required ? 'danger' : 'info'">
              {{ scope.row.is_required ? '必填' : '可选' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editField(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="deleteField(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑字段对话框 -->
    <el-dialog
      :title="editingField ? '编辑字段' : '创建字段'"
      v-model="showCreateDialog"
      width="500px"
    >
      <el-form :model="fieldForm" :rules="fieldRules" ref="fieldFormRef" label-width="100px">
        <el-form-item label="字段名称" prop="field_name">
          <el-input v-model="fieldForm.field_name" placeholder="请输入字段名称" />
        </el-form-item>
        
        <el-form-item label="实体类型" prop="entity_type">
          <el-select v-model="fieldForm.entity_type" placeholder="请选择实体类型" style="width: 100%">
            <el-option label="IP地址" value="ip" />
            <el-option label="网段" value="subnet" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="字段类型" prop="field_type">
          <el-select v-model="fieldForm.field_type" placeholder="请选择字段类型" style="width: 100%">
            <el-option label="文本" value="text" />
            <el-option label="数字" value="number" />
            <el-option label="日期" value="date" />
            <el-option label="选择" value="select" />
          </el-select>
        </el-form-item>
        
        <el-form-item v-if="fieldForm.field_type === 'select'" label="选项" prop="options">
          <div>
            <el-input
              v-for="(option, index) in selectOptions"
              :key="index"
              v-model="selectOptions[index]"
              placeholder="请输入选项"
              style="margin-bottom: 8px"
            >
              <template #append>
                <el-button @click="removeOption(index)" :disabled="selectOptions.length <= 1">
                  删除
                </el-button>
              </template>
            </el-input>
            <el-button @click="addOption" type="primary" plain>添加选项</el-button>
          </div>
        </el-form-item>
        
        <el-form-item label="是否必填">
          <el-switch v-model="fieldForm.is_required" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" @click="saveField">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import customFieldsAPI from '@/api/customFields'
import { safeGetCustomFields } from '@/utils/customFieldsDebug'

export default {
  name: 'CustomFieldManager',
  components: {
    Plus
  },
  setup() {
    const fields = ref([])
    const showCreateDialog = ref(false)
    const editingField = ref(null)
    const fieldFormRef = ref(null)
    const selectOptions = ref([''])

    const fieldForm = reactive({
      field_name: '',
      entity_type: '',
      field_type: '',
      field_options: null,
      is_required: false
    })

    const fieldRules = {
      field_name: [
        { required: true, message: '请输入字段名称', trigger: 'blur' },
        { min: 1, max: 50, message: '字段名称长度在 1 到 50 个字符', trigger: 'blur' }
      ],
      entity_type: [
        { required: true, message: '请选择实体类型', trigger: 'change' }
      ],
      field_type: [
        { required: true, message: '请选择字段类型', trigger: 'change' }
      ]
    }

    const loadFields = async () => {
      try {
        // 使用安全的自定义字段加载方法
        fields.value = await safeGetCustomFields()
      } catch (error) {
        console.error('加载字段列表失败：', error)
        // 错误信息已在safeGetCustomFields中处理
      }
    }

    const getFieldTypeLabel = (type) => {
      const labels = {
        text: '文本',
        number: '数字',
        date: '日期',
        select: '选择'
      }
      return labels[type] || type
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }

    const addOption = () => {
      selectOptions.value.push('')
    }

    const removeOption = (index) => {
      if (selectOptions.value.length > 1) {
        selectOptions.value.splice(index, 1)
      }
    }

    const editField = (field) => {
      editingField.value = field
      fieldForm.field_name = field.field_name
      fieldForm.entity_type = field.entity_type
      fieldForm.field_type = field.field_type
      fieldForm.is_required = field.is_required
      
      if (field.field_type === 'select' && field.field_options && field.field_options.options) {
        selectOptions.value = [...field.field_options.options]
      } else {
        selectOptions.value = ['']
      }
      
      showCreateDialog.value = true
    }

    const cancelEdit = () => {
      showCreateDialog.value = false
      editingField.value = null
      fieldFormRef.value?.resetFields()
      selectOptions.value = ['']
    }

    const saveField = async () => {
      try {
        await fieldFormRef.value?.validate()
        
        const fieldData = { ...fieldForm }
        
        if (fieldForm.field_type === 'select') {
          const validOptions = selectOptions.value.filter(option => option.trim() !== '')
          if (validOptions.length === 0) {
            ElMessage.error('选择类型字段至少需要一个选项')
            return
          }
          fieldData.field_options = { options: validOptions }
        }

        if (editingField.value) {
          await customFieldsAPI.updateField(editingField.value.id, fieldData)
          ElMessage.success('字段更新成功')
        } else {
          await customFieldsAPI.createField(fieldData)
          ElMessage.success('字段创建成功')
        }
        
        cancelEdit()
        loadFields()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '保存失败')
      }
    }

    const deleteField = async (field) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除字段 "${field.field_name}" 吗？这将同时删除所有相关的字段值。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await customFieldsAPI.deleteField(field.id)
        ElMessage.success('字段删除成功')
        loadFields()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    onMounted(() => {
      loadFields()
    })

    return {
      fields,
      showCreateDialog,
      editingField,
      fieldForm,
      fieldRules,
      fieldFormRef,
      selectOptions,
      loadFields,
      getFieldTypeLabel,
      formatDate,
      addOption,
      removeOption,
      editField,
      cancelEdit,
      saveField,
      deleteField
    }
  }
}
</script>

<style scoped>
.custom-field-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dialog-footer {
  text-align: right;
}
</style>