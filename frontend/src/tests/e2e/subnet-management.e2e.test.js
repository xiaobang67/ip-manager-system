/**
 * 网段管理E2E测试
 * 使用Cypress进行端到端测试
 */

describe('网段管理E2E测试', () => {
  beforeEach(() => {
    // 登录系统
    cy.login('admin', 'admin123')
    
    // 访问网段管理页面
    cy.visit('/subnet-management')
    
    // 等待页面加载
    cy.get('[data-testid="subnet-list"]').should('be.visible')
  })

  describe('网段列表显示', () => {
    it('应该显示网段列表', () => {
      cy.get('[data-testid="subnet-list"]').should('be.visible')
      cy.get('[data-testid="subnet-item"]').should('have.length.at.least', 0)
    })

    it('应该显示网段基本信息', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="subnet-network"]').should('be.visible')
        cy.get('[data-testid="subnet-description"]').should('be.visible')
        cy.get('[data-testid="subnet-utilization"]').should('be.visible')
      })
    })

    it('应该显示操作按钮', () => {
      cy.get('[data-testid="create-subnet-btn"]').should('be.visible')
      
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="edit-subnet-btn"]').should('be.visible')
        cy.get('[data-testid="delete-subnet-btn"]').should('be.visible')
        cy.get('[data-testid="view-detail-btn"]').should('be.visible')
      })
    })
  })

  describe('创建网段', () => {
    it('应该成功创建新网段', () => {
      const subnetData = {
        network: '172.16.0.0/16',
        gateway: '172.16.0.1',
        description: 'E2E测试网段',
        vlan_id: '500',
        location: 'E2E测试位置'
      }

      // 点击创建按钮
      cy.get('[data-testid="create-subnet-btn"]').click()

      // 填写表单
      cy.get('[data-testid="subnet-dialog"]').should('be.visible')
      cy.get('[data-testid="network-input"]').type(subnetData.network)
      cy.get('[data-testid="gateway-input"]').type(subnetData.gateway)
      cy.get('[data-testid="description-input"]').type(subnetData.description)
      cy.get('[data-testid="vlan-input"]').type(subnetData.vlan_id)
      cy.get('[data-testid="location-input"]').type(subnetData.location)

      // 提交表单
      cy.get('[data-testid="submit-btn"]').click()

      // 验证成功消息
      cy.get('.el-message--success').should('contain', '网段创建成功')

      // 验证网段出现在列表中
      cy.get('[data-testid="subnet-list"]').should('contain', subnetData.network)
    })

    it('应该验证网段格式', () => {
      cy.get('[data-testid="create-subnet-btn"]').click()
      
      // 输入无效网段格式
      cy.get('[data-testid="network-input"]').type('invalid-network')
      cy.get('[data-testid="gateway-input"]').click() // 触发验证

      // 应该显示错误信息
      cy.get('.el-form-item__error').should('contain', '请输入有效的网段格式')
    })

    it('应该检测网段重叠', () => {
      // 假设已存在192.168.1.0/24网段
      cy.get('[data-testid="create-subnet-btn"]').click()
      
      cy.get('[data-testid="network-input"]').type('192.168.1.0/25') // 重叠网段
      cy.get('[data-testid="gateway-input"]').type('192.168.1.1')
      cy.get('[data-testid="submit-btn"]').click()

      // 应该显示重叠错误
      cy.get('.el-message--error').should('contain', '网段重叠')
    })

    it('应该取消创建操作', () => {
      cy.get('[data-testid="create-subnet-btn"]').click()
      cy.get('[data-testid="subnet-dialog"]').should('be.visible')
      
      // 点击取消按钮
      cy.get('[data-testid="cancel-btn"]').click()
      
      // 对话框应该关闭
      cy.get('[data-testid="subnet-dialog"]').should('not.exist')
    })
  })

  describe('编辑网段', () => {
    it('应该成功编辑网段信息', () => {
      // 点击第一个网段的编辑按钮
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="edit-subnet-btn"]').click()
      })

      // 修改描述
      cy.get('[data-testid="description-input"]').clear().type('更新后的描述')
      cy.get('[data-testid="location-input"]').clear().type('更新后的位置')

      // 提交修改
      cy.get('[data-testid="submit-btn"]').click()

      // 验证成功消息
      cy.get('.el-message--success').should('contain', '网段更新成功')
    })

    it('应该预填充现有数据', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        // 获取网段信息
        cy.get('[data-testid="subnet-network"]').invoke('text').as('networkText')
        cy.get('[data-testid="edit-subnet-btn"]').click()
      })

      // 验证表单预填充
      cy.get('@networkText').then((networkText) => {
        cy.get('[data-testid="network-input"]').should('have.value', networkText.trim())
      })
    })
  })

  describe('删除网段', () => {
    it('应该显示删除确认对话框', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="delete-subnet-btn"]').click()
      })

      // 验证确认对话框
      cy.get('.el-message-box').should('be.visible')
      cy.get('.el-message-box__content').should('contain', '确定要删除这个网段吗')
    })

    it('应该取消删除操作', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="delete-subnet-btn"]').click()
      })

      // 点击取消
      cy.get('.el-message-box__btns .el-button--default').click()

      // 网段应该仍然存在
      cy.get('[data-testid="subnet-item"]').should('have.length.at.least', 1)
    })

    it('应该阻止删除有已分配IP的网段', () => {
      // 假设第一个网段有已分配的IP
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="delete-subnet-btn"]').click()
      })

      cy.get('.el-message-box__btns .el-button--primary').click()

      // 应该显示错误消息
      cy.get('.el-message--error').should('contain', '网段下存在已分配的IP地址')
    })
  })

  describe('网段详情查看', () => {
    it('应该打开网段详情对话框', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="view-detail-btn"]').click()
      })

      cy.get('[data-testid="subnet-detail-dialog"]').should('be.visible')
    })

    it('应该显示网段下的IP地址列表', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="view-detail-btn"]').click()
      })

      cy.get('[data-testid="subnet-detail-dialog"]').within(() => {
        cy.get('[data-testid="ip-list"]').should('be.visible')
        cy.get('[data-testid="ip-item"]').should('have.length.at.least', 0)
      })
    })

    it('应该显示IP地址状态统计', () => {
      cy.get('[data-testid="subnet-item"]').first().within(() => {
        cy.get('[data-testid="view-detail-btn"]').click()
      })

      cy.get('[data-testid="subnet-detail-dialog"]').within(() => {
        cy.get('[data-testid="ip-statistics"]').should('be.visible')
        cy.get('[data-testid="total-ips"]').should('be.visible')
        cy.get('[data-testid="allocated-ips"]').should('be.visible')
        cy.get('[data-testid="available-ips"]').should('be.visible')
      })
    })
  })

  describe('搜索和过滤', () => {
    it('应该支持网段搜索', () => {
      // 输入搜索关键词
      cy.get('[data-testid="search-input"]').type('192.168')

      // 等待搜索结果
      cy.wait(500)

      // 验证搜索结果
      cy.get('[data-testid="subnet-item"]').each(($item) => {
        cy.wrap($item).should('contain', '192.168')
      })
    })

    it('应该支持按位置过滤', () => {
      cy.get('[data-testid="location-filter"]').select('Building A')

      // 验证过滤结果
      cy.get('[data-testid="subnet-item"]').each(($item) => {
        cy.wrap($item).find('[data-testid="subnet-location"]').should('contain', 'Building A')
      })
    })

    it('应该支持按VLAN ID过滤', () => {
      cy.get('[data-testid="vlan-filter"]').type('100')

      // 验证过滤结果
      cy.get('[data-testid="subnet-item"]').each(($item) => {
        cy.wrap($item).find('[data-testid="subnet-vlan"]').should('contain', '100')
      })
    })

    it('应该清除搜索条件', () => {
      // 输入搜索条件
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="location-filter"]').select('Building A')

      // 点击清除按钮
      cy.get('[data-testid="clear-filters-btn"]').click()

      // 验证搜索条件被清除
      cy.get('[data-testid="search-input"]').should('have.value', '')
      cy.get('[data-testid="location-filter"]').should('have.value', '')
    })
  })

  describe('分页功能', () => {
    it('应该显示分页组件', () => {
      cy.get('[data-testid="pagination"]').should('be.visible')
    })

    it('应该支持页面切换', () => {
      // 假设有多页数据
      cy.get('[data-testid="pagination"]').within(() => {
        cy.get('.el-pager li').contains('2').click()
      })

      // 验证页面切换
      cy.url().should('include', 'page=2')
    })

    it('应该支持每页大小调整', () => {
      cy.get('[data-testid="page-size-select"]').select('20')

      // 验证每页大小变更
      cy.url().should('include', 'size=20')
    })
  })

  describe('响应式设计', () => {
    it('应该在移动设备上正确显示', () => {
      cy.viewport('iphone-6')

      cy.get('[data-testid="subnet-list"]').should('be.visible')
      cy.get('[data-testid="mobile-menu-btn"]').should('be.visible')
    })

    it('应该在平板设备上正确显示', () => {
      cy.viewport('ipad-2')

      cy.get('[data-testid="subnet-list"]').should('be.visible')
      cy.get('[data-testid="create-subnet-btn"]').should('be.visible')
    })
  })

  describe('错误处理', () => {
    it('应该处理网络错误', () => {
      // 模拟网络错误
      cy.intercept('GET', '/api/subnets', { forceNetworkError: true })

      cy.reload()

      // 验证错误消息
      cy.get('.el-message--error').should('contain', '网络错误')
    })

    it('应该处理服务器错误', () => {
      // 模拟服务器错误
      cy.intercept('GET', '/api/subnets', { statusCode: 500 })

      cy.reload()

      // 验证错误消息
      cy.get('.el-message--error').should('contain', '服务器错误')
    })

    it('应该处理权限不足', () => {
      // 模拟权限不足
      cy.intercept('POST', '/api/subnets', { statusCode: 403 })

      cy.get('[data-testid="create-subnet-btn"]').click()
      cy.get('[data-testid="network-input"]').type('10.0.0.0/8')
      cy.get('[data-testid="submit-btn"]').click()

      // 验证权限错误消息
      cy.get('.el-message--error').should('contain', '权限不足')
    })
  })

  describe('性能测试', () => {
    it('应该快速加载网段列表', () => {
      const startTime = Date.now()

      cy.visit('/subnet-management')
      cy.get('[data-testid="subnet-list"]').should('be.visible')

      cy.then(() => {
        const loadTime = Date.now() - startTime
        expect(loadTime).to.be.lessThan(3000) // 3秒内加载完成
      })
    })

    it('应该处理大量网段数据', () => {
      // 模拟大量数据
      cy.intercept('GET', '/api/subnets', { fixture: 'large-subnet-list.json' })

      cy.visit('/subnet-management')
      cy.get('[data-testid="subnet-list"]').should('be.visible')

      // 验证虚拟滚动正常工作
      cy.get('[data-testid="subnet-item"]').should('have.length.at.most', 50)
    })
  })

  describe('可访问性测试', () => {
    it('应该支持键盘导航', () => {
      cy.get('[data-testid="create-subnet-btn"]').focus()
      cy.focused().should('have.attr', 'data-testid', 'create-subnet-btn')

      // Tab键导航
      cy.focused().tab()
      cy.focused().should('have.attr', 'data-testid', 'search-input')
    })

    it('应该有正确的ARIA标签', () => {
      cy.get('[data-testid="subnet-list"]').should('have.attr', 'role', 'list')
      cy.get('[data-testid="subnet-item"]').should('have.attr', 'role', 'listitem')
    })

    it('应该支持屏幕阅读器', () => {
      cy.get('[data-testid="create-subnet-btn"]').should('have.attr', 'aria-label', '创建新网段')
      cy.get('[data-testid="search-input"]').should('have.attr', 'aria-label', '搜索网段')
    })
  })

  describe('数据持久化', () => {
    it('应该保存搜索条件', () => {
      // 设置搜索条件
      cy.get('[data-testid="search-input"]').type('test')
      cy.get('[data-testid="location-filter"]').select('Building A')

      // 刷新页面
      cy.reload()

      // 验证搜索条件被保存
      cy.get('[data-testid="search-input"]').should('have.value', 'test')
      cy.get('[data-testid="location-filter"]').should('have.value', 'Building A')
    })

    it('应该保存分页状态', () => {
      // 切换到第2页
      cy.get('[data-testid="pagination"]').within(() => {
        cy.get('.el-pager li').contains('2').click()
      })

      // 刷新页面
      cy.reload()

      // 验证仍在第2页
      cy.url().should('include', 'page=2')
    })
  })
})