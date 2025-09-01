import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 导入布局组件
import Layout from '@/components/Layout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Dashboard' }
      }
    ]
  },
  {
    path: '/ip-management',
    component: Layout,
    redirect: '/ip-management/addresses',
    meta: { title: 'IP管理', icon: 'Network', requiresAuth: true },
    children: [
      {
        path: 'addresses',
        name: 'IPAddresses',
        component: () => import('@/views/ip/IPAddressList.vue'),
        meta: { title: 'IP地址管理', icon: 'Location' }
      },
      {
        path: 'segments',
        name: 'NetworkSegments',
        component: () => import('@/views/network/NetworkSegmentList.vue'),
        meta: { title: '网段管理', icon: 'Connection' }
      },
      {
        path: 'reserved',
        name: 'ReservedAddresses',
        component: () => import('@/views/reserved/ReservedAddressList.vue'),
        meta: { title: '地址保留', icon: 'Lock' }
      }
    ]
  },
  {
    path: '/organization',
    component: Layout,
    redirect: '/organization/departments',
    meta: { title: '组织管理', icon: 'OfficeBuilding', requiresAuth: true },
    children: [
      {
        path: 'departments',
        name: 'Departments',
        component: () => import('@/views/organization/DepartmentList.vue'),
        meta: { title: '部门管理', icon: 'OfficeBuilding' }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/organization/UserList.vue'),
        meta: { title: '用户管理', icon: 'User' }
      }
    ]
  },
  {
    path: '/system',
    component: Layout,
    redirect: '/system/users',
    meta: { title: '系统管理', icon: 'Setting', requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: 'users',
        name: 'SystemUsers',
        component: () => import('@/views/system/UserManagement.vue'),
        meta: { title: '用户管理', icon: 'User', requiresAdmin: true }
      },
      {
        path: 'groups',
        name: 'SystemGroups',
        component: () => import('@/views/system/GroupManagement.vue'),
        meta: { title: '组管理', icon: 'UserFilled', requiresAdmin: true }
      },
      {
        path: 'settings',
        name: 'SystemSettings',
        component: () => import('@/views/system/SystemSettings.vue'),
        meta: { title: '系统设置', icon: 'Tools', requiresSuperuser: true }
      }
    ]
  },
  {
    path: '/statistics',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '统计报表', icon: 'DataAnalysis' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 设置页面标题
  if (to.meta?.title) {
    document.title = `${to.meta.title} - 企业IP地址管理系统`
  }
  
  const authStore = useAuthStore()
  
  // 检查是否需要认证
  if (to.meta?.requiresAuth !== false) {
    // 需要认证的路由
    if (!authStore.isLoggedIn) {
      // 未登录，尝试初始化认证状态
      const initSuccess = await authStore.initAuth()
      if (!initSuccess) {
        // 初始化失败，跳转到登录页
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
    
    // 检查管理员权限
    if (to.meta?.requiresAdmin && !authStore.isAdmin) {
      next({ path: '/403' }) // 可以创建一个403页面
      return
    }
    
    // 检查超级用户权限
    if (to.meta?.requiresSuperuser && !authStore.isSuperuser) {
      next({ path: '/403' })
      return
    }
  } else {
    // 不需要认证的路由（如登录页）
    if (to.path === '/login' && authStore.isLoggedIn) {
      // 已登录用户访问登录页，跳转到首页
      next('/')
      return
    }
  }
  
  next()
})

export default router