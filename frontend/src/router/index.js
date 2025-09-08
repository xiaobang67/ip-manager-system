import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ip-management',
    name: 'IPManagement',
    component: () => import('@/views/IPManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/subnet-management',
    name: 'SubnetManagement',
    component: () => import('@/views/SubnetManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: () => import('@/views/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/department-management',
    name: 'DepartmentManagement',
    component: () => import('@/views/DepartmentManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/audit-logs',
    name: 'AuditLogs',
    component: () => import('@/views/AuditLogs.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/custom-fields-test',
    name: 'CustomFieldsTest',
    component: () => import('@/components/CustomFieldsTest.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 标记是否已经初始化过认证
let authInitialized = false

// Navigation guard for authentication
router.beforeEach(async (to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']
  const userRole = store.getters['auth/userRole']
  
  // 如果访问登录页面且已经登录，重定向到仪表盘
  if (to.path === '/login' && isAuthenticated) {
    next('/dashboard')
    return
  }
  
  // 如果需要认证但未登录
  if (to.meta.requiresAuth && !isAuthenticated) {
    next({
      path: '/login',
      query: { redirect: to.fullPath } // 保存原始访问路径
    })
    return
  }
  
  // 如果需要管理员权限但不是管理员
  if (to.meta.requiresAdmin && userRole !== 'ADMIN') {
    next('/dashboard')
    return
  }
  
  // 仅在应用首次加载时验证token有效性
  if (isAuthenticated && !authInitialized) {
    authInitialized = true
    try {
      await store.dispatch('auth/initAuth')
    } catch (error) {
      console.error('Auth initialization error:', error)
      authInitialized = false // 重置标记，允许重试
      next('/login')
      return
    }
  }
  
  next()
})

export default router