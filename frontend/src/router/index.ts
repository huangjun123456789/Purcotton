import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 路由元信息类型
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    requiresAdmin?: boolean
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/views/Layout.vue'),
    redirect: '/heatmap',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'heatmap',
        name: 'Heatmap',
        component: () => import('@/views/Heatmap.vue'),
        meta: { title: '库位分布', requiresAuth: true }
      },
      {
        path: 'heatmap3d',
        name: 'Heatmap3D',
        component: () => import('@/views/Heatmap3D.vue'),
        meta: { title: '3D库位分布', requiresAuth: true }
      },
      {
        path: 'warehouse',
        name: 'Warehouse',
        component: () => import('@/views/Warehouse.vue'),
        meta: { title: '仓库管理', requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'import',
        name: 'Import',
        component: () => import('@/views/Import.vue'),
        meta: { title: '数据导入', requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'warehouse/:id/canvas',
        name: 'WarehouseCanvas',
        component: () => import('@/views/WarehouseCanvas.vue'),
        meta: { title: '画布布局', requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理', requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '个人设置', requiresAuth: true }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - WMS 热力图系统` : 'WMS 热力图系统'
  
  const token = localStorage.getItem('access_token')
  const userInfo = localStorage.getItem('user_info')
  const isLoggedIn = !!token && !!userInfo
  
  // 不需要认证的页面
  if (to.meta.requiresAuth === false) {
    // 已登录用户访问登录页，跳转到首页
    if (to.name === 'Login' && isLoggedIn) {
      next('/')
      return
    }
    next()
    return
  }
  
  // 需要认证但未登录
  if (to.meta.requiresAuth !== false && !isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }
  
  // 需要管理员权限
  if (to.meta.requiresAdmin) {
    const user = JSON.parse(userInfo || '{}')
    if (user.role !== 'admin') {
      // 无权限，跳转到首页
      next('/')
      return
    }
  }
  
  next()
})

export default router
