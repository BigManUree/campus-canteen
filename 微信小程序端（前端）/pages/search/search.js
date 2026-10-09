// pages/search/search.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    keyword: '',
    autoFocus: true,
    hasSearched: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    },
    
    // Tab
    activeTab: 'all',
    
    // 搜索结果
    dishes: [],
    canteens: [],
    totalCount: 0,
    dishCount: 0,
    canteenCount: 0,
    
    // 分页
    page: 1,
    pageSize: 20,
    hasMore: false,
    
    // 状态
    loading: false,
    loadingMore: false,
    
    // 搜索建议
    suggestions: [],
    
    // 热门搜索
    hotKeywords: [],
    
    // 搜索历史
    searchHistory: []
  },

  // 防抖定时器
  suggestTimer: null,

  onLoad(options) {
    // 从参数获取关键词
    if (options.keyword) {
      this.setData({ 
        keyword: options.keyword,
        autoFocus: false
      })
      this.doSearch()
    }
    
    // 加载热门搜索
    this.loadHotKeywords()
    
    // 加载搜索历史
    this.loadSearchHistory()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
  },

  onUnload() {
    // 清理定时器
    if (this.suggestTimer) {
      clearTimeout(this.suggestTimer)
    }
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

  // 输入事件
  onInput(e) {
    const keyword = e.detail.value.trim()
    this.setData({ keyword })
    
    // 清空时重置状态
    if (!keyword) {
      this.setData({
        hasSearched: false,
        suggestions: []
      })
      if (this.suggestTimer) {
        clearTimeout(this.suggestTimer)
      }
      return
    }
    
    // 防抖获取搜索建议
    if (this.suggestTimer) {
      clearTimeout(this.suggestTimer)
    }
    
    this.suggestTimer = setTimeout(() => {
      this.loadSuggestions(keyword)
    }, 300)
  },

  // 搜索确认
  onSearch() {
    const { keyword } = this.data
    if (!keyword) {
      wx.showToast({
        title: '请输入搜索关键词',
        icon: 'none'
      })
      return
    }
    
    this.doSearch()
  },

  // 执行搜索
  async doSearch() {
    const { keyword, activeTab } = this.data
    
    if (!keyword) return
    
    try {
      this.setData({ 
        loading: true,
        hasSearched: true,
        page: 1,
        suggestions: []
      })
      
      // 调用搜索接口
      const res = await api.search.all(keyword, {
        type: activeTab,
        page: 1,
        page_size: this.data.pageSize
      })
      
      // 处理菜品数据
      const dishes = this.processDishes(res.dishes || [])
      
      this.setData({
        dishes,
        canteens: res.canteens || [],
        totalCount: res.total || 0,
        dishCount: (res.dishes || []).length,
        canteenCount: (res.canteens || []).length,
        hasMore: res.has_more || false,
        loading: false
      })
      
      // 添加到搜索历史（静默）
      api.search.addHistory(keyword, activeTab)
      
      // 刷新搜索历史
      this.loadSearchHistory()
      
    } catch (error) {
      console.error('搜索失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 处理菜品数据
  processDishes(dishes) {
    return dishes.map((item) => {
      let cover_url = '/static/default-dish.png'
      try {
        if (item?.images) {
          if (typeof item.images === 'string') {
            const arr = JSON.parse(item.images)
            if (Array.isArray(arr) && arr.length > 0 && arr[0]) {
              cover_url = util.formatImageUrl(arr[0])
            }
          } else if (Array.isArray(item.images) && item.images.length > 0) {
            cover_url = util.formatImageUrl(item.images[0])
          }
        }
      } catch (e) {
        console.error('解析图片失败:', e)
      }
      
      return {
        ...item,
        cover_url
      }
    })
  },

  // 加载搜索建议
  async loadSuggestions(keyword) {
    if (!keyword) return
    
    try {
      const res = await api.search.suggest(keyword, 10)
      this.setData({
        suggestions: res.suggestions || []
      })
    } catch (error) {
      console.error('加载搜索建议失败:', error)
    }
  },

  // 加载热门搜索
  async loadHotKeywords() {
    try {
      const res = await api.search.hot(10)
      this.setData({
        hotKeywords: res.keywords || []
      })
    } catch (error) {
      console.error('加载热门搜索失败:', error)
    }
  },

  // 加载搜索历史
  async loadSearchHistory() {
    if (!app.globalData.isLogin) return
    
    try {
      const res = await api.search.history(20)
      this.setData({
        searchHistory: res.history || []
      })
    } catch (error) {
      console.error('加载搜索历史失败:', error)
    }
  },

  // Tab切换
  onTabChange(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.activeTab) return
    
    this.setData({ 
      activeTab: tab,
      page: 1
    })
    
    this.doSearch()
  },

  // 清空输入
  onClear() {
    this.setData({
      keyword: '',
      hasSearched: false,
      suggestions: []
    })
  },

  // 取消搜索
  onCancel() {
    wx.navigateBack()
  },

  // 点击搜索建议
  onSuggestTap(e) {
    const text = e.currentTarget.dataset.text
    this.setData({ keyword: text })
    this.doSearch()
  },

  // 点击热门搜索
  onHotTap(e) {
    const keyword = e.currentTarget.dataset.keyword
    this.setData({ keyword })
    this.doSearch()
  },

  // 点击搜索历史
  onHistoryTap(e) {
    const keyword = e.currentTarget.dataset.keyword
    this.setData({ keyword })
    this.doSearch()
  },

  // 清空搜索历史
  onClearHistory() {
    wx.showModal({
      title: '提示',
      content: '确定清空搜索历史吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.search.clearHistory()
            this.setData({ searchHistory: [] })
            wx.showToast({
              title: '已清空',
              icon: 'success'
            })
          } catch (error) {
            console.error('清空搜索历史失败:', error)
            wx.showToast({
              title: error.message,
              icon: 'none'
            })
          }
        }
      }
    })
  },

  // 加载更多
  async onLoadMore() {
    const { loadingMore, hasMore, keyword, activeTab, page, pageSize } = this.data
    
    if (loadingMore || !hasMore) return
    
    try {
      this.setData({ loadingMore: true })
      
      const nextPage = page + 1
      const res = await api.search.all(keyword, {
        type: activeTab,
        page: nextPage,
        page_size: pageSize
      })
      
      // 处理新数据
      const newDishes = this.processDishes(res.dishes || [])
      
      this.setData({
        dishes: [...this.data.dishes, ...newDishes],
        canteens: [...this.data.canteens, ...(res.canteens || [])],
        page: nextPage,
        hasMore: res.has_more || false,
        loadingMore: false
      })
      
    } catch (error) {
      console.error('加载更多失败:', error)
      this.setData({ loadingMore: false })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 点击菜品
  onDishTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  // 点击档口
  onCanteenTap(e) {
    const id = e.currentTarget.dataset.id
    const name = e.currentTarget.dataset.name
    wx.navigateTo({
      url: `/pages/canteen/detail?id=${id}&name=${name}`
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
      wx.showLoading({ title: '添加中...', mask: true })
      
      await api.cart.add({
        dish_id: item.dish_id,
        quantity: 1
      })
      
      wx.hideLoading()
      wx.showToast({
        title: '已添加到购物车',
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
  }
})

