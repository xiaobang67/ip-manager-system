<template>
  <div class="department-list">
    <!-- 操作栏 -->
    <el-card class="toolbar-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增部门
          </el-button>
          <el-button type="success" @click="toggleTreeView">
            <el-icon><Grid /></el-icon>
            {{ isTreeView ? '列表视图' : '树形视图' }}
          </el-button>
          <el-button type="warning" @click="handleExport">
            <el-icon><Download /></el-icon>
            导出数据
          </el-button>
        </div>
        <div class="toolbar-right">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索部门名称或编码"
            clearable
            style="width: 200px; margin-right: 10px"
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-button @click="loadData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 数据展示 -->
    <el-card class="table-card">
      <!-- 树形视图 -->
      <div v-if="isTreeView">
        <el-tree
          :data="treeData"
          :props="treeProps"
          :expand-on-click-node="false"
          default-expand-all
          node-key="id"
          class="department-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <div class="node-content">
                <span class="node-label">{{ data.name }}</span>
                <el-tag size="small" class="node-code">{{ data.code }}</el-tag>
                <el-tag
                  :type="data.is_active ? 'success' : 'danger'"
                  size="small"
                  class="node-status"
                >
                  {{ data.is_active ? '启用' : '禁用' }}
                </el-tag>
              </div>
              <div class="node-actions">
                <el-button type="primary" size="small" @click="handleAddChild(data)">
                  添加子部门
                </el-button>
                <el-button type="info" size="small" @click="handleViewStats(data)">
                  统计
                </el-button>
                <el-button type="warning" size="small" @click="handleEdit(data)">
                  编辑
                </el-button>
                <el-dropdown @command="(command) => handleDropdownCommand(command, data)">
                  <el-button size="small">
                    更多<el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item :command="data.is_active ? 'disable' : 'enable'">
                        {{ data.is_active ? '禁用' : '启用' }}
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </template>
        </el-tree>
      </div>

      <!-- 列表视图 -->
      <div v-else>
        <el-table
          :data="filteredTableData"
          v-loading="loading"
          stripe
          border
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          
          <el-table-column prop="name" label="部门名称" width="200" />

          <el-table-column prop="code" label="部门编码" width="150">
            <template #default="{ row }">
              <el-tag>{{ row.code }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column label="上级部门" width="150">
            <template #default="{ row }">
              <span v-if="row.parent">{{ row.parent.name }}</span>
              <span v-else class="text-muted">无</span>
            </template>
          </el-table-column>

          <el-table-column prop="description" label="部门描述" min-width="200" show-overflow-tooltip />

          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="created_at" label="创建时间" width="150">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>

          <el-table-column label="操作" width="280" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleAddChild(row)">
                添加子部门
              </el-button>
              <el-button type="info" size="small" @click="handleViewStats(row)">
                统计
              </el-button>
              <el-button type="warning" size="small" @click="handleEdit(row)">
                编辑
              </el-button>
              <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
                <el-button size="small">
                  更多<el-icon><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="row.is_active ? 'disable' : 'enable'">
                      {{ row.is_active ? '禁用' : '启用' }}
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 新增/编辑部门对话框 -->
    <el-dialog
      v-model="formDialogVisible"
      :title="isEdit ? '编辑部门' : (isAddChild ? '新增子部门' : '新增部门')"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入部门名称" />
        </el-form-item>

        <el-form-item label="部门编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入部门编码" />
        </el-form-item>

        <el-form-item label="上级部门">
          <el-tree-select
            v-model="form.parent_id"
            :data="treeSelectData"
            :props="treeSelectProps"
            placeholder="请选择上级部门"
            clearable
            check-strictly
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="部门描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入部门描述"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleFormSubmit">确认</el-button>
      </template>
    </el-dialog>

    <!-- 部门统计对话框 -->
    <el-dialog
      v-model="statsDialogVisible"
      title="部门统计信息"
      width="500px"
    >
      <div v-if="currentDepartmentStats" class="stats-container">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">用户数量</div>
              <div class="stat-value">{{ currentDepartmentStats.user_count }}</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">子部门数量</div>
              <div class="stat-value">{{ currentDepartmentStats.children_count }}</div>
            </div>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 20px;">
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">负责网段</div>
              <div class="stat-value">{{ currentDepartmentStats.segment_count }}</div>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="stat-item">
              <div class="stat-label">分配IP数</div>
              <div class="stat-value">{{ currentDepartmentStats.ip_count }}</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Grid,
  Download,
  Search,
  Refresh,
  ArrowDown
} from '@element-plus/icons-vue'
import { departmentApi } from '@/api/department'
import type { Department, DepartmentCreate } from '@/types'

