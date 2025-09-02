/**
 * 网段管理组件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import SubnetManagement from '@/views/SubnetManagement.vue'

// Mock API calls
const mockApi = {
  getSubnets: vi.fn(),
  createSubnet: vi.fn(),
  updateSubnet: vi.fn(),
  deleteSubnet: vi.fn(),
  getSubnetIPs: vi.fn(),
  validateSubnet: vi.fn()
}

vi.mock('@/api/subnet', () => ({
  getSubnets: (...args) => mockApi.getSubnets(...args),
  createSubnet: (...args) => mockApi.createSubnet(...args),
  updateSubnet: (...args) => mockApi.updateSubnet(...args),
  deleteSubnet: (...args) => mockApi.deleteSubnet(...args),
  getSubnetIPs: (...args) => mockApi.getSubnetIPs(...args),
  validateSubnet: (...args) => mockApi.validateSubnet(...args)
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('SubnetManagement.vue', () => {
  let wrapper
  let store

  const mockSubnetData = {
    items: [
      {
        id: 1,
        network: '192.168.1.0/24',
        netmask: '255.255.255.0',
        gateway: '192.168.1.1',
        description: 'Development Network',
        vlan_id: 100,
        location: 'Building A',
        created_at: '2023-01-01T00:00:00Z',
        ip_count: 254,
        allocated_count: 50,
        utilization_rate: 19.69
      },
      {
        id: 2,
        network: '10.0.0.0/16',
        netmask: '255.255.0.0',
        gateway: '10.0.0.1',
        description: 'Production Network',
        vlan_id: 200,
        location: 'Building B',
        created_at: '2023-01-02T00:00:00Z',
        ip_count: 65534,
        allocated_count: 1000,
        utilization_rate: 1.53
      }
    ],
    total: 2,
    page: 1,
    size: 10
  }

  beforeEach(() => {
    // 重置所有mock
    vi.clearAllMocks()
    
    // 创建Vuex store
    store = createStore({
      modules: {
        auth: {
          namespaced: true,
          state: {
            user: { id: 1, username: 'admin', role: 'admin' }
          },
          getters: {
            currentUser: state => state.user
          }
        }
      }
    })

    // 设置默认的API mock返回值
    mockApi.getSubnets.mockResolvedValue({ data: mockSubnetData })
    mockApi.validateSubnet.mockResolvedValue({ data: { valid: true } })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('组件渲染', () => {
    it('应该正确渲染网段管理页面', async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(wrapper.find('.subnet-management').exists()).toBe(true)
      expect(wrapper.find('.subnet-list').exists()).toBe(true)
      expect(mockApi.getSubnets).toHaveBeenCalled()
    })

    it('应该显示网段列表数据', async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      const subnetItems = wrapper.findAll('.subnet-item')
      expect(subnetItems).toHaveLength(2)
      expect(wrapper.text()).toContain('192.168.1.0/24')
      expect(wrapper.text()).toContain('10.0.0.0/16')
    })

    it('应该显示加载状态', () => {
      mockApi.getSubnets.mockImplementation(() => new Promise(() => {}))
      
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })

      expect(wrapper.find('.loading').exists()).toBe(true)
    })
  })

  describe('网段创建', () => {
    beforeEach(async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该打开创建网段对话框', async () => {
      const createBtn = wrapper.find('.create-subnet-btn')
      await createBtn.trigger('click')

      expect(wrapper.find('.subnet-dialog').exists()).toBe(true)
      expect(wrapper.find('.dialog-title').text()).toContain('创建网段')
    })

    it('应该验证网段格式', async () => {
      const createBtn = wrapper.find('.create-subnet-btn')
      await createBtn.trigger('click')

      const networkInput = wrapper.find('input[name="network"]')
      await networkInput.setValue('invalid-network')
      await networkInput.trigger('blur')

      expect(mockApi.validateSubnet).toHaveBeenCalledWith('invalid-network')
    })

    it('应该成功创建网段', async () => {
      const newSubnet = {
        network: '172.16.0.0/16',
        netmask: '255.255.0.0',
        gateway: '172.16.0.1',
        description: 'Test Network',
        vlan_id: 300,
        location: 'Test Location'
      }

      mockApi.createSubnet.mockResolvedValue({ data: { id: 3, ...newSubnet } })

      const createBtn = wrapper.find('.create-subnet-btn')
      await createBtn.trigger('click')

      // 填写表单
      await wrapper.find('input[name="network"]').setValue(newSubnet.network)
      await wrapper.find('input[name="gateway"]').setValue(newSubnet.gateway)
      await wrapper.find('input[name="description"]').setValue(newSubnet.description)
      await wrapper.find('input[name="vlan_id"]').setValue(newSubnet.vlan_id)
      await wrapper.find('input[name="location"]').setValue(newSubnet.location)

      // 提交表单
      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockApi.createSubnet).toHaveBeenCalledWith(newSubnet)
      expect(ElMessage.success).toHaveBeenCalledWith('网段创建成功')
      expect(mockApi.getSubnets).toHaveBeenCalledTimes(2) // 初始加载 + 创建后刷新
    })

    it('应该处理创建失败的情况', async () => {
      mockApi.createSubnet.mockRejectedValue(new Error('网段重叠'))

      const createBtn = wrapper.find('.create-subnet-btn')
      await createBtn.trigger('click')

      // 填写表单并提交
      await wrapper.find('input[name="network"]').setValue('192.168.1.0/24')
      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('创建失败: 网段重叠')
    })
  })

  describe('网段编辑', () => {
    beforeEach(async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该打开编辑网段对话框', async () => {
      const editBtn = wrapper.find('.edit-subnet-btn')
      await editBtn.trigger('click')

      expect(wrapper.find('.subnet-dialog').exists()).toBe(true)
      expect(wrapper.find('.dialog-title').text()).toContain('编辑网段')
    })

    it('应该预填充现有网段数据', async () => {
      const editBtn = wrapper.find('.edit-subnet-btn')
      await editBtn.trigger('click')

      expect(wrapper.find('input[name="network"]').element.value).toBe('192.168.1.0/24')
      expect(wrapper.find('input[name="gateway"]').element.value).toBe('192.168.1.1')
      expect(wrapper.find('input[name="description"]').element.value).toBe('Development Network')
    })

    it('应该成功更新网段', async () => {
      const updatedSubnet = {
        id: 1,
        network: '192.168.1.0/24',
        gateway: '192.168.1.254',
        description: 'Updated Development Network',
        vlan_id: 101,
        location: 'Building A - Floor 2'
      }

      mockApi.updateSubnet.mockResolvedValue({ data: updatedSubnet })

      const editBtn = wrapper.find('.edit-subnet-btn')
      await editBtn.trigger('click')

      // 修改表单数据
      await wrapper.find('input[name="gateway"]').setValue(updatedSubnet.gateway)
      await wrapper.find('input[name="description"]').setValue(updatedSubnet.description)

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockApi.updateSubnet).toHaveBeenCalledWith(1, expect.objectContaining({
        gateway: updatedSubnet.gateway,
        description: updatedSubnet.description
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('网段更新成功')
    })
  })

  describe('网段删除', () => {
    beforeEach(async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该显示删除确认对话框', async () => {
      const deleteBtn = wrapper.find('.delete-subnet-btn')
      await deleteBtn.trigger('click')

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除这个网段吗？删除后该网段下的所有IP地址也将被清理。',
        '确认删除',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    it('应该成功删除网段', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.deleteSubnet.mockResolvedValue({ data: { success: true } })

      const deleteBtn = wrapper.find('.delete-subnet-btn')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(mockApi.deleteSubnet).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('网段删除成功')
      expect(mockApi.getSubnets).toHaveBeenCalledTimes(2) // 初始加载 + 删除后刷新
    })

    it('应该处理删除失败的情况', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.deleteSubnet.mockRejectedValue(new Error('网段下存在已分配的IP地址'))

      const deleteBtn = wrapper.find('.delete-subnet-btn')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('删除失败: 网段下存在已分配的IP地址')
    })

    it('应该处理用户取消删除', async () => {
      ElMessageBox.confirm.mockRejectedValue('cancel')

      const deleteBtn = wrapper.find('.delete-subnet-btn')
      await deleteBtn.trigger('click')
      await flushPromises()

      expect(mockApi.deleteSubnet).not.toHaveBeenCalled()
    })
  })

  describe('搜索和过滤', () => {
    beforeEach(async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该支持按网段搜索', async () => {
      const searchInput = wrapper.find('.search-input')
      await searchInput.setValue('192.168')
      await searchInput.trigger('input')

      // 等待防抖
      await new Promise(resolve => setTimeout(resolve, 350))
      await flushPromises()

      expect(mockApi.getSubnets).toHaveBeenCalledWith(expect.objectContaining({
        search: '192.168'
      }))
    })

    it('应该支持按位置过滤', async () => {
      const locationFilter = wrapper.find('.location-filter')
      await locationFilter.setValue('Building A')
      await locationFilter.trigger('change')

      expect(mockApi.getSubnets).toHaveBeenCalledWith(expect.objectContaining({
        location: 'Building A'
      }))
    })

    it('应该支持按VLAN ID过滤', async () => {
      const vlanFilter = wrapper.find('.vlan-filter')
      await vlanFilter.setValue('100')
      await vlanFilter.trigger('change')

      expect(mockApi.getSubnets).toHaveBeenCalledWith(expect.objectContaining({
        vlan_id: '100'
      }))
    })
  })

  describe('分页功能', () => {
    beforeEach(async () => {
      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该显示分页组件', () => {
      expect(wrapper.find('.pagination').exists()).toBe(true)
    })

    it('应该处理页面切换', async () => {
      const nextPageBtn = wrapper.find('.next-page-btn')
      await nextPageBtn.trigger('click')

      expect(mockApi.getSubnets).toHaveBeenCalledWith(expect.objectContaining({
        page: 2
      }))
    })

    it('应该处理每页大小变更', async () => {
      const pageSizeSelect = wrapper.find('.page-size-select')
      await pageSizeSelect.setValue('20')
      await pageSizeSelect.trigger('change')

      expect(mockApi.getSubnets).toHaveBeenCalledWith(expect.objectContaining({
        size: 20,
        page: 1
      }))
    })
  })

  describe('网段详情查看', () => {
    beforeEach(async () => {
      mockApi.getSubnetIPs.mockResolvedValue({
        data: {
          items: [
            {
              id: 1,
              ip_address: '192.168.1.1',
              status: 'allocated',
              hostname: 'gateway',
              mac_address: '00:11:22:33:44:55'
            }
          ],
          total: 1
        }
      })

      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该打开网段详情对话框', async () => {
      const detailBtn = wrapper.find('.view-detail-btn')
      await detailBtn.trigger('click')

      expect(wrapper.find('.subnet-detail-dialog').exists()).toBe(true)
      expect(mockApi.getSubnetIPs).toHaveBeenCalledWith(1)
    })

    it('应该显示网段下的IP地址列表', async () => {
      const detailBtn = wrapper.find('.view-detail-btn')
      await detailBtn.trigger('click')
      await flushPromises()

      expect(wrapper.find('.ip-list').exists()).toBe(true)
      expect(wrapper.text()).toContain('192.168.1.1')
      expect(wrapper.text()).toContain('gateway')
    })
  })

  describe('错误处理', () => {
    it('应该处理网络请求失败', async () => {
      mockApi.getSubnets.mockRejectedValue(new Error('网络错误'))

      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载网段列表失败: 网络错误')
    })

    it('应该处理权限不足的情况', async () => {
      mockApi.getSubnets.mockRejectedValue({ response: { status: 403 } })

      wrapper = mount(SubnetManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('权限不足，无法访问网段管理')
    })
  })
})
      