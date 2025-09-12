<template>
  <div class="advanced-search">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchForm.query"
        placeholder="搜索IP地址、使用人、MAC地址、设备类型..."
        @input="handleRealTimeSearch"
        @keyup.enter="handleSearch"
        clearable
        class="search-input"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
        <template #suffix>
          <div class="search-actions">
            <el-button
              type="text"
              @click="showAdvancedFilters = !showAdvancedFilters"
              :class="{ active: showAdvancedFilters }"
            >
              <el-icon><Filter /></el-icon>
              高级筛选
            </el-button>
            <el-button
              type="text"
              @click="showSearchHistory = !showSearchHistory"
              :class="{ active: showSearchHistory }"
            >
              <el-icon><Clock /></el-icon>
              历史
            </el-button>
          </div>
        </template>
      </el-input>
      
      <el-button type="primary" @click="handleSearch" :loading="searching">
        搜索
      </el-button>
      
      <el-button @click="resetSearch">
        重置
      </el-button>
    </div>

    <!-- 快捷搜索标签 -->
    <div v-if="quickSearchTags.length > 0" class="quick-search-tags">
      <span class="tags-label">快捷搜索：</span>
      <el-tag
        v-for="tag in quickSearchTags"
        :key="tag.id"
        @click="applyQuickSearch(tag)"
        class="quick-tag"
        effect="plain"
      >
        <el-icon><Star /></el-icon>
        {{ tag.search_name || '未命名搜索' }}
      </el-tag>
    </div>

    <!-- 高级筛选面板 -->
    <el-collapse-transition>
      <div v-show="showAdvancedFilters" class="advanced-filters">
        <el-card>
          <template #header>
            <div class="filter-header">
              <span>高级筛选条件</span>
              <el-button type="text" @click="saveCurrentSearch">
                <el-icon><Collection /></el-icon>
                保存搜索
              </el-button>
            </div>
          </template>
          
          <el-form :model="searchForm" label-width="100px" class="filter-form">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="网段">
                  <el-select v-model="searchForm.subnet_id" placeholder="选择网段" clearable>
                    <el-option
                      v-for="subnet in subnets"
                      :key="subnet.id"
                      :label="subnet.network"
                      :value="subnet.id"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="状态">
                  <el-select v-model="searchForm.status" placeholder="选择状态" clearable>
                    <el-option label="可用" value="available" />
                    <el-option label="使用中" value="allocated" />
                    <el-option label="保留" value="reserved" />
                    <el-option label="冲突" value="conflict" />
                  </el-select>
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="设备类型">
                  <el-select v-model="searchForm.device_type" placeholder="选择设备类型" clearable>
                    <el-option
                      v-for="deviceType in availableDeviceTypes"
                      :key="deviceType.code"
                      :label="deviceType.name"
                      :value="deviceType.code"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="8">

              </el-col>
              
              <el-col :span="8">
                <el-form-item label="所属部门">
                  <el-input v-model="searchForm.assigned_to" placeholder="所属部门" clearable />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="使用人">
                  <el-input v-model="searchForm.user_name" placeholder="使用人" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="MAC地址">
                  <el-input v-model="searchForm.mac_address" placeholder="MAC地址" clearable />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="IP范围起始">
                  <el-input v-model="searchForm.ip_range_start" placeholder="如：192.168.1.1" clearable />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="IP范围结束">
                  <el-input v-model="searchForm.ip_range_end" placeholder="如：192.168.1.100" clearable />
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="分配日期起">
                  <el-date-picker
                    v-model="searchForm.allocated_date_start"
                    type="datetime"
                    placeholder="选择开始日期"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="分配日期止">
                  <el-date-picker
                    v-model="searchForm.allocated_date_end"
                    type="datetime"
                    placeholder="选择结束日期"
                    format="YYYY-MM-DD HH:mm:ss"
                    value-format="YYYY-MM-DDTHH:mm:ss"
                  />
                </el-form-item>
              </el-col>
              
              <el-col :span="8">
                <el-form-item label="标签">
                  <el-select
                    v-model="searchForm.tags"
                    multiple
                    placeholder="选择标签"
                    clearable
                    collapse-tags
                    collapse-tags-tooltip
                  >
                    <el-option
                      v-for="tag in availableTags"
                      :key="tag.id"
                      :label="tag.name"
                      :value="tag.id"
                    >
                      <span :style="{ color: tag.color }">● {{ tag.name }}</span>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <!-- 自定义字段搜索 -->
            <el-row v-if="customFields.length > 0" :gutter="20">
              <el-col :span="24">
                <el-divider content-position="left">自定义字段</el-divider>
              </el-col>
              
              <el-col
                v-for="field in customFields"
                :key="field.id"
                :span="8"
              >
                <el-form-item :label="field.field_name">
                  <!-- 文本类型 -->
                  <el-input
                    v-if="field.field_type === 'text'"
                    v-model="searchForm.custom_fields[field.id]"
                    :placeholder="`搜索${field.field_name}`"
                    clearable
                  />
                  
                  <!-- 数字类型 -->
                  <div v-else-if="field.field_type === 'number'" class="number-range">
                    <el-input-number
                      v-model="searchForm.custom_fields[field.id + '_min']"
                      :placeholder="`最小值`"
                      style="width: 48%"
                      size="small"
                    />
                    <span style="margin: 0 2%">-</span>
                    <el-input-number
                      v-model="searchForm.custom_fields[field.id + '_max']"
                      :placeholder="`最大值`"
                      style="width: 48%"
                      size="small"
                    />
                  </div>
                  
                  <!-- 日期类型 -->
                  <el-date-picker
                    v-else-if="field.field_type === 'date'"
                    v-model="searchForm.custom_fields[field.id]"
                    type="daterange"
                    range-separator="至"
                    start-placeholder="开始日期"
                    end-placeholder="结束日期"
                    format="YYYY-MM-DD"
                    value-format="YYYY-MM-DD"
                    style="width: 100%"
                  />
                  
                  <!-- 选择类型 -->
                  <el-select
                    v-else-if="field.field_type === 'select'"
                    v-model="searchForm.custom_fields[field.id]"
                    multiple
                    :placeholder="`选择${field.field_name}`"
                    clearable
                    collapse-tags
                  >
                    <el-option
                      v-for="option in field.field_options?.options || []"
                      :key="option"
                      :label="option"
                      :value="option"
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="排序方式">
                  <el-select v-model="searchForm.sort_by" placeholder="排序字段">
                    <el-option label="IP地址" value="ip_address" />
                    <el-option label="状态" value="status" />
                    <el-option label="使用人" value="user_name" />
                    <el-option label="分配时间" value="allocated_at" />
                    <el-option label="创建时间" value="created_at" />
                  </el-select>
                  <el-select v-model="searchForm.sort_order" placeholder="排序方向" style="margin-left: 10px; width: 100px;">
                    <el-option label="升序" value="asc" />
                    <el-option label="降序" value="desc" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </el-card>
      </div>
    </el-collapse-transition>

    <!-- 搜索历史面板 -->
    <el-collapse-transition>
      <div v-show="showSearchHistory" class="search-history">
        <el-card>
          <template #header>
            <div class="history-header">
              <span>搜索历史</span>
              <el-button type="text" @click="loadSearchHistory">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          
          <div class="history-tabs">
            <el-tabs v-model="historyActiveTab">
              <el-tab-pane label="最近搜索" name="recent">
                <div v-if="searchHistory.length === 0" class="empty-history">
                  <el-empty description="暂无搜索历史" />
                </div>
                <div v-else class="history-list">
                  <div
                    v-for="item in searchHistory"
                    :key="item.id"
                    class="history-item"
                    @click="applyHistorySearch(item)"
                  >
                    <div class="history-content">
                      <div class="history-name">
                        {{ item.search_name || '未命名搜索' }}
                      </div>
                      <div class="history-params">
                        {{ formatSearchParams(item.search_params) }}
                      </div>
                      <div class="history-meta">
                        <span>使用 {{ item.used_count }} 次</span>
                        <span>{{ formatDate(item.created_at) }}</span>
                      </div>
                    </div>
                    <div class="history-actions">
                      <el-button
                        type="text"
                        @click.stop="toggleFavorite(item)"
                        :class="{ favorite: item.is_favorite }"
                      >
                        <el-icon><Star /></el-icon>
                      </el-button>
                      <el-button
                        type="text"
                        @click.stop="editSearchName(item)"
                      >
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button
                        type="text"
                        @click.stop="deleteHistory(item)"
                        class="delete-btn"
                      >
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
              
              <el-tab-pane label="收藏搜索" name="favorites">
                <div v-if="favoriteSearches.length === 0" class="empty-history">
                  <el-empty description="暂无收藏搜索" />
                </div>
                <div v-else class="history-list">
                  <div
                    v-for="item in favoriteSearches"
                    :key="item.id"
                    class="history-item favorite-item"
                    @click="applyHistorySearch(item)"
                  >
                    <div class="history-content">
                      <div class="history-name">
                        <el-icon><Star /></el-icon>
                        {{ item.search_name || '未命名搜索' }}
                      </div>
                      <div class="history-params">
                        {{ formatSearchParams(item.search_params) }}
                      </div>
                      <div class="history-meta">
                        <span>使用 {{ item.used_count }} 次</span>
                      </div>
                    </div>
                    <div class="history-actions">
                      <el-button
                        type="text"
                        @click.stop="editSearchName(item)"
                      >
                        <el-icon><Edit /></el-icon>
                      </el-button>
                      <el-button
                        type="text"
                        @click.stop="toggleFavorite(item)"
                        class="unfavorite-btn"
                      >
                        <el-icon><Star /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-card>
      </div>
    </el-collapse-transition>

    <!-- 保存搜索对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存搜索"
      width="400px"
    >
      <el-form :model="saveForm" label-width="80px">
        <el-form-item label="搜索名称">
          <el-input
            v-model="saveForm.search_name"
            placeholder="为这个搜索起个名字"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="saveForm.is_favorite">
            添加到收藏
          </el-checkbox>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSaveDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmSaveSearch">保存</el-button>
      </template>
    </el-dialog>

    <!-- 编辑搜索名称对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑搜索名称"
      width="400px"
    >
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="搜索名称">
          <el-input
            v-model="editForm.search_name"
            placeholder="搜索名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmEditName">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Filter, Clock, Star, Collection, Refresh, 
  Edit, Delete 
} from '@element-plus/icons-vue'
import { ipAPI, subnetApi } from '@/api'
import customFieldsAPI from '@/api/customFields'
import { safeGetCustomFields } from '@/utils/customFieldsDebug'
import tagsAPI from '@/api/tags'
import { debounce } from '@/utils/debounce'

