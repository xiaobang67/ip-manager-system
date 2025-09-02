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
    path: '/audit-logs',
    name: 'AuditLogs',
    component: () => import('@/components/AuditLogsManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

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
  if (to.meta.requiresAdmin && userRole !== 'admin') {
    next('/dashboard')
    return
  }
  
  // 如果已登录，验证token有效性（仅在应用启动时）
  if (isAuthenticated && from.path === '/') {
    try {
      await store.dispatch('auth/initAuth')
    } catch (error) {
      console.error('Auth initialization error:', error)
      next('/login')
      return
    }
  }
  
  next()
})

export default router