// 响应式数据
const loading = ref(false)
const tableData = ref<Department[]>([])
const treeData = ref<Department[]>([])
const selectedRows = ref<Department[]>([])
const searchKeyword = ref('')
const isTreeView = ref(true)

// 表单对话框
const formDialogVisible = ref(false)
const isEdit = ref(false)
const isAddChild = ref(false)
const formRef = ref()
const form = reactive<DepartmentCreate>({
  name: '',
  code: '',
  parent_id: undefined,
  description: '',
  is_active: true
})

const formRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 2, max: 100, message: '部门名称长度应在2-100个字符之间', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入部门编码', trigger: 'blur' },
    { min: 2, max: 50, message: '部门编码长度应在2-50个字符之间', trigger: 'blur' },
    { pattern: /^[A-Za-z0-9_-]+$/, message: '部门编码只能包含字母、数字、下划线和连字符', trigger: 'blur' }
  ],
  description: [
    { max: 500, message: '部门描述最长500个字符', trigger: 'blur' }
  ]
}

// 统计对话框
const statsDialogVisible = ref(false)
const currentDepartmentStats = ref<any>()
const currentEditRow = ref<Department>()
const parentDepartment = ref<Department>()

// 树形组件配置
const treeProps = {
  children: 'children',
  label: 'name'
}

const treeSelectProps = {
  children: 'children',
  label: 'name',
  value: 'id'
}

