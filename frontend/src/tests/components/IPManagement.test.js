/**
 * IP地址管理组件测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import IPManagement from '@/views/IPManagement.vue'

// Mock API calls
const mockApi = {
  getIPs: vi.fn(),
  allocateIP: vi.fn(),
  reserveIP: vi.fn(),
  releaseIP: vi.fn(),
  searchIPs: vi.fn(),
  conflictCheck: vi.fn()
}

vi.mock('@/api/ip', () => ({
  getIPs: (...args) => mockApi.getIPs(...args),
  allocateIP: (...args) => mockApi.allocateIP(...args),
  reserveIP: (...args) => mockApi.reserveIP(...args),
  releaseIP: (...args) => mockApi.releaseIP(...args),
  searchIPs: (...args) => mockApi.searchIPs(...args),
  conflictCheck: (...args) => mockApi.conflictCheck(...args)
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(),
    prompt: vi.fn()
  }
}))

describe('IPManagement.vue', () => {
  let wrapper
  let store

  const mockIPData = {
    items: [
      {
        id: 1,
        ip_address: '192.168.1.10',
        subnet_id: 1,
        status: 'allocated',
        mac_address: '00:11:22:33:44:55',
        hostname: 'server-01',
        device_type: 'Server',
        location: 'Building A',
        assigned_to: 'IT Department',
        description: 'Web Server',
        allocated_at: '2023-01-01T10:00:00Z',
        allocated_by: 1
      },
      {
        id: 2,
        ip_address: '192.168.1.11',
        subnet_id: 1,
        status: 'available',
        mac_address: null,
        hostname: null,
        device_type: null,
        location: null,
        assigned_to: null,
        description: null,
        allocated_at: null,
        allocated_by: null
      },
      {
        id: 3,
        ip_address: '192.168.1.12',
        subnet_id: 1,
        status: 'reserved',
        mac_address: null,
        hostname: 'reserved-ip',
        device_type: null,
        location: 'Building A',
        assigned_to: 'Network Team',
        description: 'Reserved for future use',
        allocated_at: null,
        allocated_by: null
      }
    ],
    total: 3,
    page: 1,
    size: 50
  }

  beforeEach(() => {
    vi.clearAllMocks()
    
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

    mockApi.getIPs.mockResolvedValue({ data: mockIPData })
    mockApi.conflictCheck.mockResolvedValue({ data: { conflicts: [] } })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  describe('组件渲染', () => {
    it('应该正确渲染IP管理页面', async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(wrapper.find('.ip-management').exists()).toBe(true)
      expect(wrapper.find('.ip-list').exists()).toBe(true)
      expect(mockApi.getIPs).toHaveBeenCalled()
    })

    it('应该显示IP地址列表数据', async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      const ipItems = wrapper.findAll('.ip-item')
      expect(ipItems).toHaveLength(3)
      expect(wrapper.text()).toContain('192.168.1.10')
      expect(wrapper.text()).toContain('192.168.1.11')
      expect(wrapper.text()).toContain('192.168.1.12')
    })

    it('应该显示不同的IP状态', async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(wrapper.text()).toContain('已分配')
      expect(wrapper.text()).toContain('可用')
      expect(wrapper.text()).toContain('保留')
    })
  })

  describe('IP地址分配', () => {
    beforeEach(async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该打开分配IP对话框', async () => {
      const allocateBtn = wrapper.find('.allocate-ip-btn')
      await allocateBtn.trigger('click')

      expect(wrapper.find('.allocate-dialog').exists()).toBe(true)
      expect(wrapper.find('.dialog-title').text()).toContain('分配IP地址')
    })

    it('应该成功分配IP地址', async () => {
      const allocationData = {
        ip_address: '192.168.1.11',
        mac_address: '00:11:22:33:44:66',
        hostname: 'new-server',
        device_type: 'Server',
        assigned_to: 'Development Team',
        description: 'Development Server'
      }

      mockApi.allocateIP.mockResolvedValue({ 
        data: { 
          id: 2, 
          status: 'allocated',
          ...allocationData 
        } 
      })

      const allocateBtn = wrapper.find('.allocate-ip-btn')
      await allocateBtn.trigger('click')

      // 填写分配表单
      await wrapper.find('input[name="mac_address"]').setValue(allocationData.mac_address)
      await wrapper.find('input[name="hostname"]').setValue(allocationData.hostname)
      await wrapper.find('select[name="device_type"]').setValue(allocationData.device_type)
      await wrapper.find('input[name="assigned_to"]').setValue(allocationData.assigned_to)
      await wrapper.find('textarea[name="description"]').setValue(allocationData.description)

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(mockApi.allocateIP).toHaveBeenCalledWith('192.168.1.11', expect.objectContaining({
        mac_address: allocationData.mac_address,
        hostname: allocationData.hostname,
        device_type: allocationData.device_type,
        assigned_to: allocationData.assigned_to,
        description: allocationData.description
      }))
      expect(ElMessage.success).toHaveBeenCalledWith('IP地址分配成功')
    })

    it('应该处理分配失败的情况', async () => {
      mockApi.allocateIP.mockRejectedValue(new Error('IP地址已被分配'))

      const allocateBtn = wrapper.find('.allocate-ip-btn')
      await allocateBtn.trigger('click')

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('分配失败: IP地址已被分配')
    })
  })

  describe('IP地址保留', () => {
    beforeEach(async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该成功保留IP地址', async () => {
      ElMessageBox.prompt.mockResolvedValue({ value: '为未来项目保留' })
      mockApi.reserveIP.mockResolvedValue({ 
        data: { 
          id: 2, 
          status: 'reserved',
          description: '为未来项目保留'
        } 
      })

      const reserveBtn = wrapper.find('.reserve-ip-btn')
      await reserveBtn.trigger('click')
      await flushPromises()

      expect(ElMessageBox.prompt).toHaveBeenCalledWith(
        '请输入保留原因：',
        '保留IP地址',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消'
        })
      )
      expect(mockApi.reserveIP).toHaveBeenCalledWith('192.168.1.11', '为未来项目保留')
      expect(ElMessage.success).toHaveBeenCalledWith('IP地址保留成功')
    })

    it('应该处理用户取消保留', async () => {
      ElMessageBox.prompt.mockRejectedValue('cancel')

      const reserveBtn = wrapper.find('.reserve-ip-btn')
      await reserveBtn.trigger('click')
      await flushPromises()

      expect(mockApi.reserveIP).not.toHaveBeenCalled()
    })
  })

  describe('IP地址释放', () => {
    beforeEach(async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该显示释放确认对话框', async () => {
      const releaseBtn = wrapper.find('.release-ip-btn')
      await releaseBtn.trigger('click')

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要释放这个IP地址吗？释放后该IP地址将变为可用状态。',
        '确认释放',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    it('应该成功释放IP地址', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.releaseIP.mockResolvedValue({ 
        data: { 
          id: 1, 
          status: 'available',
          mac_address: null,
          hostname: null,
          assigned_to: null
        } 
      })

      const releaseBtn = wrapper.find('.release-ip-btn')
      await releaseBtn.trigger('click')
      await flushPromises()

      expect(mockApi.releaseIP).toHaveBeenCalledWith('192.168.1.10')
      expect(ElMessage.success).toHaveBeenCalledWith('IP地址释放成功')
    })
  })

  describe('搜索和过滤功能', () => {
    beforeEach(async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该支持按IP地址搜索', async () => {
      const searchInput = wrapper.find('.search-input')
      await searchInput.setValue('192.168.1.10')
      await searchInput.trigger('input')

      // 等待防抖
      await new Promise(resolve => setTimeout(resolve, 350))
      await flushPromises()

      expect(mockApi.searchIPs).toHaveBeenCalledWith(expect.objectContaining({
        query: '192.168.1.10'
      }))
    })

    it('应该支持按状态过滤', async () => {
      const statusFilter = wrapper.find('.status-filter')
      await statusFilter.setValue('allocated')
      await statusFilter.trigger('change')

      expect(mockApi.getIPs).toHaveBeenCalledWith(expect.objectContaining({
        status: 'allocated'
      }))
    })

    it('应该支持按设备类型过滤', async () => {
      const deviceFilter = wrapper.find('.device-filter')
      await deviceFilter.setValue('Server')
      await deviceFilter.trigger('change')

      expect(mockApi.getIPs).toHaveBeenCalledWith(expect.objectContaining({
        device_type: 'Server'
      }))
    })

    it('应该支持按主机名搜索', async () => {
      const searchInput = wrapper.find('.search-input')
      await searchInput.setValue('server-01')
      await searchInput.trigger('input')

      await new Promise(resolve => setTimeout(resolve, 350))
      await flushPromises()

      expect(mockApi.searchIPs).toHaveBeenCalledWith(expect.objectContaining({
        query: 'server-01'
      }))
    })
  })



  describe('冲突检测', () => {
    beforeEach(async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该执行冲突检测', async () => {
      mockApi.conflictCheck.mockResolvedValue({
        data: {
          conflicts: [
            {
              ip_address: '192.168.1.10',
              mac_address: '00:11:22:33:44:55',
              detected_mac: '00:11:22:33:44:77',
              last_seen: '2023-01-03T09:00:00Z'
            }
          ]
        }
      })

      const conflictBtn = wrapper.find('.conflict-check-btn')
      await conflictBtn.trigger('click')
      await flushPromises()

      expect(mockApi.conflictCheck).toHaveBeenCalled()
      expect(wrapper.find('.conflict-results').exists()).toBe(true)
      expect(wrapper.text()).toContain('发现冲突')
    })

    it('应该显示无冲突结果', async () => {
      mockApi.conflictCheck.mockResolvedValue({
        data: { conflicts: [] }
      })

      const conflictBtn = wrapper.find('.conflict-check-btn')
      await conflictBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.success).toHaveBeenCalledWith('未发现IP地址冲突')
    })
  })

  describe('批量操作', () => {
    beforeEach(async () => {
      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()
    })

    it('应该支持批量选择IP地址', async () => {
      const checkboxes = wrapper.findAll('.ip-checkbox')
      await checkboxes[0].setChecked(true)
      await checkboxes[1].setChecked(true)

      expect(wrapper.find('.batch-actions').exists()).toBe(true)
      expect(wrapper.text()).toContain('已选择 2 个IP地址')
    })

    it('应该支持批量释放IP地址', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')
      mockApi.releaseIP.mockResolvedValue({ data: { success: true } })

      const checkboxes = wrapper.findAll('.ip-checkbox')
      await checkboxes[0].setChecked(true)

      const batchReleaseBtn = wrapper.find('.batch-release-btn')
      await batchReleaseBtn.trigger('click')
      await flushPromises()

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要批量释放选中的IP地址吗？',
        '批量释放',
        expect.objectContaining({
          type: 'warning'
        })
      )
    })
  })

  describe('错误处理', () => {
    it('应该处理网络请求失败', async () => {
      mockApi.getIPs.mockRejectedValue(new Error('网络错误'))

      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('加载IP地址列表失败: 网络错误')
    })

    it('应该处理权限不足的情况', async () => {
      mockApi.getIPs.mockRejectedValue({ response: { status: 403 } })

      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })

      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('权限不足，无法访问IP管理')
    })

    it('应该处理分配冲突', async () => {
      mockApi.allocateIP.mockRejectedValue({ 
        response: { 
          status: 409, 
          data: { message: 'MAC地址已存在' } 
        } 
      })

      wrapper = mount(IPManagement, {
        global: {
          plugins: [store]
        }
      })
      await flushPromises()

      const allocateBtn = wrapper.find('.allocate-ip-btn')
      await allocateBtn.trigger('click')

      const submitBtn = wrapper.find('.submit-btn')
      await submitBtn.trigger('click')
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalledWith('分配失败: MAC地址已存在')
    })
  })
})