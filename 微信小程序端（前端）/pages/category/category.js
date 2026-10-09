// pages/category/category.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    canteens: [],           // 食堂列表
    currentCanteen: null,   // 当前选中的食堂
    dishes: [],            // 菜品列表（根据食堂动态加载）
    loading: true,
    loadingMore: false,
    page: 1,
    pageSize: 20,
    hasMore: true,
    total: 0,
    sortBy: 'default',
    order: 'desc',
    cartCount: 0,
    activeCanteenName: '',
    activeCanteenLocation: '',
    activeWindowCount: 0,
    sortLabel: '推荐优先',
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    console.log('=== 分类页面加载 ===')
    console.log('URL参数:', options)
    
    if (options.canteen_id) {
      this.setData({ currentCanteen: Number(options.canteen_id) })
      console.log('设置当前食堂ID:', Number(options.canteen_id))
    }
  },

  onShow() {
    if (app && typeof app.bindAdminAlertToPage === 'function') {
      app.bindAdminAlertToPage(this)
    }
    console.log('=== 分类页面显示 ===')

    const params = app.globalData.categoryParams
    if (params) {
      console.log('检测到全局参数:', params)
      const isRecent = params.timestamp && (Date.now() - params.timestamp < 5000)

      if (isRecent && params.canteen_id) {
        console.log('应用食堂参数')
        this.setData({
          currentCanteen: Number(params.canteen_id)
        })
        this.updateActiveCanteenMeta(this.data.canteens, Number(params.canteen_id))
      }

      delete app.globalData.categoryParams
    }

    this.loadCanteens()
    this.loadCartCount()
  },

  onPullDownRefresh() {
    this.loadCanteens().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  onReachBottom() {
    this.loadMore()
  },

  onAdminAlertLater() {
    const wsManager = getApp().globalData.wsManager
    if (wsManager && typeof wsManager.dismissAdminAlert === 'function') {
      wsManager.dismissAdminAlert(false)
    }
  },

  onAdminAlertView() {
    const wsManager = getApp().globalData.wsManager
    if (wsManager && typeof wsManager.dismissAdminAlert === 'function') {
      wsManager.dismissAdminAlert(true)
    }
  },

  // 1. 加载食堂列表
  async loadCanteens() {
    try {
      console.log('=== 1. 开始加载食堂列表 ===')
      const res = await api.canteen.list()
      console.log('食堂 API 响应:', res)
      
      let canteens = Array.isArray(res) ? res : (res?.items || [])
      console.log('解析后食堂数量:', canteens.length)
      
      this.setData({ canteens })
      this.updateActiveCanteenMeta(canteens, this.data.currentCanteen)
      
      if (!this.data.currentCanteen && canteens.length > 0) {
        this.setData({ currentCanteen: canteens[0].canteen_id })
        this.updateActiveCanteenMeta(canteens, canteens[0].canteen_id)
        console.log('默认选中第一个食堂:', canteens[0].canteen_id)
      }
      
      await this.loadDishes(true)
      
      console.log('=== 食堂加载完成 ===')
    } catch (error) {
      console.error('=== 加载食堂失败 ===', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 2. 加载菜品列表（根据选中的食堂）
  async loadDishes(reset = false) {
    try {
      if (reset) {
        this.setData({ loading: true, page: 1, hasMore: true })
      }
      
      const { page, pageSize, currentCanteen, sortBy, order } = this.data
      
      console.log('=== 2. 开始加载菜品列表 ===')
      console.log('当前食堂ID:', currentCanteen)
      
      const params = {
        page,
        page_size: pageSize
      }
      
      if (currentCanteen) {
        params.canteen_id = currentCanteen
      }
      
      // 排序
      if (sortBy === 'sales') {
        params.sort_by = 'sales_count'
        params.order = order
      } else if (sortBy === 'price') {
        params.sort_by = 'price'
        params.order = order
      }
      
      console.log('请求参数:', params)
      
      const res = await api.dish.list(params)
      console.log('菜品 API 响应:', res)
      
      let items = []
      let total = 0
      
      if (res && res.items) {
        items = res.items || []
        total = res.total || 0
      } else if (Array.isArray(res)) {
        items = res
        total = res.length
      }
      
      console.log('解析后菜品数量:', items.length)
      console.log('总数:', total)
      
      const dishes = items.map(d => this.processDish(d))
      const finalDishes = reset ? dishes : [...this.data.dishes, ...dishes]
      const hasMore = finalDishes.length < total
      
      this.setData({
        dishes: finalDishes,
        total,
        hasMore,
        loading: false,
        sortLabel: this.getSortLabel(sortBy, order)
      })
      
      console.log('=== 菜品加载完成 ===')
    } catch (error) {
      console.error('=== 加载菜品失败 ===', error)
      this.setData({ loading: false })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  processDish(dish) {
    let cover_url = '/static/default-dish.png'
    try {
      if (dish?.images) {
        if (typeof dish.images === 'string') {
          const arr = JSON.parse(dish.images)
          if (Array.isArray(arr) && arr.length > 0 && arr[0]) {
            cover_url = util.formatImageUrl(arr[0])
          }
        } else if (Array.isArray(dish.images) && dish.images.length > 0) {
          cover_url = util.formatImageUrl(dish.images[0])
        }
      }
    } catch (e) {
      console.error('解析图片失败:', e)
    }
    
    return {
      ...dish,
      cover_url,
      sales_count: dish.sales || dish.sales_count || 0
    }
  },

  updateActiveCanteenMeta(canteens = [], canteenId = null) {
    const matched = (canteens || []).find(item => String(item.canteen_id) === String(canteenId))
    if (!matched) {
      this.setData({
        activeCanteenName: '',
        activeCanteenLocation: '',
        activeWindowCount: 0
      })
      return
    }

    const locationParts = [matched.building, matched.floor].filter(Boolean)
    this.setData({
      activeCanteenName: matched.canteen_name || '',
      activeCanteenLocation: locationParts.join(' · '),
      activeWindowCount: matched.window_count || 0
    })
  },

  getSortLabel(sortBy, order) {
    if (sortBy === 'sales') {
      return order === 'desc' ? '销量优先' : '销量回看'
    }

    if (sortBy === 'price') {
      return order === 'desc' ? '价格从高到低' : '价格从低到高'
    }

    return '推荐优先'
  },

  async loadCartCount() {
    if (!app.globalData.isLogin) return
    
    try {
      const res = await api.cart.list()
      const items = Array.isArray(res) ? res : (res?.items || [])
      const count = items.reduce((sum, item) => sum + (item.quantity || 0), 0)
      this.setData({ cartCount: count })
    } catch (error) {
      console.error('加载购物车失败:', error)
    }
  },

  // 点击食堂 → 重新加载菜品
  onCanteenTap(e) {
    const id = e.currentTarget.dataset.id
    console.log('\n========== 点击食堂 ==========')
    console.log('选中食堂ID:', id)
    
    this.setData({ 
      currentCanteen: id,
      dishes: []
    })
    this.updateActiveCanteenMeta(this.data.canteens, id)
    
    this.loadDishes(true)
  },

  // 点击排序
  onSortChange(e) {
    const sortBy = e.currentTarget.dataset.sort
    const currentSort = this.data.sortBy
    
    let order = 'desc'
    if (sortBy === currentSort && sortBy !== 'default') {
      order = this.data.order === 'desc' ? 'asc' : 'desc'
    }
    
    this.setData({ sortBy, order })
    this.loadDishes(true)
  },

  // 加载更多
  loadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) return
    
    this.setData({ 
      loadingMore: true,
      page: this.data.page + 1
    })
    
    this.loadDishes(false).finally(() => {
      this.setData({ loadingMore: false })
    })
  },

  // 添加到购物车
  async onAddToCart(e) {
    if (!app.globalData.isLogin) {
      wx.navigateTo({ url: '/pages/auth/login' })
      return
    }
    
    const item = e.currentTarget.dataset.item
    if (!item) return
    
    try {
      await api.cart.add({
        dish_id: item.dish_id,
        quantity: 1
      })
      
      wx.showToast({ title: '已添加', icon: 'success' })
      this.loadCartCount()
    } catch (error) {
      console.error('添加购物车失败:', error)
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },

  // 点击菜品
  onDishTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  // 点击搜索
  onSearchTap() {
    wx.navigateTo({
      url: '/pages/search/search'
    })
  },

  // 去购物车
  onGoToCart() {
    wx.switchTab({
      url: '/pages/cart/cart'
    })
  }
})
