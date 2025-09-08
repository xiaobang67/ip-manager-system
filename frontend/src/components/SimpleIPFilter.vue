<template>
  <div class="simple-ip-filter">
    <!-- 搜索和筛选区域 -->
    <div class="filter-container">
      <!-- 快速搜索栏 -->
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="搜索IP地址、使用人、MAC地址..."
          @input="handleQuickSearch"
          @keyup.enter="handleSearch"
          clearable
          class="search-input"
          size="default"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 筛选条件栏 -->
      <div class="filter-section">
        <el-row :gutter="16" align="middle">
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <div class="filter-item">
              <label class="filter-label">网段筛选</label>
              <el-select 
                v-model="filters.subnet_id" 
                placeholder="选择网段" 
                clearable
                @change="handleFilterChange"
                size="default"
              >
                <el-option
                  v-for="subnet in subnets"
                  :key="subnet.id"
                  :label="subnet.network"
                  :value="subnet.id"
                />
              </el-select>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6" :lg="4">
            <div class="filter-item">
              <label class="filter-label">状态筛选</label>
              <el-select 
                v-model="filters.status" 
                placeholder="选择状态" 
                clearable
                @change="handleFilterChange"
                size="default"
              >
                <el-option label="可用" value="available" />
                <el-option label="使用中" value="allocated" />
                <el-option label="保留" value="reserved" />
                <el-option label="冲突" value="conflict" />
              </el-select>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6" :lg="5">
            <div class="filter-item">
              <label class="filter-label">所属部门</label>
              <el-select 
                v-model="filters.assigned_to" 
                placeholder="选择部门" 
                clearable
                filterable
                allow-create
                @change="handleFilterChange"
                size="default"
              >
                <el-option
                  v-for="dept in departments"
                  :key="dept"
                  :label="dept"
                  :value="dept"
                />
              </el-select>
            </div>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="6" :lg="10">
            <div class="filter-actions">
              <el-button type="primary" @click="handleSearch" :loading="searching" size="default">
                <el-icon><Search /></el-icon>
                搜索
              </el-button>
              <el-button @click="handleReset" size="default">
                <el-icon><Refresh /></el-icon>
                重置
              </el-button>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 当前筛选条件显示 -->
    <div v-if="hasActiveFilters" class="active-filters">
      <span class="filter-label">当前筛选：</span>
      <el-tag
        v-if="filters.subnet_id"
        closable
        @close="clearFilter('subnet_id')"
        type="primary"
        size="small"
      >
        网段: {{ getSubnetName(filters.subnet_id) }}
      </el-tag>
      <el-tag
        v-if="filters.status"
        closable
        @close="clearFilter('status')"
        type="success"
        size="small"
      >
        状态: {{ getStatusText(filters.status) }}
      </el-tag>
      <el-tag
        v-if="filters.assigned_to"
        closable
        @close="clearFilter('assigned_to')"
        type="warning"
        size="small"
      >
        部门: {{ filters.assigned_to }}
      </el-tag>
      <el-tag
        v-if="searchQuery"
        closable
        @close="clearSearch"
        type="info"
        size="small"
      >
        关键词: {{ searchQuery }}
      </el-tag>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import { subnetApi, ipAPI } from '@/api'
import { debounce } from '@/utils/debounce'