// 计算属性
const filteredTableData = computed(() => {
  if (!searchKeyword.value) return tableData.value
  
  return tableData.value.filter(item =>
    item.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
    item.code.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

const treeSelectData = computed(() => {
  // 构建树选择器数据，排除当前编辑的部门及其子部门
  const buildTreeData = (departments: Department[], excludeId?: number): Department[] => {
    return departments
      .filter(dept => dept.id !== excludeId)
      .map(dept => ({
        ...dept,
        children: dept.children ? buildTreeData(dept.children, excludeId) : undefined
      }))
  }
  
  return buildTreeData(treeData.value, currentEditRow.value?.id)
})

// 方法
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadData = async () => {
  loading.value = true
  try {
    // 加载列表数据
    const listData = await departmentApi.getList({ limit: 1000 })
    tableData.value = listData
    
    // 加载树形数据
    const treeDataResult = await departmentApi.getTree()
    treeData.value = treeDataResult
  } catch (error) {
    ElMessage.error('加载数据失败')
    console.error(error)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索功能在计算属性中实现
}

const toggleTreeView = () => {
  isTreeView.value = !isTreeView.value
}

const handleAdd = () => {
  isEdit.value = false
  isAddChild.value = false
  parentDepartment.value = undefined
  resetForm()
  formDialogVisible.value = true
}

const handleAddChild = (parent: Department) => {
  isEdit.value = false
  isAddChild.value = true
  parentDepartment.value = parent
  resetForm()
  form.parent_id = parent.id
  formDialogVisible.value = true
}

const handleEdit = (row: Department) => {
  isEdit.value = true
  isAddChild.value = false
  currentEditRow.value = row
  
  // 填充表单数据
  Object.assign(form, {
    name: row.name,
    code: row.code,
    parent_id: row.parent_id,
    description: row.description || '',
    is_active: row.is_active
  })
  
  formDialogVisible.value = true
}

const handleFormSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    
    // 创建表单数据副本用于处理
    const formData = {...form}
    
    // 确保非必填字段在为空时设置为undefined而不是空字符串
    Object.keys(formData).forEach(key => {
      if (formData[key] === '') {
        formData[key] = undefined
      }
    })
    
    if (isEdit.value && currentEditRow.value) {
      await departmentApi.update(currentEditRow.value.id, formData)
      ElMessage.success('部门更新成功')
    } else {
      await departmentApi.create(formData)
      ElMessage.success('部门创建成功')
    }
    
    formDialogVisible.value = false
    loadData()
  } catch (error) {
    console.error('保存部门失败:', error)
  }
}

const handleViewStats = async (row: Department) => {
  try {
    const stats = await departmentApi.getStatistics(row.id)
    currentDepartmentStats.value = stats
    statsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取统计信息失败')
    console.error(error)
  }
}

const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

const handleSelectionChange = (selection: Department[]) => {
  selectedRows.value = selection
}

const handleDropdownCommand = async (command: string, row: Department) => {
  switch (command) {
    case 'enable':
    case 'disable':
      await handleToggleStatus(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

const handleToggleStatus = async (row: Department) => {
  try {
    const action = row.is_active ? '禁用' : '启用'
    await ElMessageBox.confirm(
      `确定要${action}部门 ${row.name} 吗？`,
      `确认${action}`,
      { type: 'warning' }
    )
    
    await departmentApi.update(row.id, { is_active: !row.is_active })
    ElMessage.success(`${action}成功`)
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('切换部门状态失败:', error)
    }
  }
}

const handleDelete = async (row: Department) => {
  try {
    // 检查是否有子部门
    if (row.children && row.children.length > 0) {
      ElMessageBox.alert(
        `无法删除部门 ${row.name}，因为该部门下有 ${row.children.length} 个子部门。请先删除所有子部门后再尝试删除。`,
        '无法删除部门',
        { type: 'error' }
      )
      return
    }
    
    // 检查部门下是否有用户
    try {
      const users = await userApi.getByDepartment(row.id)
      if (users && users.length > 0) {
        ElMessageBox.alert(
          `无法删除部门 ${row.name}，因为该部门下有 ${users.length} 个用户。请先将这些用户转移到其他部门或删除后再尝试删除部门。`,
          '无法删除部门',
          { type: 'error' }
        )
        return
      }
    } catch (err) {
      console.error('获取部门用户失败:', err)
      // 如果无法获取用户列表，仍然允许继续删除流程
    }
    
    // 如果没有子部门和用户，则可以继续删除流程
    await ElMessageBox.confirm(
      `确定要删除部门 ${row.name} 吗？此操作不可恢复！`,
      '确认删除',
      { type: 'warning' }
    )
    
    await departmentApi.delete(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除部门失败:', error)
    }
  }
}

const resetForm = () => {
  Object.assign(form, {
    name: '',
    code: '',
    parent_id: undefined,
    description: '',
    is_active: true
  })
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.department-list {
  padding: 0;
}

.toolbar-card,
.table-card {
  margin-bottom: 20px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.text-muted {
  color: #909399;
}

.department-tree {
  padding: 20px 0;
}

.tree-node {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.node-label {
  font-weight: 500;
  margin-right: 8px;
}

.node-code {
  margin-right: 8px;
}

.node-status {
  margin-right: 16px;
}

.node-actions {
  display: flex;
  gap: 8px;
}

.stats-container {
  padding: 20px 0;
}

.stat-item {
  text-align: center;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  transition: all 0.3s;
}

.stat-item:hover {
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    gap: 10px;
  }
  
  .toolbar-left,
  .toolbar-right {
    width: 100%;
    justify-content: center;
    flex-wrap: wrap;
  }
  
  .node-actions {
    flex-direction: column;
    gap: 4px;
  }
  
  .node-actions .el-button {
    margin: 0;
  }
}
</style>