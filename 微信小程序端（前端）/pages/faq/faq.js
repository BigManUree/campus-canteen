// pages/faq/faq.js
const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    categories: ['全部', '订单相关', '支付相关', '配送相关', '其他问题'],
    activeCategory: '全部',
    faqList: [],
    filteredList: [],
    loading: true,
    expandedIds: [], // 展开的FAQ ID列表
    searchKeyword: '', // 搜索关键词
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad() {
    this.loadFAQList()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
  },

  // 加载FAQ列表
  async loadFAQList() {
    try {
      this.setData({ loading: true })
      
      const res = await api.faq.list()
      const faqList = res.items || res || []
      
      this.setData({
        faqList: faqList,
        filteredList: faqList,
        loading: false
      })
      
    } catch (error) {
      console.error('加载FAQ失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 搜索输入
  onSearchInput(e) {
    const keyword = e.detail.value
    this.setData({ searchKeyword: keyword })
    this.filterList()
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

  // 清除搜索
  onClearSearch() {
    this.setData({ searchKeyword: '' })
    this.filterList()
  },

  // 切换分类
  onCategoryChange(e) {
    const category = e.currentTarget.dataset.category
    
    this.setData({
      activeCategory: category,
      expandedIds: [] // 切换分类时收起所有
    })
    
    this.filterList()
  },

  // 过滤列表
  filterList() {
    const { faqList, activeCategory, searchKeyword } = this.data
    
    let filteredList = faqList
    
    // 按分类过滤
    if (activeCategory !== '全部') {
      filteredList = filteredList.filter(item => item.category === activeCategory)
    }
    
    // 按关键词搜索
    if (searchKeyword) {
      const keyword = searchKeyword.toLowerCase()
      filteredList = filteredList.filter(item => {
        const question = (item.question || '').toLowerCase()
        const answer = (item.answer || '').toLowerCase()
        return question.includes(keyword) || answer.includes(keyword)
      })
    }
    
    this.setData({ filteredList })
  },

  // 切换FAQ展开/收起
  onToggleFAQ(e) {
    const id = e.currentTarget.dataset.id
    const { expandedIds } = this.data
    const numId = typeof id === 'string' ? parseInt(id, 10) : id
    const index = expandedIds.indexOf(numId)

    if (index > -1) {
      expandedIds.splice(index, 1)
    } else {
      expandedIds.push(numId)
    }

    this.setData({
      expandedIds: [...expandedIds]
    })
  }
})

