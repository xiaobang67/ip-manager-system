/**
 * 监控仪表盘组件单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import MonitoringDashboard from '@/components/MonitoringDashboard.vue'
import * as monitoringAPI from '@/api/monitoring'

// Mock ECharts
vi.mock('echarts', () => ({
  init: vi.fn(() => ({
    setOption: vi.fn(),
    resize: vi.fn(),
    dispose: vi.fn()
  }))
}))

// Mock Element Plus Message
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      info: vi.fn()
    }
  }
})

// Mock API calls
vi.mock('@/api/monitoring', () => ({
  getDashboardSummary: vi.fn(),
  getTopUtilizedSubnets: vi.fn(),
  getAllocationTrends: vi.fn(),
  getAlertHistory: vi.fn(),
  resolveAlert: vi.fn()
}))

describe('MonitoringDashboard', () => {
  let wrapper

  const mockDashboardData = {
    ip_statistics: {
      total_ips: 1000,
      allocated_ips: 750,
      reserved_ips: 50,
      available_ips: 180,
      conflict_ips: 20,
      utilization_rate: 80.0,
      allocation_rate: 75.0,
      reservation_rate: 5.0
    },
    alert_statistics: {
      active_rules: 5,
      recent_alerts: 10,
      unresolved_alerts: 3,
      severity_breakdown: {
        low: 2,
        medium: 5,
        high: 2,
        critical: 1
      }
    },
    total_subnets: 25,
    total_users: 15,
    recent_allocations_24h: 12,
    timestamp: '2023-01-01T10:00:00Z'
  }

  const mockSubnetData = [
    {
      subnet_id: 1,
      network: '192.168.1.0/24',
      description: 'Main Office Network',
      vlan_id: 100,
      location: 'Office Building A',
      total_ips: 254,
      allocated_ips: 200,
      reserved_ips: 10,
      available_ips: 44,
      conflict_ips: 0,
      utilization_rate: 82.68,
      created_at: '2023-01-01T00:00:00Z'
    },
    {
      subnet_id: 2,
      network: '192.168.2.0/24',
      description: 'Guest Network',
      vlan_id: 200,
      location: 'Office Building B',
      total_ips: 254,
      allocated_ips: 50,
      reserved_ips: 5,
      available_ips: 199,
      conflict_ips: 0,
      utilization_rate: 21.65,
      created_at: '2023-01-01T00:00:00Z'
    }
  ]

  const mockTrendData = [
    { date: '2023-01-01', allocations: 10 },
    { date: '2023-01-02', allocations: 15 },
    { date: '2023-01-03', allocations: 8 }
  ]

  const mockAlertData = [
    {
      id: 1,
      alert_message: 'High utilization in subnet 192.168.1.0/24',
      severity: 'high',
      is_resolved: false,
      created_at: '2023-01-01T10:00:00Z'
    },
    {
      id: 2,
      alert_message: 'IP conflict detected',
      severity: 'critical',
      is_resolved: true,
      created_at: '2023-01-01T09:00:00Z'
    }
  ]

  beforeEach(() => {
    // Setup API mocks
    vi.mocked(monitoringAPI.getDashboardSummary).mockResolvedValue({
      data: mockDashboardData
    })
    vi.mocked(monitoringAPI.getTopUtilizedSubnets).mockResolvedValue({
      data: mockSubnetData
    })
    vi.mocked(monitoringAPI.getAllocationTrends).mockResolvedValue({
      data: mockTrendData
    })
    vi.mocked(monitoringAPI.getAlertHistory).mockResolvedValue({
      data: mockAlertData
    })
    vi.mocked(monitoringAPI.resolveAlert).mockResolvedValue({})

    // Clear all mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('should render dashboard with correct structure', () => {
    wrapper = mount(MonitoringDashboard)

    // Check if main sections are rendered
    expect(wrapper.find('.monitoring-dashboard').exists()).toBe(true)
    expect(wrapper.find('.stats-cards').exists()).toBe(true)
    expect(wrapper.find('.charts-section').exists()).toBe(true)
    expect(wrapper.find('.table-section').exists()).toBe(true)
    expect(wrapper.find('.alerts-section').exists()).toBe(true)
  })

  it('should load dashboard data on mount', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for async operations
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Check if API calls were made
    expect(monitoringAPI.getDashboardSummary).toHaveBeenCalledOnce()
    expect(monitoringAPI.getTopUtilizedSubnets).toHaveBeenCalledWith(10)
    expect(monitoringAPI.getAllocationTrends).toHaveBeenCalledWith(30)
    expect(monitoringAPI.getAlertHistory).toHaveBeenCalledWith({ limit: 10 })
  })

  it('should display correct statistics in cards', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for data to load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Check if statistics are displayed correctly
    const statCards = wrapper.findAll('.stat-card')
    expect(statCards).toHaveLength(4)

    // Check total IPs
    expect(wrapper.text()).toContain('1000')
    // Check utilization rate
    expect(wrapper.text()).toContain('80%')
    // Check total subnets
    expect(wrapper.text()).toContain('25')
    // Check unresolved alerts
    expect(wrapper.text()).toContain('3')
  })

  it('should handle API errors gracefully', async () => {
    // Mock API to throw error
    vi.mocked(monitoringAPI.getDashboardSummary).mockRejectedValue(
      new Error('Network error')
    )

    wrapper = mount(MonitoringDashboard)

    // Wait for error handling
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Check if error message was shown
    expect(ElMessage.error).toHaveBeenCalledWith('加载仪表盘数据失败')
  })

  it('should render subnet utilization table correctly', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for data to load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Check if table is rendered
    const table = wrapper.find('.table-section el-table')
    expect(table.exists()).toBe(true)

    // Check if subnet data is displayed
    expect(wrapper.text()).toContain('192.168.1.0/24')
    expect(wrapper.text()).toContain('Main Office Network')
    expect(wrapper.text()).toContain('82.68%')
  })

  it('should render alert history table correctly', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for data to load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Check if alerts table is rendered
    const alertsTable = wrapper.find('.alerts-section el-table')
    expect(alertsTable.exists()).toBe(true)

    // Check if alert data is displayed
    expect(wrapper.text()).toContain('High utilization in subnet')
    expect(wrapper.text()).toContain('IP conflict detected')
  })

  it('should resolve alert when resolve button is clicked', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for data to load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Find and click resolve button for unresolved alert
    const resolveButtons = wrapper.findAll('el-button[type="text"]')
    const resolveButton = resolveButtons.find(btn => btn.text().includes('解决'))
    
    if (resolveButton) {
      await resolveButton.trigger('click')

      // Check if resolve API was called
      expect(monitoringAPI.resolveAlert).toHaveBeenCalledWith(1)
      expect(ElMessage.success).toHaveBeenCalledWith('警报已解决')
    }
  })

  it('should handle resolve alert error', async () => {
    // Mock resolve alert to throw error
    vi.mocked(monitoringAPI.resolveAlert).mockRejectedValue(
      new Error('Resolve error')
    )

    wrapper = mount(MonitoringDashboard)

    // Wait for data to load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Trigger resolve alert
    await wrapper.vm.resolveAlert(1)

    // Check if error message was shown
    expect(ElMessage.error).toHaveBeenCalledWith('解决警报失败')
  })

  it('should get correct utilization color based on rate', () => {
    wrapper = mount(MonitoringDashboard)

    const { getUtilizationColor } = wrapper.vm

    expect(getUtilizationColor(95)).toBe('#F56C6C') // Red for >= 90%
    expect(getUtilizationColor(85)).toBe('#E6A23C') // Orange for >= 80%
    expect(getUtilizationColor(65)).toBe('#409EFF') // Blue for >= 60%
    expect(getUtilizationColor(45)).toBe('#67C23A') // Green for < 60%
  })

  it('should get correct severity type and text', () => {
    wrapper = mount(MonitoringDashboard)

    const { getSeverityType, getSeverityText } = wrapper.vm

    expect(getSeverityType('low')).toBe('info')
    expect(getSeverityType('medium')).toBe('warning')
    expect(getSeverityType('high')).toBe('danger')
    expect(getSeverityType('critical')).toBe('danger')

    expect(getSeverityText('low')).toBe('低')
    expect(getSeverityText('medium')).toBe('中')
    expect(getSeverityText('high')).toBe('高')
    expect(getSeverityText('critical')).toBe('严重')
  })

  it('should format datetime correctly', () => {
    wrapper = mount(MonitoringDashboard)

    const { formatDateTime } = wrapper.vm
    const testDate = '2023-01-01T10:30:00Z'
    
    const result = formatDateTime(testDate)
    expect(result).toMatch(/\d{4}\/\d{1,2}\/\d{1,2}/)
  })

  it('should refresh data when refresh buttons are clicked', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for initial load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Clear previous calls
    vi.clearAllMocks()

    // Test refresh IP stats
    await wrapper.vm.refreshIPStats()
    expect(monitoringAPI.getDashboardSummary).toHaveBeenCalledOnce()

    // Test refresh trends
    await wrapper.vm.refreshTrends()
    expect(monitoringAPI.getAllocationTrends).toHaveBeenCalledWith(30)

    // Test refresh subnet stats
    await wrapper.vm.refreshSubnetStats()
    expect(monitoringAPI.getTopUtilizedSubnets).toHaveBeenCalledWith(10)
  })

  it('should change trend days and reload data', async () => {
    wrapper = mount(MonitoringDashboard)

    // Wait for initial load
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    // Clear previous calls
    vi.clearAllMocks()

    // Change trend days
    wrapper.vm.trendDays = 7
    await wrapper.vm.refreshTrends()

    expect(monitoringAPI.getAllocationTrends).toHaveBeenCalledWith(7)
  })

  it('should show report generation dialog', async () => {
    wrapper = mount(MonitoringDashboard)

    // Initially dialog should be hidden
    expect(wrapper.vm.showReportDialog).toBe(false)

    // Find and click generate report button
    const generateButton = wrapper.find('el-button[type="primary"]')
    await generateButton.trigger('click')

    // Dialog should be shown
    expect(wrapper.vm.showReportDialog).toBe(true)
  })

  it('should handle report generation', async () => {
    wrapper = mount(MonitoringDashboard)

    const reportInfo = {
      report_id: 'test-report-123',
      report_type: 'utilization',
      format: 'pdf'
    }

    await wrapper.vm.handleReportGenerated(reportInfo)

    expect(ElMessage.success).toHaveBeenCalledWith('报告生成请求已提交')
  })
})