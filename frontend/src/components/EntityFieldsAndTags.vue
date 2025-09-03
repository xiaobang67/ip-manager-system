<template>
  <div class="entity-fields-and-tags">
    <!-- 自定义字段部分 -->
    <el-card class="box-card" v-if="customFields.length > 0">
      <template #header>
        <div class="card-header">
          <span>自定义字段</span>
          <el-button size="small" @click="editMode = !editMode">
            {{ editMode ? '取消编辑' : '编辑' }}
          </el-button>
        </div>
      </template>

      <el-form :model="fieldValues" ref="fieldFormRef" label-width="120px">
        <el-form-item
          v-for="field in customFields"
          :key="field.id"
          :label="field.field_name"
          :prop="`${field.id}`"
          :rules="getFieldRules(field)"
        >
          <div v-if="!editMode" class="field-display">
            <span v-if="field.value">{{ formatFieldValue(field) }}</span>
            <span v-else class="empty-value">未设置</span>
          </div>
          
          <div v-else>
            <!-- 文本类型 -->
            <el-input
              v-if="field.field_type === 'text'"
              v-model="fieldValues[field.id]"
              :placeholder="`请输入${field.field_name}`"
            />
            
            <!-- 数字类型 -->
            <el-input-number
              v-else-if="field.field_type === 'number'"
              v-model="fieldValues[field.id]"
              :placeholder="`请输入${field.field_name}`"
              style="width: 100%"
            />
            
            <!-- 日期类型 -->
            <el-date-picker
              v-else-if="field.field_type === 'date'"
              v-model="fieldValues[field.id]"
              type="date"
              :placeholder="`请选择${field.field_name}`"
              style="width: 100%"
            />
            
            <!-- 选择类型 -->
            <el-select
              v-else-if="field.field_type === 'select'"
              v-model="fieldValues[field.id]"
              :placeholder="`请选择${field.field_name}`"
              style="width: 100%"
            >
              <el-option
                v-for="option in field.field_options?.options || []"
                :key="option"
                :label="option"
                :value="option"
              />
            </el-select>
          </div>
        </el-form-item>
        
        <el-form-item v-if="editMode">
          <el-button type="primary" @click="saveFields">保存字段</el-button>
          <el-button @click="resetFields">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 标签部分 -->
    <el-card class="box-card" style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>标签</span>
          <el-button size="small" @click="showTagDialog = true">
            <el-icon><Plus /></el-icon>
            管理标签
          </el-button>
        </div>
      </template>

      <div class="tags-display">
        <el-tag
          v-for="tag in entityTags"
          :key="tag.id"
          :color="tag.color"
          closable
          @close="removeTag(tag.id)"
          style="margin-right: 8px; margin-bottom: 8px; color: white; border: none;"
        >
          {{ tag.name }}
        </el-tag>
        
        <div v-if="entityTags.length === 0" class="empty-tags">
          暂无标签
        </div>
      </div>
    </el-card>

    <!-- 标签管理对话框 -->
    <el-dialog
      title="管理标签"
      v-model="showTagDialog"
      width="500px"
    >
      <div class="tag-management">
        <!-- 搜索标签 -->
        <el-input
          v-model="tagSearchQuery"
          placeholder="搜索标签"
          @input="searchTags"
          style="margin-bottom: 20px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <!-- 可用标签列表 -->
        <div class="available-tags">
          <h4>可用标签</h4>
          <div class="tag-list">
            <el-tag
              v-for="tag in availableTags"
              :key="tag.id"
              :color="tag.color"
              :class="{ 'selected-tag': selectedTagIds.includes(tag.id) }"
              @click="toggleTagSelection(tag.id)"
              style="margin-right: 8px; margin-bottom: 8px; cursor: pointer; color: white; border: none;"
            >
              {{ tag.name }}
              <el-icon v-if="selectedTagIds.includes(tag.id)"><Check /></el-icon>
            </el-tag>
          </div>
        </div>

        <!-- 当前标签 -->
        <div class="current-tags" style="margin-top: 20px">
          <h4>当前标签</h4>
          <div class="tag-list">
            <el-tag
              v-for="tag in entityTags"
              :key="tag.id"
              :color="tag.color"
              closable
              @close="removeTag(tag.id)"
              style="margin-right: 8px; margin-bottom: 8px; color: white; border: none;"
            >
              {{ tag.name }}
            </el-tag>
          </div>
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showTagDialog = false">关闭</el-button>
          <el-button type="primary" @click="saveTags">保存标签</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search, Check } from '@element-plus/icons-vue'
import customFieldsAPI from '@/api/customFields'
import { safeGetEntityCustomFields } from '@/utils/customFieldsDebug'
import tagsAPI from '@/api/tags'
import { debounce } from '@/utils/debounce'

