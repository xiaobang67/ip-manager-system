<template>
  <AppLayout>
    <div class="subnet-management">
    <div class="page-header">
      <h1>网段管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog" :icon="Plus">
          添加网段
        </el-button>
      </div>
    </div>

    <!-- 搜索和过滤 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索网段、描述、位置..."
            :prefix-icon="Search"
            @input="handleSearch"
            clearable
          />
        </el-col>
        <el-col :span="4">
          <el-input
            v-model="vlanFilter"
            placeholder="VLAN ID"
            type="number"
            @input="handleVlanFilter"
            clearable
          />
        </el-col>
        <el-col :span="4">
          <el-button @click="resetFilters">重置</el-button>
        </el-col>
      </el-row>
    </div>

    <!-- 网段列表 -->
    <div class="subnet-list">
      <el-table
        :data="subnets"
        v-loading="loading"
        stripe
        style="width: 100%"
        @sort-change="handleSortChange"
      >
        <el-table-column prop="network" label="网段" width="150" sortable />
        <el-table-column prop="netmask" label="子网掩码" width="120" />
        <el-table-column prop="gateway" label="网关" width="120" />
        <el-table-column prop="vlan_id" label="VLAN ID" width="80" sortable />
        <el-table-column prop="location" label="位置" width="120" />
        <el-table-column prop="description" label="描述" min-width="150" show-overflow-tooltip />
        
        <!-- IP使用情况 -->
        <el-table-column label="IP使用情况" width="200">
          <template #default="scope">
            <div class="ip-usage">
              <div class="usage-text">
                {{ scope.row.allocated_count || 0 }} / {{ scope.row.ip_count || 0 }}
              </div>
              <el-progress
                :percentage="getUsagePercentage(scope.row)"
                :color="getUsageColor(scope.row)"
                :stroke-width="6"
                :show-text="false"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160" sortable>
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="viewSubnet(scope.row)">
              查看
            </el-button>
            <el-button size="small" type="primary" @click="editSubnet(scope.row)">
              编辑
            </el-button>
            <el-button 
              size="small" 
              type="warning" 
              @click="syncSubnetIPs(scope.row)"
              :loading="scope.row.syncing"
            >
              同步IP
            </el-button>
            <el-button
              v-if="isAdmin"
              size="small"
              type="danger"
              @click="deleteSubnet(scope.row)"
              :disabled="scope.row.allocated_count > 0"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑网段对话框 -->
    <SubnetDialog
      v-model:visible="dialogVisible"
      :subnet="currentSubnet"
      :mode="dialogMode"
      @success="handleDialogSuccess"
    />

    <!-- 网段详情对话框 -->
    <SubnetDetailDialog
      v-model:visible="detailDialogVisible"
      :subnet="currentSubnet"
    />
    </div>
  </AppLayout>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { subnetApi } from '@/api/subnet'
import AppLayout from '@/components/AppLayout.vue'
import SubnetDialog from '@/components/subnet/SubnetDialog.vue'
import SubnetDetailDialog from '@/components/subnet/SubnetDetailDialog.vue'
import { debounce } from '@/utils/debounce'
import { useStore } from 'vuex'