export default {
  name: 'AdvancedSearch',
  components: {
    Search, Filter, Clock, Star, Collection, Refresh, Edit, Delete
  },
  emits: ['search', 'reset'],
  setup(props, { emit }) {
    // 响应式数据
    const searching = ref(false)
    const showAdvancedFilters = ref(false)
    const showSearchHistory = ref(false)
    const showSaveDialog = ref(false)
    const showEditDialog = ref(false)
    const historyActiveTab = ref('recent')
    
    const subnets = ref([])
    const searchHistory = ref([])
    const favoriteSearches = ref([])
    const quickSearchTags = ref([])
    const availableTags = ref([])
    const customFields = ref([])
    const availableDeviceTypes = ref([])
    
    // 搜索表单
    const searchForm = reactive({
      query: '',
      subnet_id: null,
      status: null,
      device_type: null,
      location: '',
      assigned_to: '',
      user_name: '',
      mac_address: '',
      ip_range_start: '',
      ip_range_end: '',
      allocated_date_start: null,
      allocated_date_end: null,
      tags: [],
      custom_fields: {},
      sort_by: 'ip_address',
      sort_order: 'asc'
    })
    
    // 保存搜索表单
    const saveForm = reactive({
      search_name: '',
      is_favorite: false
    })
    
    // 编辑搜索表单
    const editForm = reactive({
      search_name: '',
      search_id: null
    })
    
    // 方法
    const loadSubnets = async () => {
      try {
        const response = await subnetApi.getSubnets()
        subnets.value = response.data || []
      } catch (error) {
        console.error('加载网段列表失败：', error)
      }
    }

    const loadTags = async () => {
      try {
        const response = await tagsAPI.getTags({ limit: 1000 })
        availableTags.value = response.data || []
      } catch (error) {
        console.error('加载标签列表失败：', error)
      }
    }

    const loadCustomFields = async () => {
      try {
        // 使用安全的自定义字段加载方法
        customFields.value = await safeGetCustomFields('ip')
      } catch (error) {
        console.error('加载自定义字段失败：', error)
        // 错误信息已在safeGetCustomFields中处理
      }
    }

    const loadDeviceTypes = async () => {
      try {
        // 从设备类型管理API获取设备类型列表
        const { getDeviceTypeOptions } = await import('@/api/deviceTypes')
        const response = await getDeviceTypeOptions()
        
        if (response && response.data && Array.isArray(response.data)) {
          // 处理API响应格式：response.data
          availableDeviceTypes.value = response.data.filter(type => type.status === 'active')
        } else if (response && Array.isArray(response)) {
          // 处理直接响应格式：response
          availableDeviceTypes.value = response.filter(type => type.status === 'active')
        } else {
          // 如果获取失败，使用静态列表作为备选
          availableDeviceTypes.value = [
            { code: 'server', name: '服务器' },
            { code: 'desktop', name: '台式机' },
            { code: 'laptop', name: '笔记本电脑' },
            { code: 'switch', name: '网络交换机' },
            { code: 'router', name: '路由器' },
            { code: 'printer', name: '打印机' },
            { code: 'firewall', name: '防火墙' },
            { code: 'other', name: '其他' }
          ]
        }
      } catch (error) {
        console.error('加载设备类型列表失败：', error)
        // 如果获取失败，使用静态列表，但不包含workstation
        availableDeviceTypes.value = [
          { code: 'server', name: '服务器' },
          { code: 'desktop', name: '台式机' },
          { code: 'laptop', name: '笔记本电脑' },
          { code: 'switch', name: '网络交换机' },
          { code: 'router', name: '路由器' },
          { code: 'printer', name: '打印机' },
          { code: 'firewall', name: '防火墙' },
          { code: 'other', name: '其他' }
        ]
      }
    }
    
    const loadSearchHistory = async () => {
      try {
        const [historyResponse, favoritesResponse] = await Promise.all([
          ipAPI.getSearchHistory(20),
          ipAPI.getSearchFavorites()
        ])
        
        searchHistory.value = historyResponse.data || []
        favoriteSearches.value = favoritesResponse.data || []
        
        // 更新快捷搜索标签（取前5个收藏搜索）
        quickSearchTags.value = favoriteSearches.value.slice(0, 5)
      } catch (error) {
        console.error('加载搜索历史失败：', error)
      }
    }
    
    const handleSearch = async () => {
      searching.value = true
      try {
        // 清理空值
        const searchParams = {}
        Object.keys(searchForm).forEach(key => {
          const value = searchForm[key]
          if (value !== null && value !== '' && value !== undefined) {
            if (Array.isArray(value) && value.length === 0) return
            searchParams[key] = value
          }
        })
        
        // 发送搜索事件
        emit('search', searchParams)
        
        // 如果有搜索条件，保存到历史记录
        if (Object.keys(searchParams).length > 0) {
          await saveToHistory(searchParams)
        }
      } catch (error) {
        ElMessage.error('搜索失败：' + error.message)
      } finally {
        searching.value = false
      }
    }
    
    const handleRealTimeSearch = debounce(() => {
      if (searchForm.query && searchForm.query.length >= 2) {
        handleSearch()
      }
    }, 500)
    
    const resetSearch = () => {
      Object.keys(searchForm).forEach(key => {
        if (Array.isArray(searchForm[key])) {
          searchForm[key] = []
        } else if (typeof searchForm[key] === 'boolean') {
          searchForm[key] = false
        } else {
          searchForm[key] = key === 'sort_by' ? 'ip_address' : 
                           key === 'sort_order' ? 'asc' : 
                           null
        }
      })
      
      emit('reset')
    }
    
    const saveToHistory = async (searchParams) => {
      try {
        await ipAPI.saveSearchHistory({
          search_params: searchParams
        })
      } catch (error) {
        console.error('保存搜索历史失败：', error)
      }
    }
    
    const saveCurrentSearch = () => {
      // 检查是否有搜索条件
      const hasSearchParams = Object.keys(searchForm).some(key => {
        const value = searchForm[key]
        return value !== null && value !== '' && value !== undefined && 
               !(Array.isArray(value) && value.length === 0)
      })
      
      if (!hasSearchParams) {
        ElMessage.warning('请先设置搜索条件')
        return
      }
      
      saveForm.search_name = ''
      saveForm.is_favorite = false
      showSaveDialog.value = true
    }
    
    const confirmSaveSearch = async () => {
      try {
        const searchParams = {}
        Object.keys(searchForm).forEach(key => {
          const value = searchForm[key]
          if (value !== null && value !== '' && value !== undefined) {
            if (Array.isArray(value) && value.length === 0) return
            searchParams[key] = value
          }
        })
        
        await ipAPI.saveSearchHistory({
          search_name: saveForm.search_name || null,
          search_params: searchParams,
          is_favorite: saveForm.is_favorite
        })
        
        ElMessage.success('搜索保存成功')
        showSaveDialog.value = false
        loadSearchHistory()
      } catch (error) {
        ElMessage.error('保存搜索失败：' + error.message)
      }
    }
    
    const applyHistorySearch = (historyItem) => {
      // 应用历史搜索参数
      Object.keys(searchForm).forEach(key => {
        searchForm[key] = historyItem.search_params[key] || 
                         (key === 'sort_by' ? 'ip_address' : 
                          key === 'sort_order' ? 'asc' : 
                          Array.isArray(searchForm[key]) ? [] : null)
      })
      
      // 执行搜索
      handleSearch()
      
      // 关闭历史面板
      showSearchHistory.value = false
    }
    
    const applyQuickSearch = (quickSearch) => {
      applyHistorySearch(quickSearch)
    }
    
    const toggleFavorite = async (item) => {
      try {
        const response = await ipAPI.toggleSearchFavorite(item.id)
        item.is_favorite = response.data.is_favorite
        
        ElMessage.success(response.data.message)
        loadSearchHistory()
      } catch (error) {
        ElMessage.error('操作失败：' + error.message)
      }
    }
    
    const editSearchName = (item) => {
      editForm.search_name = item.search_name || ''
      editForm.search_id = item.id
      showEditDialog.value = true
    }
    
    const confirmEditName = async () => {
      try {
        await ipAPI.updateSearchName(editForm.search_id, editForm.search_name)
        ElMessage.success('搜索名称更新成功')
        showEditDialog.value = false
        loadSearchHistory()
      } catch (error) {
        ElMessage.error('更新失败：' + error.message)
      }
    }
    
    const deleteHistory = async (item) => {
      try {
        await ElMessageBox.confirm(
          '确定要删除这个搜索历史吗？',
          '确认删除',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        await ipAPI.deleteSearchHistory(item.id)
        ElMessage.success('删除成功')
        loadSearchHistory()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败：' + error.message)
        }
      }
    }
    
    const formatSearchParams = (params) => {
      const conditions = []
      
      if (params.query) conditions.push(`关键词: ${params.query}`)
      if (params.status) conditions.push(`状态: ${params.status}`)
      if (params.device_type) conditions.push(`设备类型: ${params.device_type}`)

      
      return conditions.length > 0 ? conditions.join(', ') : '无特定条件'
    }
    
    const formatDate = (dateString) => {
      if (!dateString) return ''
      return new Date(dateString).toLocaleString('zh-CN')
    }
    
    // 生命周期
    onMounted(() => {
      loadSubnets()
      loadSearchHistory()
      loadTags()
      loadCustomFields()
      loadDeviceTypes()
    })
    
    // 监听搜索历史面板显示状态
    watch(showSearchHistory, (newVal) => {
      if (newVal) {
        loadSearchHistory()
      }
    })
    
    return {
      // 响应式数据
      searching,
      showAdvancedFilters,
      showSearchHistory,
      showSaveDialog,
      showEditDialog,
      historyActiveTab,
      subnets,
      searchHistory,
      favoriteSearches,
      quickSearchTags,
      availableTags,
      customFields,
      availableDeviceTypes,
      searchForm,
      saveForm,
      editForm,
      
      // 方法
      handleSearch,
      handleRealTimeSearch,
      resetSearch,
      saveCurrentSearch,
      confirmSaveSearch,
      applyHistorySearch,
      applyQuickSearch,
      toggleFavorite,
      editSearchName,
      confirmEditName,
      deleteHistory,
      loadSearchHistory,
      formatSearchParams,
      formatDate
    }
  }
}
</script>

