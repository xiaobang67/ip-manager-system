<template>
  <div class="tag-manager">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>标签管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            添加标签
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索标签名称"
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 标签列表 -->
      <el-table :data="displayTags" style="width: 100%; margin-top: 20px">
        <el-table-column prop="name" label="标签名称">
          <template #default="scope">
            <el-tag :color="scope.row.color" style="color: white; border: none;">
              {{ scope.row.name }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="color" label="颜色">
          <template #default="scope">
            <div class="color-display">
              <div 
                class="color-box" 
                :style="{ backgroundColor: scope.row.color }"
              ></div>
              <span>{{ scope.row.color }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="使用统计" v-if="showUsageStats">
          <template #default="scope">
            <div class="usage-stats">
              <el-tag size="small" type="info">IP: {{ getUsageCount(scope.row.id, 'ip') }}</el-tag>
              <el-tag size="small" type="success">网段: {{ getUsageCount(scope.row.id, 'subnet') }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="scope">
            <el-button size="small" @click="editTag(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="deleteTag(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-if="!searchQuery"
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalTags"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; text-align: right"
      />
    </el-card>

    <!-- 创建/编辑标签对话框 -->
    <el-dialog
      :title="editingTag ? '编辑标签' : '创建标签'"
      v-model="showCreateDialog"
      width="400px"
    >
      <el-form :model="tagForm" :rules="tagRules" ref="tagFormRef" label-width="80px">
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="tagForm.name" placeholder="请输入标签名称" />
        </el-form-item>
        
        <el-form-item label="颜色" prop="color">
          <div class="color-picker-container">
            <el-color-picker v-model="tagForm.color" />
            <el-input v-model="tagForm.color" placeholder="#007bff" style="margin-left: 10px" />
          </div>
        </el-form-item>
        
        <el-form-item label="描述">
          <el-input
            v-model="tagForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入标签描述（可选）"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelEdit">取消</el-button>
          <el-button type="primary" @click="saveTag">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import tagsAPI from '@/api/tags'
import { debounce } from '@/utils/debounce'

export default {
  name: 'TagManager',
  components: {
    Plus,
    Search
  },
  setup() {
    const tags = ref([])
    const searchResults = ref([])
    const searchQuery = ref('')
    const showCreateDialog = ref(false)
    const editingTag = ref(null)
    const tagFormRef = ref(null)
    const showUsageStats = ref(false)
    const usageStats = ref([])
    
    // 分页相关
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalTags = ref(0)

    const tagForm = reactive({
      name: '',
      color: '#007bff',
      description: ''
    })

    const tagRules = {
      name: [
        { required: true, message: '请输入标签名称', trigger: 'blur' },
        { min: 1, max: 50, message: '标签名称长度在 1 到 50 个字符', trigger: 'blur' },
        { pattern: /^[\w\u4e00-\u9fff\-]+$/, message: '标签名称只能包含字母、数字、中文、连字符和下划线', trigger: 'blur' }
      ],
      color: [
        { required: true, message: '请选择颜色', trigger: 'blur' },
        { pattern: /^#[0-9A-Fa-f]{6}$/, message: '请输入有效的十六进制颜色值', trigger: 'blur' }
      ]
    }

    const displayTags = computed(() => {
      return searchQuery.value ? searchResults.value : tags.value
    })

    const loadTags = async () => {
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }
        const response = await tagsAPI.getTags(params)
        tags.value = response.data
        // 注意：这里假设API返回了总数，实际可能需要调整
        totalTags.value = response.total || response.data.length
      } catch (error) {
        ElMessage.error('加载标签列表失败')
      }
    }

    const loadUsageStats = async () => {
      try {
        const response = await tagsAPI.getTagsUsageStats()
        usageStats.value = response.data
        showUsageStats.value = true
      } catch (error) {
        console.error('加载使用统计失败:', error)
      }
    }

    const getUsageCount = (tagId, entityType) => {
      const stat = usageStats.value.find(s => s.tag.id === tagId)
      if (!stat) return 0
      return entityType === 'ip' ? stat.ip_count : stat.subnet_count
    }

    const handleSearch = debounce(async () => {
      if (!searchQuery.value.trim()) {
        searchResults.value = []
        return
      }
      
      try {
        const response = await tagsAPI.searchTags(searchQuery.value)
        searchResults.value = response.data
      } catch (error) {
        ElMessage.error('搜索失败')
      }
    }, 300)

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }

    const editTag = (tag) => {
      editingTag.value = tag
      tagForm.name = tag.name
      tagForm.color = tag.color
      tagForm.description = tag.description || ''
      showCreateDialog.value = true
    }

    const cancelEdit = () => {
      showCreateDialog.value = false
      editingTag.value = null
      tagFormRef.value?.resetFields()
    }

    const saveTag = async () => {
      try {
        await tagFormRef.value?.validate()
        
        if (editingTag.value) {
          await tagsAPI.updateTag(editingTag.value.id, tagForm)
          ElMessage.success('标签更新成功')
        } else {
          await tagsAPI.createTag(tagForm)
          ElMessage.success('标签创建成功')
        }
        
        cancelEdit()
        loadTags()
        if (showUsageStats.value) {
          loadUsageStats()
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '保存失败')
      }
    }

    const deleteTag = async (tag) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除标签 "${tag.name}" 吗？这将从所有关联的IP地址和网段中移除此标签。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await tagsAPI.deleteTag(tag.id)
        ElMessage.success('标签删除成功')
        loadTags()
        if (showUsageStats.value) {
          loadUsageStats()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const handleSizeChange = (newSize) => {
      pageSize.value = newSize
      currentPage.value = 1
      loadTags()
    }

    const handleCurrentChange = (newPage) => {
      currentPage.value = newPage
      loadTags()
    }

    onMounted(() => {
      loadTags()
      loadUsageStats()
    })

    return {
      tags,
      searchResults,
      searchQuery,
      displayTags,
      showCreateDialog,
      editingTag,
      tagForm,
      tagRules,
      tagFormRef,
      showUsageStats,
      usageStats,
      currentPage,
      pageSize,
      totalTags,
      loadTags,
      getUsageCount,
      handleSearch,
      formatDate,
      editTag,
      cancelEdit,
      saveTag,
      deleteTag,
      handleSizeChange,
      handleCurrentChange
    }
  }
}
</script>

<style scoped>
.tag-manager {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
}

.color-display {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #ddd;
}

.color-picker-container {
  display: flex;
  align-items: center;
}

.usage-stats {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.dialog-footer {
  text-align: right;
}
</style>