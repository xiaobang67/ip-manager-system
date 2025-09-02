/**
 * 报告生成对话框组件单元测试
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElMessage } from 'element-plus'
import ReportGenerationDialog from '@/components/ReportGenerationDialog.vue'
import * as monitoringAPI from '@/api/monitoring'
import * as subnetAPI from '@/api/subnet'

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
  generateReport: vi.fn(),
  getReportStatus: vi.fn(),
  downloadReport: vi.fn()
}))

vi.mock('@/api/subnet', () => ({
  getSubnets: vi.fn()
}))

describe('ReportGenerationDialog', () => {
  let wrapper

  const mockSubnets = [
    {
      id: 1,
      network: '192.168.1.0/24',
      description: 'Main Office Network'
    },
    {
      id: 2,
      network: '192.168.2.0/24',
      description: 'Guest Network'
    }
  ]

  const mockReportResponse = {
    data: {
      report_id: 'test-report-123',
      report_type: 'utilization',
      format: 'pdf',
      file_url: '/api/v1/monitoring/reports/test-report-123/download',
      generated_at: '2023-01-01T10:00:00Z',
      expires_at: '2023-01-08T10:00:00Z'
    }
  }

  beforeEach(() => {
    // Setup API mocks
    vi.mocked(subnetAPI.getSubnets).mockResolvedValue({
      data: mockSubnets
    })
    vi.mocked(monitoringAPI.generateReport).mockResolvedValue(mockReportResponse)
    vi.mocked(monitoringAPI.getReportStatus).mockResolvedValue({
      data: {
        report_id: 'test-report-123',
        status: 'completed',
        generated_at: '2023-01-01T10:00:00Z',
        expires_at: '2023-01-08T10:00:00Z',
        download_url: '/api/v1/monitoring/reports/test-report-123/download'
      }
    })
    vi.mocked(monitoringAPI.downloadReport).mockResolvedValue({
      data: new Blob(['test content'], { type: 'application/pdf' })
    })

    // Clear all mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('should render dialog with correct structure', () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    expect(wrapper.find('el-dialog').exists()).toBe(true)
    expect(wrapper.find('el-form').exists()).toBe(true)
    expect(wrapper.find('el-form-item').exists()).toBe(true)
  })

  it('should load available subnets on mount', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 0))

    expect(subnetAPI.getSubnets).toHaveBeenCalledOnce()
    expect(wrapper.vm.availableSubnets).toEqual(mockSubnets)
  })

  it('should have correct default form values', () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    expect(wrapper.vm.reportForm.report_type).toBe('utilization')
    expect(wrapper.vm.reportForm.format).toBe('pdf')
    expect(wrapper.vm.reportForm.subnet_ids).toEqual([])
    expect(wrapper.vm.reportForm.include_details).toBe(true)
  })

  it('should validate required fields', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Clear required fields
    wrapper.vm.reportForm.report_type = ''
    wrapper.vm.reportForm.format = ''

    // Try to generate report
    await wrapper.vm.generateReport()

    // Form validation should prevent submission
    expect(monitoringAPI.generateReport).not.toHaveBeenCalled()
  })

  it('should generate report successfully', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Set valid form data
    wrapper.vm.reportForm.report_type = 'utilization'
    wrapper.vm.reportForm.format = 'pdf'

    // Mock form validation to pass
    wrapper.vm.formRef = {
      validate: vi.fn().mockResolvedValue(true)
    }

    await wrapper.vm.generateReport()

    expect(monitoringAPI.generateReport).toHaveBeenCalledWith({
      report_type: 'utilization',
      format: 'pdf',
      subnet_ids: [],
      include_details: true
    })

    expect(wrapper.vm.showStatusDialog).toBe(true)
    expect(wrapper.emitted('report-generated')).toBeTruthy()
  })

  it('should include date range in report request', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Set date range
    wrapper.vm.dateRange = ['2023-01-01', '2023-01-31']

    // Mock form validation
    wrapper.vm.formRef = {
      validate: vi.fn().mockResolvedValue(true)
    }

    await wrapper.vm.generateReport()

    expect(monitoringAPI.generateReport).toHaveBeenCalledWith({
      report_type: 'utilization',
      format: 'pdf',
      subnet_ids: [],
      include_details: true,
      date_range: {
        start_date: '2023-01-01',
        end_date: '2023-01-31'
      }
    })
  })

  it('should handle generate report error', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Mock API to throw error
    vi.mocked(monitoringAPI.generateReport).mockRejectedValue(
      new Error('Generation failed')
    )

    // Mock form validation
    wrapper.vm.formRef = {
      validate: vi.fn().mockResolvedValue(true)
    }

    await wrapper.vm.generateReport()

    expect(ElMessage.error).toHaveBeenCalledWith('生成报告失败')
  })

  it('should poll report status until completion', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Mock initial generating status, then completed
    vi.mocked(monitoringAPI.getReportStatus)
      .mockResolvedValueOnce({
        data: { status: 'generating' }
      })
      .mockResolvedValueOnce({
        data: { 
          status: 'completed',
          download_url: '/download/url'
        }
      })

    // Start polling
    await wrapper.vm.pollReportStatus()

    // Wait for polling to complete
    await new Promise(resolve => setTimeout(resolve, 2100))

    expect(wrapper.vm.reportStatus.status).toBe('completed')
  })

  it('should check report status manually', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    wrapper.vm.reportStatus.report_id = 'test-report-123'

    await wrapper.vm.checkStatus()

    expect(monitoringAPI.getReportStatus).toHaveBeenCalledWith('test-report-123')
  })

  it('should download report successfully', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Setup report status
    wrapper.vm.reportStatus.report_id = 'test-report-123'
    wrapper.vm.reportForm.format = 'pdf'

    // Mock DOM methods
    const mockLink = {
      href: '',
      download: '',
      click: vi.fn()
    }
    const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockLink)
    const appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    const removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => {})
    const createObjectURLSpy = vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:url')
    const revokeObjectURLSpy = vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {})

    await wrapper.vm.downloadReport()

    expect(monitoringAPI.downloadReport).toHaveBeenCalledWith('test-report-123')
    expect(createElementSpy).toHaveBeenCalledWith('a')
    expect(mockLink.download).toBe('report_test-report-123.pdf')
    expect(mockLink.click).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('报告下载成功')

    // Cleanup
    createElementSpy.mockRestore()
    appendChildSpy.mockRestore()
    removeChildSpy.mockRestore()
    createObjectURLSpy.mockRestore()
    revokeObjectURLSpy.mockRestore()
  })

  it('should handle download error', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Mock download to throw error
    vi.mocked(monitoringAPI.downloadReport).mockRejectedValue(
      new Error('Download failed')
    )

    wrapper.vm.reportStatus.report_id = 'test-report-123'

    await wrapper.vm.downloadReport()

    expect(ElMessage.error).toHaveBeenCalledWith('下载报告失败')
  })

  it('should format datetime correctly', () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    const testDate = '2023-01-01T10:30:00Z'
    const result = wrapper.vm.formatDateTime(testDate)
    
    expect(result).toMatch(/\d{4}\/\d{1,2}\/\d{1,2}/)
  })

  it('should reset form when dialog closes', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Modify form data
    wrapper.vm.reportForm.report_type = 'inventory'
    wrapper.vm.reportForm.format = 'csv'
    wrapper.vm.dateRange = ['2023-01-01', '2023-01-31']

    // Close dialog
    await wrapper.vm.handleClose()

    // Form should be reset
    expect(wrapper.vm.reportForm.report_type).toBe('utilization')
    expect(wrapper.vm.reportForm.format).toBe('pdf')
    expect(wrapper.vm.dateRange).toBeNull()
  })

  it('should emit update:modelValue when dialog visibility changes', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    // Change dialog visibility
    wrapper.vm.dialogVisible = false

    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual([false])
  })

  it('should show different file extensions for different formats', async () => {
    wrapper = mount(ReportGenerationDialog, {
      props: {
        modelValue: true
      }
    })

    const testCases = [
      { format: 'pdf', expected: 'pdf' },
      { format: 'excel', expected: 'xlsx' },
      { format: 'csv', expected: 'csv' },
      { format: 'json', expected: 'json' }
    ]

    for (const testCase of testCases) {
      wrapper.vm.reportForm.format = testCase.format
      wrapper.vm.reportStatus.report_id = 'test-report-123'

      // Mock DOM methods for download test
      const mockLink = { download: '', click: vi.fn() }
      vi.spyOn(document, 'createElement').mockReturnValue(mockLink)
      vi.spyOn(document.body, 'appendChild').mockImplementation(() => {})
      vi.spyOn(document.body, 'removeChild').mockImplementation(() => {})
      vi.spyOn(window.URL, 'createObjectURL').mockReturnValue('blob:url')
      vi.spyOn(window.URL, 'revokeObjectURL').mockImplementation(() => {})

      await wrapper.vm.downloadReport()

      expect(mockLink.download).toBe(`report_test-report-123.${testCase.expected}`)

      // Restore mocks
      vi.restoreAllMocks()
    }
  })
})