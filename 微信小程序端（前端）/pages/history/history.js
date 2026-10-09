// pages/history/history.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    histories: [],
    loading: true,
    loadingMore: false,
    page: 1,
    pageSize: 20,
    hasMore: true,
    error: false,
    total: 0,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad() {
    this.loadHistories()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    // 每次显示时刷新数据
    this.loadHistories()
  },

  onPullDownRefresh() {
    this.loadHistories().finally(() => {
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

  // 加载历史记录
  async loadHistories(reset = true) {
    try {
      if (reset) {
        this.setData({ loading: true, page: 1, hasMore: true, error: false })
      }

      const { page, pageSize } = this.data
      const res = await api.history.list(page, pageSize)
      
      let items = []
      let total = 0
      
      if (res && res.items) {
        items = res.items || []
        total = res.total || 0
      } else if (Array.isArray(res)) {
        items = res
        total = res.length
      }

      // 处理历史记录数据
      const histories = items.map(h => {
        const dish = h.dish || {}
        return {
          ...h,
          browse_id: h.browse_id || h.id,
          dish_id: dish.dish_id || dish.id,
          cover_url: this.getDishCoverUrl(dish),
          dish_name: dish.name || '未知菜品',
          dish_price: dish.price || 0,
          browse_time_text: util.formatDate(h.browse_time || h.create_time, 'MM-DD HH:mm')
        }
      })

      const finalHistories = reset ? histories : [...this.data.histories, ...histories]
      const hasMore = finalHistories.length < total

      this.setData({
        histories: finalHistories,
        total,
        hasMore,
        loading: false
      })
    } catch (error) {
      console.error('加载历史失败:', error)
      this.setData({ loading: false, error: true })
    }
  },

  onRetry() {
    this.loadHistories()
  },

  getDishCoverUrl(dish) {
    const fallback = '/static/default-dish.png'
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

  loadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) return
    
    this.setData({ 
      loadingMore: true,
      page: this.data.page + 1
    })
    
    this.loadHistories(false).finally(() => {
      this.setData({ loadingMore: false })
    })
  },

  // 查看菜品详情
  onDishTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  // 删除单条记录
  async onRemoveHistory(e) {
    const dishId = e.currentTarget.dataset.dishId
    
    if (!dishId) {
      wx.showToast({ title: '菜品信息错误', icon: 'none' })
      return
    }

    try {
      await api.history.remove(dishId)
      wx.showToast({ title: '已删除', icon: 'success' })
      
      // 刷新列表
      setTimeout(() => {
        this.loadHistories()
      }, 500)
    } catch (error) {
      console.error('删除失败:', error)
      wx.showToast({ 
        title: error.message, 
        icon: 'none' 
      })
    }
  },

  // 清空历史
  onClearHistory() {
    if (this.data.histories.length === 0) {
      wx.showToast({ title: '暂无浏览记录', icon: 'none' })
      return
    }

    wx.showModal({
      title: '清空浏览历史',
      content: '确定要清空所有浏览记录吗？此操作不可恢复。',
      confirmText: '清空',
      confirmColor: '#ff4757',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '清空中...', mask: true })
            await api.history.clear()
            wx.hideLoading()
            wx.showToast({ title: '已清空', icon: 'success' })
            
            // 清空本地数据
            this.setData({ 
              histories: [],
              total: 0,
              page: 1,
              hasMore: false
            })
          } catch (error) {
            wx.hideLoading()
            console.error('清空失败:', error)
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
