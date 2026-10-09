// pages/index/index.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    currentLocation: '校园食堂',
    unreadCount: 0,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    },
    canteens: [],
    hotDishes: [],
    bannerDishes: [],
    loading: true,
    error: false,
    greetingTitle: '今日食堂吃点什么',
    greetingSubtitle: '把热门菜品、常用入口和食堂分布放在同一个首页里，打开就能快速下单。',
    currentMealLabel: '正在推荐',
    activeBannerIndex: 0,
    featuredDishName: '',
    featuredDishMeta: '',
    lastVisitedCanteenId: null,
    quickTips: {
      coupon: '领券下单更划算',
      history: '回看最近浏览过的菜品'
    }
  },

  onLoad() {
    this.updateGreeting()
    this.loadCanteens()
    this.loadData()
    this.loadUnreadCount()
    this.restoreLastVisitedCanteen()
    this.updateQuickTips()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    this.updateGreeting()
    this.loadCanteens()
    this.loadData(true)
    this.loadUnreadCount()
    this.restoreLastVisitedCanteen()
    this.updateQuickTips()
  },

  onPullDownRefresh() {
    this.updateGreeting()
    Promise.all([
      this.loadCanteens(),
      this.loadData(),
      this.loadUnreadCount()
    ]).finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  updateGreeting() {
    const hour = new Date().getHours()
    let greetingTitle = '今日食堂吃点什么'
    let greetingSubtitle = '把热门菜品、常用入口和食堂分布放在同一个首页里，打开就能快速下单。'
    let currentMealLabel = '正在推荐'

    if (hour >= 5 && hour < 10) {
      greetingTitle = '早餐时间，先吃点热乎的'
      greetingSubtitle = '看看哪些食堂已经开窗，早点把早餐和上午能量一起安排好。'
      currentMealLabel = '早餐时段'
    } else if (hour >= 10 && hour < 14) {
      greetingTitle = '中午这一餐，选热销更稳'
      greetingSubtitle = '午高峰来了，首页先帮你挑出热门菜品和常去食堂。'
      currentMealLabel = '午餐高峰'
    } else if (hour >= 14 && hour < 17) {
      greetingTitle = '下午有点饿，来份轻食也不错'
      greetingSubtitle = '适合补一餐或者提前看看晚饭，少纠结，直接点进食堂分类。'
      currentMealLabel = '下午加餐'
    } else if (hour >= 17 && hour < 21) {
      greetingTitle = '晚餐时间，看看今天想吃什么'
      greetingSubtitle = '晚间热门和食堂状态都在这里，适合直接下单。'
      currentMealLabel = '晚餐时段'
    } else {
      greetingTitle = '夜深了，也许你还想来点吃的'
      greetingSubtitle = '先看看还有哪些食堂营业，或者把想吃的菜先收藏到心里。'
      currentMealLabel = '夜间浏览'
    }

    this.setData({
      greetingTitle,
      greetingSubtitle,
      currentMealLabel
    })
  },

  restoreLastVisitedCanteen() {
    const lastVisitedCanteenId = app.globalData?.categoryParams?.canteen_id || null
    this.setData({ lastVisitedCanteenId })
  },

  updateQuickTips() {
    const isLogin = !!app.globalData.isLogin
    this.setData({
      quickTips: {
        coupon: isLogin ? '领券下单更划算' : '登录后可查看可用优惠券',
        history: isLogin ? '回看最近浏览过的菜品' : '登录后可同步最近浏览记录'
      }
    })
  },

  async loadCanteens() {
    try {
      const res = await api.canteen.list()
      const canteens = Array.isArray(res) ? res : (res?.items || [])
      this.setData({ canteens })
    } catch (error) {
      console.error('加载食堂列表失败:', error)
      this.setData({ canteens: [] })
    }
  },

  async loadUnreadCount() {
    if (!app.globalData.isLogin) {
      this.setData({ unreadCount: 0 })
      return
    }

    try {
      const res = await api.notification.unreadCount()
      this.setData({
        unreadCount: res.count || 0
      })
    } catch (error) {
      console.error('加载未读消息数失败:', error)
    }
  },

  async loadData(forceRefresh = false) {
    try {
      this.setData({ loading: true, error: false })

      const dishesRes = await api.dish.list({
        page: 1,
        page_size: 20,
        sort_by: 'sales_count',
        order: 'desc',
        _t: Date.now()
      }).catch(() => [])

      const dishes = this.processDishes(dishesRes)
      const nextBannerDishes = dishes.filter(item => item.cover_url).slice(0, 8)
      const nextHotDishes = dishes.slice(0, 6)

      const shouldUpdateBanner = forceRefresh || this.hasBannerChanged(nextBannerDishes)
      const activeBannerIndex = 0
      const featuredDish = nextBannerDishes[activeBannerIndex] || null

      this.setData({
        bannerDishes: shouldUpdateBanner ? nextBannerDishes : this.data.bannerDishes,
        hotDishes: nextHotDishes,
        loading: false,
        activeBannerIndex,
        featuredDishName: featuredDish?.name || '',
        featuredDishMeta: featuredDish
          ? `月售${featuredDish.sales_count || 0} · ¥${featuredDish.price}`
          : ''
      })
    } catch (error) {
      console.error('加载数据失败:', error)
      this.setData({ loading: false, error: true })
    }
  },

  hasBannerChanged(nextBannerDishes = []) {
    const currentIds = (this.data.bannerDishes || []).map(item => String(item.dish_id)).join(',')
    const nextIds = nextBannerDishes.map(item => String(item.dish_id)).join(',')
    return currentIds !== nextIds
  },

  processDishes(data) {
    const dishes = Array.isArray(data) ? data : (data?.items || [])
    return dishes.map((item) => {
      let cover_url = '/static/default-dish.png'
      try {
        const sourceImages = Array.isArray(item?.image_urls) && item.image_urls.length
          ? item.image_urls
          : item?.images

        if (Array.isArray(sourceImages) && sourceImages.length > 0 && sourceImages[0]) {
          cover_url = util.formatImageUrl(sourceImages[0])
        } else if (typeof sourceImages === 'string') {
          const arr = JSON.parse(sourceImages)
          if (Array.isArray(arr) && arr.length > 0 && arr[0]) {
            cover_url = util.formatImageUrl(arr[0])
          }
        }
      } catch (e) {
        console.error('解析图片失败:', e)
      }

      return {
        ...item,
        cover_url,
        rating: item.rating || 0,
        sales_count: item.sales || 0
      }
    })
  },

  onRetry() {
    this.loadCanteens()
    this.loadData(true)
    this.loadUnreadCount()
  },

  onFeaturedChange(e) {
    const current = Number(e.detail.current || 0)
    const currentItem = (this.data.bannerDishes || [])[current]

    this.setData({
      activeBannerIndex: current,
      featuredDishName: currentItem?.name || '',
      featuredDishMeta: currentItem
        ? `月售${currentItem.sales_count || 0} · ¥${currentItem.price}`
        : ''
    })
  },

  onAdminAlertLater() {
    const appInstance = getApp()
    const wsManager = appInstance.globalData.wsManager
    if (wsManager && typeof wsManager.dismissAdminAlert === 'function') {
      wsManager.dismissAdminAlert(false)
    }
  },

  onAdminAlertView() {
    const appInstance = getApp()
    const wsManager = appInstance.globalData.wsManager
    if (wsManager && typeof wsManager.dismissAdminAlert === 'function') {
      wsManager.dismissAdminAlert(true)
    }
  },

  onActivityTap() {
    wx.navigateTo({
      url: '/pages/activity/activity'
    })
  },

  onCouponTap() {
    if (!app.globalData.isLogin) {
      wx.showToast({ title: '请先登录后查看优惠券', icon: 'none' })
      wx.navigateTo({ url: '/pages/auth/login' })
      return
    }
    wx.navigateTo({
      url: '/pages/coupon/coupon'
    })
  },

  onFAQTap() {
    wx.navigateTo({
      url: '/pages/faq/faq'
    })
  },

  onNotificationCenterTap() {
    if (!app.globalData.isLogin) {
      wx.showToast({ title: '请先登录后查看消息中心', icon: 'none' })
      wx.navigateTo({ url: '/pages/auth/login' })
      return
    }

    wx.navigateTo({
      url: '/pages/notification/notification'
    })
  },

  onHistoryTap() {
    if (!app.globalData.isLogin) {
      wx.showToast({ title: '请先登录后查看历史记录', icon: 'none' })
      wx.navigateTo({ url: '/pages/auth/login' })
      return
    }
    wx.navigateTo({
      url: '/pages/history/history'
    })
  },

  onCanteenQuickNav(e) {
    const index = e.currentTarget.dataset.index
    const { canteens } = this.data

    if (canteens && canteens[index]) {
      const canteen = canteens[index]
      const app = getApp()
      app.globalData.categoryParams = {
        canteen_id: canteen.canteen_id,
        timestamp: Date.now()
      }

      this.setData({
        lastVisitedCanteenId: canteen.canteen_id
      })

      wx.switchTab({
        url: '/pages/category/category'
      })
    } else {
      wx.showToast({
        title: '食堂信息加载中',
        icon: 'none'
      })
    }
  },

  onDishTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  async onAddToCart(e) {
    if (!app.globalData.isLogin) {
      wx.showToast({ title: '请先登录后添加购物车', icon: 'none' })
      wx.navigateTo({ url: '/pages/auth/login' })
      return
    }

    const item = e.currentTarget.dataset.item
    if (!item) return

    try {
      wx.showLoading({ title: '添加中...', mask: true })

      await api.cart.add({
        dish_id: item.dish_id,
        quantity: 1
      })

      wx.hideLoading()
      wx.showToast({
        title: `已添加到购物车`,
        icon: 'success'
      })
    } catch (error) {
      wx.hideLoading()
      console.error('添加购物车失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  onViewAllDishes() {
    wx.switchTab({
      url: '/pages/category/category'
    })
  }
})