export default {
  name: 'EntityFieldsAndTags',
  components: {
    Plus,
    Search,
    Check
  },
  props: {
    entityType: {
      type: String,
      required: true,
      validator: (value) => ['ip', 'subnet'].includes(value)
    },
    entityId: {
      type: Number,
      required: true
    }
  },
  setup(props) {
    const customFields = ref([])
    const entityTags = ref([])
    const allTags = ref([])
    const searchedTags = ref([])
    const editMode = ref(false)
    const showTagDialog = ref(false)
    const fieldFormRef = ref(null)
    const tagSearchQuery = ref('')
    const selectedTagIds = ref([])

    const fieldValues = reactive({})

    const availableTags = computed(() => {
      return tagSearchQuery.value ? searchedTags.value : allTags.value
    })

    const loadCustomFields = async () => {
      try {
        // 使用安全的自定义字段加载方法
        const result = await safeGetEntityCustomFields(props.entityType, props.entityId)
        customFields.value = result.fields || []
        
        // 初始化字段值
        customFields.value.forEach(field => {
          fieldValues[field.id] = field.value || ''
        })
      } catch (error) {
        console.error('加载自定义字段失败:', error)
        // 错误信息已在safeGetEntityCustomFields中处理
      }
    }

    const loadEntityTags = async () => {
      try {
        let response
        if (props.entityType === 'ip') {
          response = await tagsAPI.getIPTags(props.entityId)
        } else {
          response = await tagsAPI.getSubnetTags(props.entityId)
        }
        entityTags.value = response.data.tags
      } catch (error) {
        console.error('加载实体标签失败:', error)
      }
    }

    const loadAllTags = async () => {
      try {
        const response = await tagsAPI.getTags({ limit: 1000 })
        allTags.value = response.data
      } catch (error) {
        console.error('加载标签列表失败:', error)
      }
    }

    const searchTags = debounce(async () => {
      if (!tagSearchQuery.value.trim()) {
        searchedTags.value = []
        return
      }
      
      try {
        const response = await tagsAPI.searchTags(tagSearchQuery.value)
        searchedTags.value = response.data
      } catch (error) {
        console.error('搜索标签失败:', error)
      }
    }, 300)

    const getFieldRules = (field) => {
      const rules = []
      
      if (field.is_required) {
        rules.push({
          required: true,
          message: `${field.field_name}是必填字段`,
          trigger: 'blur'
        })
      }
      
      if (field.field_type === 'number') {
        rules.push({
          type: 'number',
          message: `${field.field_name}必须是数字`,
          trigger: 'blur'
        })
      }
      
      return rules
    }

    const formatFieldValue = (field) => {
      if (!field.value) return ''
      
      switch (field.field_type) {
        case 'date':
          return new Date(field.value).toLocaleDateString('zh-CN')
        case 'number':
          return Number(field.value).toLocaleString()
        default:
          return field.value
      }
    }

    const saveFields = async () => {
      try {
        await fieldFormRef.value?.validate()
        
        // 转换字段值格式
        const formattedValues = {}
        Object.keys(fieldValues).forEach(fieldId => {
          const field = customFields.value.find(f => f.id == fieldId)
          let value = fieldValues[fieldId]
          
          if (field && value !== null && value !== undefined && value !== '') {
            if (field.field_type === 'date' && value instanceof Date) {
              value = value.toISOString()
            } else if (field.field_type === 'number') {
              value = String(value)
            } else {
              value = String(value)
            }
          } else {
            value = ''
          }
          
          formattedValues[fieldId] = value
        })
        
        await customFieldsAPI.updateEntityFields(props.entityType, props.entityId, formattedValues)
        ElMessage.success('字段保存成功')
        editMode.value = false
        loadCustomFields()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '保存失败')
      }
    }

    const resetFields = () => {
      customFields.value.forEach(field => {
        fieldValues[field.id] = field.value || ''
      })
    }

    const toggleTagSelection = (tagId) => {
      const index = selectedTagIds.value.indexOf(tagId)
      if (index > -1) {
        selectedTagIds.value.splice(index, 1)
      } else {
        selectedTagIds.value.push(tagId)
      }
    }

    const saveTags = async () => {
      try {
        const currentTagIds = entityTags.value.map(tag => tag.id)
        const newTagIds = [...currentTagIds, ...selectedTagIds.value]
        const uniqueTagIds = [...new Set(newTagIds)]
        
        await tagsAPI.assignTags(props.entityType, props.entityId, uniqueTagIds)
        ElMessage.success('标签保存成功')
        showTagDialog.value = false
        selectedTagIds.value = []
        loadEntityTags()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '保存失败')
      }
    }

    const removeTag = async (tagId) => {
      try {
        if (props.entityType === 'ip') {
          await tagsAPI.removeTagFromIP(props.entityId, tagId)
        } else {
          await tagsAPI.removeTagFromSubnet(props.entityId, tagId)
        }
        ElMessage.success('标签移除成功')
        loadEntityTags()
      } catch (error) {
        ElMessage.error('移除标签失败')
      }
    }

    // 监听props变化，重新加载数据
    watch(() => [props.entityType, props.entityId], () => {
      loadCustomFields()
      loadEntityTags()
    }, { immediate: true })

    onMounted(() => {
      loadAllTags()
    })

    return {
      customFields,
      entityTags,
      allTags,
      availableTags,
      editMode,
      showTagDialog,
      fieldFormRef,
      tagSearchQuery,
      selectedTagIds,
      fieldValues,
      getFieldRules,
      formatFieldValue,
      saveFields,
      resetFields,
      searchTags,
      toggleTagSelection,
      saveTags,
      removeTag
    }
  }
}
</script>

<style scoped>
.entity-fields-and-tags {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.field-display {
  min-height: 32px;
  line-height: 32px;
}

.empty-value {
  color: #999;
  font-style: italic;
}

.tags-display {
  min-height: 40px;
}

.empty-tags {
  color: #999;
  font-style: italic;
  line-height: 40px;
}

.tag-management {
  max-height: 400px;
  overflow-y: auto;
}

.tag-list {
  max-height: 150px;
  overflow-y: auto;
}

.selected-tag {
  opacity: 0.8;
  transform: scale(0.95);
}

.dialog-footer {
  text-align: right;
}
</style>