// pages/refund/detail.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    refundId: null,
    refund: null,
    loading: true,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options = {}) {
    if (!options.id) {
      wx.showToast({
        title: '退款信息错误',
        icon: 'none'
      })
      setTimeout(() => wx.navigateBack(), 1200)
      return
    }

    this.setData({ refundId: options.id })
    this.loadDetail()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (this.data.refundId) {
      this.loadDetail()
    }
  },

  async loadDetail() {
    try {
      this.setData({ loading: true })
      const list = await api.refund.list({})
      const refunds = Array.isArray(list) ? list : (list?.items || list?.data || [])
      const current = refunds.find(item => String(item.refund_id) === String(this.data.refundId))

      if (!current) {
        throw new Error('未找到退款记录')
      }

      this.setData({
        refund: this.processRefund(current),
        loading: false
      })
    } catch (error) {
      console.error('加载退款详情失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  processRefund(refund) {
    const statusMap = {
      pending: { text: '待审核', color: '#f08c00', bg: 'linear-gradient(135deg, #fff4e6 0%, #ffe8cc 100%)' },
      approved: { text: '已批准', color: '#2f9e44', bg: 'linear-gradient(135deg, #ebfbee 0%, #d3f9d8 100%)' },
      rejected: { text: '已拒绝', color: '#e03131', bg: 'linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%)' },
      completed: { text: '已完成', color: '#5c7cfa', bg: 'linear-gradient(135deg, #edf2ff 0%, #dbe4ff 100%)' }
    }

    const statusInfo = statusMap[refund.status] || { text: '未知状态', color: '#868e96', bg: '#f1f3f5' }
    return {
      ...refund,
      status_text: statusInfo.text,
      status_color: statusInfo.color,
      status_bg: statusInfo.bg,
      refund_amount_text: util.formatPrice(refund.refund_amount || 0),
      create_time_text: util.formatDate(refund.create_time, 'YYYY-MM-DD HH:mm:ss'),
      approve_time_text: refund.approve_time ? util.formatDate(refund.approve_time, 'YYYY-MM-DD HH:mm:ss') : '',
      order_no_text: refund.order?.order_no || refund.order_no || refund.order_id || '--'
    }
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

  onViewOrder() {
    const orderId = this.data.refund?.order_id
    if (!orderId) return
    wx.navigateTo({
      url: `/pages/order/detail?id=${orderId}`
    })
  }
})

