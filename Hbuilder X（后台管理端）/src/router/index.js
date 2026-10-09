import { createRouter, createWebHashHistory } from 'vue-router'
import { APP_TITLE, STORAGE_KEYS } from '@/utils/constants'
import { useAuthStore } from '@/stores/auth'
import { menuItems } from './menu'

const LazyLayout = () => import('@/layout/AdminLayout.vue')
const LazyActivities = () => import('@/views/activities/ActivitiesView.vue')
const LazyMessages = () => import('@/views/messages/MessagesView.vue')
const LazyLogin = () => import('@/views/auth/LoginView.vue')
const LazyDashboard = () => import('@/views/dashboard/DashboardView.vue')
const LazyOrders = () => import('@/views/orders/OrdersView.vue')
const LazyRefunds = () => import('@/views/refunds/RefundsView.vue')
const LazyUsers = () => import('@/views/users/UsersView.vue')
const LazyDishes = () => import('@/views/dishes/DishesView.vue')
const LazyCanteens = () => import('@/views/canteens/CanteensView.vue')
const LazyCategories = () => import('@/views/categories/CategoriesView.vue')
const LazyCoupons = () => import('@/views/coupons/CouponsView.vue')
const LazyReviews = () => import('@/views/reviews/ReviewsView.vue')
const LazyNotifications = () => import('@/views/notifications/NotificationsView.vue')
const LazyFaqs = () => import('@/views/faqs/FaqsView.vue')
const LazyStatistics = () => import('@/views/statistics/StatisticsView.vue')
const LazyExport = () => import('@/views/export/ExportView.vue')
const LazyQueues = () => import('@/views/queues/QueuesView.vue')

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LazyLogin,
    meta: { public: true, title: '管理端登录' }
  },
  {
    path: '/',
    component: LazyLayout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', name: 'dashboard', component: LazyDashboard, meta: { title: '数据看板' } },
      { path: 'orders', name: 'orders', component: LazyOrders, meta: { title: '订单管理' } },
      { path: 'refunds', name: 'refunds', component: LazyRefunds, meta: { title: '退款管理' } },
      { path: 'users', name: 'users', component: LazyUsers, meta: { title: '用户管理' } },
      { path: 'dishes', name: 'dishes', component: LazyDishes, meta: { title: '菜品管理' } },
      { path: 'canteens', name: 'canteens', component: LazyCanteens, meta: { title: '档口管理' } },
      { path: 'categories', name: 'categories', component: LazyCategories, meta: { title: '分类管理' } },
      { path: 'activities', name: 'activities', component: LazyActivities, meta: { title: '活动管理' } },
      { path: 'messages', name: 'messages', component: LazyMessages, meta: { title: '消息中心' } },
      { path: 'coupons', name: 'coupons', component: LazyCoupons, meta: { title: '优惠券管理' } },
      { path: 'reviews', name: 'reviews', component: LazyReviews, meta: { title: '评价管理' } },
      { path: 'notifications', name: 'notifications', component: LazyNotifications, meta: { title: '通知管理' } },
      { path: 'faqs', name: 'faqs', component: LazyFaqs, meta: { title: 'FAQ 管理' } },
      { path: 'statistics', name: 'statistics', component: LazyStatistics, meta: { title: '统计分析' } },
      { path: 'export', name: 'export', component: LazyExport, meta: { title: '报表导出' } },
      { path: 'queues', name: 'queues', component: LazyQueues, meta: { title: '排队管理' } }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

router.beforeEach(async (to, _from, next) => {
  document.title = `${to.meta?.title || '管理后台'} - ${APP_TITLE}`
  if (!to.meta?.public) {
    document.body.classList.add('route-loading')
  }

  const token = localStorage.getItem(STORAGE_KEYS.token)
  if (to.meta?.public) {
    if (token && to.path === '/login') {
      next('/dashboard')
      return
    }
    next()
    return
  }

  if (!token) {
    next('/login')
    return
  }

  const authStore = useAuthStore()
  if (!authStore.user) {
    try {
      await authStore.fetchProfile()
    } catch (_error) {
      authStore.clearAuth()
      next('/login')
      return
    }
  }

  next()
})

router.afterEach(() => {
  window.setTimeout(() => {
    document.body.classList.remove('route-loading')
  }, 180)
})

export { menuItems }
export default router