export default {
  name: 'SimpleIPFilter',
  components: {
    Search,
    Refresh
  },
  emits: ['search', 'reset'],
  setup(props, { emit }) {
    // 响应式数据
    const searching = ref(false)
    const searchQuery = ref('')
    const subnets = ref([])
    const departments = ref([])
    
    // 筛选条件
    const filters = reactive({
      subnet_id: null,
      status: null,
      assigned_to: null
    })
    
    // 计算属性
    const hasActiveFilters = computed(() => {
      return filters.subnet_id || filters.status || filters.assigned_to || searchQuery.value
    })
    
    // 方法
    const loadSubnets = async () => {
      try {
        const response = await subnetApi.getSubnets()
        subnets.value = response.subnets || response.data || []
      } catch (error) {
        console.error('加载网段列表失败：', error)
      }
    }
    
    const loadDepartments = async () => {
      try {
        // 首先尝试从组织管理API获取部门列表
        const { getDepartmentOptions } = await import('@/api/departments')
        const response = await getDepartmentOptions()
        
        if (response && response.data && response.data.departments) {
          // 处理API响应格式：response.data.departments
          const apiDepartments = response.data.departments.map(dept => dept.name).sort()
          departments.value = apiDepartments
          return
        } else if (response && response.departments) {
          // 处理直接响应格式：response.departments
          const apiDepartments = response.departments.map(dept => dept.name).sort()
          departments.value = apiDepartments
          return
        }
        
        // 如果部门API没有返回数据，尝试从使用中IP中获取
        const ipResponse = await ipAPI.searchIPs({ 
          status: 'allocated', 
          limit: 1000 
        })
        const ips = ipResponse.data || ipResponse || []
        
        // 提取所有非空的assigned_to值并去重
        const assignedTos = ips
          .map(ip => ip.assigned_to)
          .filter(assigned => assigned && assigned.trim())
          .filter((value, index, self) => self.indexOf(value) === index)
          .sort()
        
        // 合并静态部门列表和动态获取的部门
        const staticDepartments = [
          '技术部',
          '运维部', 
          '产品部',
          '市场部',
          '人事部',
          '财务部',
          '客服部'
        ]
        
        // 合并并去重
        const allDepartments = [...staticDepartments, ...assignedTos]
          .filter((value, index, self) => self.indexOf(value) === index)
          .sort()
        
        departments.value = allDepartments
        
      } catch (error) {
        console.error('加载部门列表失败：', error)
        // 如果获取失败，使用静态列表
        departments.value = [
          '技术部',
          '运维部', 
          '产品部',
          '市场部',
          '人事部',
          '财务部',
          '客服部'
        ]
      }
    }
    
    const handleFilterChange = () => {
      // 筛选条件变化时自动搜索
      handleSearch()
    }
    
    const handleSearch = () => {
      searching.value = true
      
      // 构建搜索参数
      const searchParams = {
        query: searchQuery.value || undefined,
        subnet_id: filters.subnet_id || undefined,
        status: filters.status || undefined,
        assigned_to: filters.assigned_to || undefined
      }
      
      // 清理空值
      Object.keys(searchParams).forEach(key => {
        if (searchParams[key] === undefined || searchParams[key] === '') {
          delete searchParams[key]
        }
      })
      

      
      emit('search', searchParams)
      
      setTimeout(() => {
        searching.value = false
      }, 500)
    }
    
    const handleQuickSearch = () => {

      if (searchQuery.value && searchQuery.value.length >= 2) {
        handleSearch()
      } else if (!searchQuery.value) {
        handleSearch()
      }
    }
    
    const handleReset = () => {
      // 重置所有筛选条件
      filters.subnet_id = null
      filters.status = null
      filters.assigned_to = null
      searchQuery.value = ''
      
      emit('reset')
    }
    
    const clearFilter = (filterKey) => {
      filters[filterKey] = null
      handleSearch()
    }
    
    const clearSearch = () => {
      searchQuery.value = ''
      handleSearch()
    }
    
    const getSubnetName = (subnetId) => {
      const subnet = subnets.value.find(s => s.id === subnetId)
      return subnet ? subnet.network : `网段${subnetId}`
    }
    
    const getStatusText = (status) => {
      const statusMap = {
        available: '可用',
        allocated: '使用中',
        reserved: '保留',
        conflict: '冲突'
      }
      return statusMap[status] || status
    }
    
    // 生命周期
    onMounted(() => {
      loadSubnets()
      loadDepartments()
    })
    
    return {
      // 响应式数据
      searching,
      searchQuery,
      subnets,
      departments,
      filters,
      hasActiveFilters,
      
      // 方法
      handleFilterChange,
      handleSearch,
      handleQuickSearch,
      handleReset,
      clearFilter,
      clearSearch,
      getSubnetName,
      getStatusText
    }
  }
}
</script>

<style scoped>
.simple-ip-filter {
  margin-bottom: 20px;
  background-color: var(--bg-color, #ffffff);
  border: 1px solid var(--border-color, #e4e7ed);
  border-radius: 8px;
  padding: 20px;
  color: var(--text-color-primary, #303133);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
}

.filter-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.search-section {
  display: flex;
  justify-content: flex-start;
}

.search-input {
  width: 100%;
  max-width: 400px;
}

.filter-section {
  width: 100%;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.filter-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color-regular, #606266);
  margin-bottom: 2px;
  white-space: nowrap;
}

.filter-item .el-select {
  width: 100%;
}

.filter-actions {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  justify-content: flex-start;
  padding-top: 20px;
}

.filter-actions .el-button {
  min-width: 80px;
}

.active-filters {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 16px;
  border-top: 1px solid var(--border-color-lighter, #f0f0f0);
  margin-top: 8px;
}

.active-filters .filter-label {
  color: var(--text-color-secondary, #909399);
  margin-right: 8px;
  font-size: 13px;
  white-space: nowrap;
}

.active-filters .el-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .filter-actions {
    padding-top: 16px;
  }
}

@media (max-width: 768px) {
  .simple-ip-filter {
    padding: 16px;
  }
  
  .filter-container {
    gap: 12px;
  }
  
  .search-input {
    max-width: 100%;
  }
  
  .filter-section .el-col {
    margin-bottom: 12px;
  }
  
  .filter-actions {
    justify-content: flex-start;
    flex-wrap: wrap;
    padding-top: 12px;
  }
  
  .filter-actions .el-button {
    min-width: 70px;
    flex: 1;
    max-width: 120px;
  }
}

@media (max-width: 480px) {
  .simple-ip-filter {
    padding: 12px;
  }
  
  .filter-label {
    font-size: 12px;
  }
  
  .filter-actions .el-button {
    font-size: 13px;
    padding: 8px 12px;
  }
}
</style>