export default {
  name: 'SubnetManagement',
  components: {
    AppLayout,
    SubnetDialog,
    SubnetDetailDialog
  },
  setup() {
    // Vuex store
    const store = useStore()
    
    // 用户权限相关
    const currentUser = computed(() => store.getters['auth/currentUser'])
    const userRole = computed(() => store.getters['auth/userRole'])
    const isAdmin = computed(() => userRole.value === 'admin')
    
    // 响应式数据
    const loading = ref(false)
    const subnets = ref([])
    const total = ref(0)
    const currentPage = ref(1)
    const pageSize = ref(20)
    const searchQuery = ref('')
    const vlanFilter = ref('')
    
    // 对话框状态
    const dialogVisible = ref(false)
    const detailDialogVisible = ref(false)
    const dialogMode = ref('create') // 'create' | 'edit'
    const currentSubnet = ref(null)

    // 计算属性
    const isSearching = computed(() => searchQuery.value.trim() !== '')

    // 获取网段列表
    const fetchSubnets = async () => {
      loading.value = true
      
      try {
        const params = {
          skip: (currentPage.value - 1) * pageSize.value,
          limit: pageSize.value
        }

        let response
        if (isSearching.value) {
          response = await subnetApi.searchSubnets({
            ...params,
            q: searchQuery.value.trim()
          })
        } else {
          response = await subnetApi.getSubnets(params)
        }

        // 处理API响应数据
        if (!response) {
          subnets.value = []
          total.value = 0
          return
        }

        let subnetData = []
        let totalCount = 0

        if (response.subnets && Array.isArray(response.subnets)) {
          subnetData = response.subnets
          totalCount = response.total || 0
        } else if (response.data?.subnets && Array.isArray(response.data.subnets)) {
          subnetData = response.data.subnets
          totalCount = response.data.total || 0
        } else if (Array.isArray(response)) {
          subnetData = response
          totalCount = response.length
        } else if (response.data && Array.isArray(response.data)) {
          subnetData = response.data
          totalCount = response.data.length
        } else {
          subnetData = []
          totalCount = 0
        }

        subnets.value = subnetData
        total.value = totalCount
      } catch (error) {
        subnets.value = []
        total.value = 0
        ElMessage.error('获取网段列表失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        loading.value = false
      }
    }

    // 防抖搜索
    const handleSearch = debounce(() => {
      currentPage.value = 1
      fetchSubnets()
    }, 300)

    // VLAN过滤
    const handleVlanFilter = debounce(async () => {
      if (vlanFilter.value) {
        loading.value = true
        try {
          const response = await subnetApi.getSubnetsByVlan(vlanFilter.value)
          
          if (!response) {
            subnets.value = []
            total.value = 0
            return
          }

          let subnetData = []
          
          if (Array.isArray(response)) {
            subnetData = response
          } else if (response.data && Array.isArray(response.data)) {
            subnetData = response.data
          } else if (response.subnets && Array.isArray(response.subnets)) {
            subnetData = response.subnets
          } else {
            subnetData = []
          }

          subnets.value = subnetData
          total.value = subnetData.length
        } catch (error) {
          subnets.value = []
          total.value = 0
          ElMessage.error('按VLAN过滤失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          loading.value = false
        }
      } else {
        fetchSubnets()
      }
    }, 300)

    // 重置过滤器
    const resetFilters = () => {
      searchQuery.value = ''
      vlanFilter.value = ''
      currentPage.value = 1
      fetchSubnets()
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pageSize.value = size
      currentPage.value = 1
      fetchSubnets()
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
      fetchSubnets()
    }

    // 排序处理
    const handleSortChange = ({ column, prop, order }) => {
      // 这里可以实现排序逻辑
      // TODO: 实现服务端排序
    }

    // 显示创建对话框
    const showCreateDialog = () => {
      currentSubnet.value = null
      dialogMode.value = 'create'
      dialogVisible.value = true
    }

    // 查看网段详情
    const viewSubnet = (subnet) => {
      currentSubnet.value = subnet
      detailDialogVisible.value = true
    }

    // 编辑网段
    const editSubnet = (subnet) => {
      currentSubnet.value = subnet
      dialogMode.value = 'edit'
      dialogVisible.value = true
    }

    // 删除网段
    const deleteSubnet = async (subnet) => {
      if (subnet.allocated_count > 0) {
        ElMessage.warning('该网段存在使用中的IP地址，无法删除')
        return
      }

      try {
        await ElMessageBox.confirm(
          `确定要删除网段 ${subnet.network} 吗？此操作不可恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        await subnetApi.deleteSubnet(subnet.id)
        ElMessage.success('网段删除成功')
        fetchSubnets()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除网段失败: ' + (error.response?.data?.detail || error.message))
        }
      }
    }

    // 同步网段IP地址
    const syncSubnetIPs = async (subnet) => {
      try {
        await ElMessageBox.confirm(
          `确定要同步网段 ${subnet.network} 的IP地址吗？\n\n此操作将：\n• 根据CIDR格式重新生成正确的IP地址范围\n• 添加缺失的IP地址\n• 删除不属于该网段的未分配IP地址\n• 保留使用中的IP地址`,
          '确认同步IP地址',
          {
            confirmButtonText: '确定同步',
            cancelButtonText: '取消',
            type: 'warning',
            dangerouslyUseHTMLString: false
          }
        )

        // 设置同步状态
        subnet.syncing = true
        
        const response = await subnetApi.syncSubnetIPs(subnet.id)
        
        ElMessage.success({
          message: `IP地址同步完成！新增 ${response.stats.added} 个，删除 ${response.stats.removed} 个，保持 ${response.stats.kept} 个`,
          duration: 5000
        })
        
        // 刷新网段列表以显示最新的IP统计
        fetchSubnets()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('同步IP地址失败: ' + (error.response?.data?.detail || error.message))
        }
      } finally {
        // 清除同步状态
        subnet.syncing = false
      }
    }

    // 对话框成功回调
    const handleDialogSuccess = () => {
      fetchSubnets()
    }

    // 工具函数
    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString('zh-CN')
    }

    const getUsagePercentage = (subnet) => {
      if (!subnet.ip_count || subnet.ip_count === 0) return 0
      return Math.round((subnet.allocated_count / subnet.ip_count) * 100)
    }

    const getUsageColor = (subnet) => {
      const percentage = getUsagePercentage(subnet)
      if (percentage >= 90) return '#f56c6c'
      if (percentage >= 70) return '#e6a23c'
      return '#67c23a'
    }

    // 生命周期
    onMounted(() => {
      fetchSubnets()
    })

    return {
      // 图标
      Plus,
      Search,
      
      // 用户权限
      currentUser,
      userRole,
      isAdmin,
      
      // 数据
      loading,
      subnets,
      total,
      currentPage,
      pageSize,
      searchQuery,
      vlanFilter,
      
      // 对话框
      dialogVisible,
      detailDialogVisible,
      dialogMode,
      currentSubnet,
      
      // 方法
      fetchSubnets,
      handleSearch,
      handleVlanFilter,
      resetFilters,
      handleSizeChange,
      handleCurrentChange,
      handleSortChange,
      showCreateDialog,
      viewSubnet,
      editSubnet,
      deleteSubnet,
      syncSubnetIPs,
      handleDialogSuccess,
      formatDate,
      getUsagePercentage,
      getUsageColor
    }
  }
}
</script>

<style scoped>
.subnet-management {
  padding: 20px;
  background-color: var(--bg-color-page);
  color: var(--text-color-primary);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: var(--text-color-primary);
}

.search-section {
  margin-bottom: 20px;
  padding: 20px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--box-shadow);
}

.subnet-list {
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  box-shadow: var(--box-shadow);
  padding: 20px;
}

.ip-usage {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.usage-text {
  font-size: 12px;
  color: #606266;
  text-align: center;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}
</style>