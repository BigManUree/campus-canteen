// pages/refund/list.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    refunds: [],
    loading: true,
    refreshing: false,
    
    // 状态筛选
    currentStatus: 'all', // all, pending, approved, rejected, completed
    statusOptions: [
      { value: 'all', label: '全部' },
      { value: 'pending', label: '待审核' },
      { value: 'approved', label: '已批准' },
      { value: 'rejected', label: '已拒绝' },
      { value: 'completed', label: '已完成' }
    ],
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad() {
    this.loadRefunds()
  },

  onShow() {
    app.bindAdminAlertToPage(this)

    // 从详情页返回时刷新列表
    if (this.data.refunds.length > 0) {
      this.loadRefunds()
    }
  },

  onPullDownRefresh() {
    this.loadRefunds(true)
  },

  // 加载退款列表
  async loadRefunds(isRefresh = false) {
    try {
      if (isRefresh) {
        this.setData({ refreshing: true })
      } else {
        this.setData({ loading: true })
      }
      
      const params = {}
      if (this.data.currentStatus !== 'all') {
        params.status = this.data.currentStatus
      }
      
      const result = await api.refund.list(params)
      const list = Array.isArray(result) ? result : (result?.items || result?.data || [])
      
      // 处理退款数据
      const refunds = list.map(refund => this.processRefundData(refund))
      
      this.setData({
        refunds,
        loading: false,
        refreshing: false
      })
      
      if (isRefresh) {
        wx.stopPullDownRefresh()
      }
      
    } catch (error) {
      console.error('加载退款列表失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
      this.setData({ 
        loading: false,
        refreshing: false
      })
    }
  },

  // 处理退款数据
  processRefundData(refund) {
    const statusInfo = this.getStatusInfo(refund.status)
    
    return {
      ...refund,
      refund_amount_text: util.formatPrice(refund.refund_amount || 0),
      create_time_text: util.formatDate(refund.create_time, 'MM-DD HH:mm'),
      status_text: statusInfo.text,
      status_color: statusInfo.color,
      status_bg: statusInfo.bg,
      reason_category_text: this.getReasonCategoryText(refund.reason_category)
    }
  },

  // 获取状态信息
  getStatusInfo(status) {
    const statusMap = {
      pending: {
        text: '待审核',
        color: '#ff9500',
        bg: 'linear-gradient(135deg, #fff4e6 0%, #ffe8cc 100%)'
      },
      approved: {
        text: '已批准',
        color: '#34c759',
        bg: 'linear-gradient(135deg, #e6ffe6 0%, #ccffcc 100%)'
      },
      rejected: {
        text: '已拒绝',
        color: '#ff4757',
        bg: 'linear-gradient(135deg, #ffe8e8 0%, #ffd6d6 100%)'
      },
      completed: {
        text: '已完成',
        color: '#8e8e93',
        bg: 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)'
      }
    }
    
    return statusMap[status] || {
      text: '未知',
      color: '#8e8e93',
      bg: '#f5f5f5'
    }
  },

  // 获取退款原因分类文本
  getReasonCategoryText(category) {
    const categoryMap = {
      dont_want: '不想要了',
      too_long: '等太久',
      quality: '质量问题',
      other: '其他原因'
    }
    return categoryMap[category] || '未知原因'
  },

  // 切换状态筛选
  onStatusChange(e) {
    const status = e.currentTarget.dataset.status
    if (status === this.data.currentStatus) return
    
    this.setData({ currentStatus: status })
    this.loadRefunds()
  },

  // 查看退款详情
  onRefundDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/refund/detail?id=${id}`
    })
  },

  // 查看订单详情
  onOrderDetail(e) {
    const orderId = e.currentTarget.dataset.orderId
    wx.navigateTo({
      url: `/pages/order/detail?id=${orderId}`
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
  }
})

