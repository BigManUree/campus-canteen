// pages/favorite/favorite.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    allFavorites: [],
    favorites: [],
    loading: true,
    loadingMore: false,
    page: 1,
    pageSize: 10,
    hasMore: true,
    error: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad() {
    this.loadFavorites()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (!this.data.allFavorites || this.data.allFavorites.length === 0) {
      this.loadFavorites()
    } else {
      this.applyPagination(true)
    }
  },

  onPullDownRefresh() {
    this.loadFavorites().finally(() => {
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

  // 加载收藏列表
  async loadFavorites() {
    try {
      this.setData({ loading: true, page: 1, hasMore: true, error: false })
      const res = await api.favorite.list()
      const list = Array.isArray(res) ? res : (res && res.items) ? res.items : []
      const allFavorites = list.map(f => {
        const dish = f.dish || {}
        return {
          ...f,
          cover_url: this.getDishCoverUrl(dish),
          dish_name: dish.name,
          dish_price: dish.price
        }
      })
      this.setData({
        allFavorites,
        loading: false
      })
      this.applyPagination(true)
    } catch (error) {
      console.error('加载收藏失败:', error)
      this.setData({ loading: false, error: true })
    }
  },

  onRetry() {
    this.loadFavorites()
  },

  getDishCoverUrl(dish) {
    const fallback = '/static/logo.png'
    if (!dish) return fallback
    const raw = dish.images
    if (!raw) return fallback
    
    if (Array.isArray(raw)) {
      const url = raw[0] || fallback
      return util.formatImageUrl(url)
    }
    
    if (typeof raw === 'string') {
      const s = raw.trim()
      if (!s) return fallback
      if (s.startsWith('[')) {
        try {
          const arr = JSON.parse(s)
          if (Array.isArray(arr) && arr.length > 0) {
            const url = arr[0] || fallback
            return util.formatImageUrl(url)
          }
        } catch (e) {}
      }
      return util.formatImageUrl(s)
    }
    return fallback
  },

  applyPagination(reset = false) {
    const { allFavorites, page, pageSize } = this.data
    const nextPage = reset ? 1 : page
    const end = nextPage * pageSize
    const slice = (allFavorites || []).slice(0, end)
    const hasMore = slice.length < (allFavorites || []).length
    this.setData({ favorites: slice, page: nextPage, hasMore })
  },

  loadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) return
    this.setData({ loadingMore: true, page: this.data.page + 1 })
    this.applyPagination(false)
    setTimeout(() => this.setData({ loadingMore: false }), 200)
  },

  // 查看菜品详情
  onDishTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  // 取消收藏
  async onRemoveFavorite(e) {
    const dishId = e.currentTarget.dataset.dishId
    
    if (!dishId) {
      wx.showToast({ title: '菜品信息错误', icon: 'none' })
      return
    }

    wx.showModal({
      title: '提示',
      content: '确定要取消收藏吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            // 修复：直接传递 dishId，而不是对象
            await api.favorite.remove(dishId)
            wx.showToast({ title: '已取消收藏', icon: 'success' })
            setTimeout(() => {
              this.loadFavorites()
            }, 500)
          } catch (error) {
            console.error('取消收藏失败:', error)
            wx.showToast({ 
              title: error.message, 
              icon: 'none' 
            })
          }
        }
      }
    })
  }
})
