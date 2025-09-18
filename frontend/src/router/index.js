import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/',
    redirect: (to) => {
      // 根据用户角色重定向到不同页面
      const userRole = store.getters['auth/userRole']
      if (userRole?.toLowerCase() === 'readonly') {
        return '/ip-management'
      }
      return '/dashboard'
    }
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
    meta: { requiresAuth: true, allowReadonly: true }
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
    path: '/device-type-management',
    name: 'DeviceTypeManagement',
    component: () => import('@/views/DeviceTypeManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/custom-fields-test',
    name: 'CustomFieldsTest',
    component: () => import('@/components/CustomFieldsTest.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/theme-test',
    name: 'ThemeTest',
    component: () => import('@/views/ThemeTest.vue'),
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
  // 仅在应用首次加载或刷新时验证token有效性
  if (!authInitialized) {
    authInitialized = true
    try {
      await store.dispatch('auth/initAuth')
    } catch (error) {
      console.error('Auth initialization error:', error)
      authInitialized = false // 重置标记，允许重试
    }
  }

  // 重新获取认证状态（可能在initAuth中被更新）
  const isAuthenticated = store.getters['auth/isAuthenticated']
  const userRole = store.getters['auth/userRole']
  const currentUser = store.getters['auth/currentUser']

  console.log('路由守卫:', {
    to: to.path,
    from: from.path,
    isAuthenticated,
    userRole,
    currentUser: currentUser?.username,
    requiresAuth: to.meta.requiresAuth,
    requiresAdmin: to.meta.requiresAdmin
  })

  // 如果访问登录页面且已经登录，重定向到仪表盘
  if (to.path === '/login' && isAuthenticated) {
    console.log('已登录用户访问登录页，重定向到仪表盘')
    next('/dashboard')
    return
  }

  // 如果需要认证但未登录
  if (to.meta.requiresAuth && !isAuthenticated) {
    console.log('需要认证但未登录，重定向到登录页')
    next({
      path: '/login',
      query: { redirect: to.fullPath } // 保存原始访问路径
    })
    return
  }

  // 如果需要管理员权限但不是管理员
  if (to.meta.requiresAdmin && userRole?.toLowerCase() !== 'admin') {
    console.log('需要管理员权限但不是管理员，重定向到仪表盘')
    next('/dashboard')
    return
  }

  // 如果是只读用户，检查是否允许访问该页面
  if (userRole?.toLowerCase() === 'readonly') {
    // 只读用户只能访问IP管理页面
    const allowedPaths = ['/ip-management']
    if (!allowedPaths.includes(to.path)) {
      console.log('只读用户访问受限页面，重定向到IP管理页面')
      next('/ip-management')
      return
    }
  }

  next()
})

export default router