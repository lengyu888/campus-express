import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { tokenStore } from '../api/http'
import { startRoute, endRoute } from '../composables/routeProgress'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/Login.vue'),
    meta: { public: true, title: '登录' }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '工作台' }
      },
      {
        path: 'packages',
        name: 'packages',
        component: () => import('../views/Packages.vue'),
        meta: { title: '包裹管理', roles: ['admin', 'staff'] }
      },
      {
        path: 'pickup',
        name: 'pickup',
        component: () => import('../views/Pickup.vue'),
        meta: { title: '取件核验', roles: ['admin', 'staff'] }
      },
      {
        path: 'my-packages',
        name: 'my-packages',
        component: () => import('../views/MyPackages.vue'),
        meta: { title: '我的包裹' }
      },
      {
        path: 'shipments',
        name: 'shipments',
        component: () => import('../views/Shipments.vue'),
        meta: { title: '我的寄件', roles: ['student'] }
      },
      {
        path: 'shipment-manage',
        name: 'shipment-manage',
        component: () => import('../views/ShipmentManage.vue'),
        meta: { title: '寄件处理', roles: ['staff', 'admin'] }
      },
      {
        path: 'stats',
        name: 'stats',
        component: () => import('../views/Stats.vue'),
        meta: { title: '统计报表', roles: ['staff', 'admin'] }
      },
      {
        path: 'notifications',
        name: 'notifications',
        component: () => import('../views/Notifications.vue'),
        meta: { title: '消息中心' }
      },
      {
        path: 'announcements',
        name: 'announcements',
        component: () => import('../views/Announcements.vue'),
        meta: { title: '公告管理', roles: ['admin'] }
      },
      {
        path: 'stations',
        name: 'stations',
        component: () => import('../views/Stations.vue'),
        meta: { title: '驿站管理', roles: ['admin', 'staff'] }
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('../views/Users.vue'),
        meta: { title: '用户管理', roles: ['admin'] }
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('../views/Profile.vue'),
        meta: { title: '个人中心' }
      }
    ]
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('../views/Forbidden.vue'),
    meta: { public: true, title: '无权访问' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFound.vue'),
    meta: { public: true, title: '页面不存在' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  startRoute()
  const auth = useAuthStore()

  if (to.meta.public) {
    if (to.path === '/login' && tokenStore.access) return { path: '/' }
    return true
  }

  if (!tokenStore.access) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (!auth.user) {
    try {
      await auth.loadMe()
    } catch (e) {
      tokenStore.clear()
      return { path: '/login', query: { redirect: to.fullPath } }
    }
  }

  if (to.meta.roles && !to.meta.roles.includes(auth.user?.role)) {
    return { path: '/403' }
  }

  return true
})

router.afterEach((to) => {
  endRoute()
  document.title = to.meta.title ? `${to.meta.title} · 校园快递收发系统` : '校园快递收发系统'
})

router.onError(() => endRoute())

export default router