<style scoped>
.advanced-search {
  margin-bottom: 20px;
  background-color: var(--bg-primary-page);
  color: var(--text-primary);
}

.search-bar {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 15px;
}

.search-input {
  flex: 1;
}

.search-actions {
  display: flex;
  gap: 5px;
}

.search-actions .el-button.active {
  color: var(--primary) !important;
}

.quick-search-tags {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.tags-label {
  color: var(--text-tertiary);
  font-size: 14px;
}

.quick-tag {
  cursor: pointer;
  transition: all 0.3s;
  background-color: var(--fill-primary) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-secondary) !important;
}

.quick-tag:hover {
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #ffffff !important;
}

.advanced-filters {
  margin-bottom: 15px;
}

.advanced-filters .el-card {
  background-color: var(--bg-primary) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-primary) !important;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-primary);
}

.filter-form .el-form-item {
  margin-bottom: 15px;
}

.search-history {
  margin-bottom: 15px;
}

.search-history .el-card {
  background-color: var(--bg-primary) !important;
  border-color: var(--border-primary) !important;
  color: var(--text-primary) !important;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-primary);
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border-primary-lighter);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background-color: var(--bg-primary);
  color: var(--text-primary);
}

.history-item:hover {
  background-color: var(--fill-primary) !important;
  border-color: var(--primary) !important;
}

.favorite-item {
  border-color: var(--danger) !important;
  background-color: var(--fill-primary-light) !important;
}

.history-content {
  flex: 1;
}

.history-name {
  font-weight: 500;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text-primary);
}

.history-params {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-bottom: 4px;
}

.history-meta {
  font-size: 11px;
  color: var(--text-quaternary);
  display: flex;
  gap: 15px;
}

.history-actions {
  display: flex;
  gap: 5px;
}

.history-actions .el-button.favorite {
  color: var(--danger) !important;
}

.history-actions .el-button.unfavorite-btn {
  color: var(--danger) !important;
}

.history-actions .el-button.delete-btn {
  color: var(--danger) !important;
}

.empty-history {
  text-align: center;
  padding: 40px 0;
  color: var(--text-tertiary);
}

.history-tabs .el-tabs__content {
  padding-top: 15px;
}

.number-range {
  display: flex;
  align-items: center;
  gap: 2%;
}
</style>