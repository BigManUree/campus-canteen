// pages/address/address.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    addresses: [],
    loading: true,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad() {
    this.loadAddresses()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    this.loadAddresses()
  },

  onPullDownRefresh() {
    this.loadAddresses().finally(() => {
      wx.stopPullDownRefresh()
    })
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

  // 加载地址列表
  async loadAddresses() {
    try {
      this.setData({ loading: true })
      const res = await api.address.list()
      this.setData({
        addresses: res || [],
        loading: false
      })
    } catch (error) {
      console.error('加载地址失败:', error)
      this.setData({ loading: false })
    }
  },

  // 添加地址
  onAddAddress() {
    wx.navigateTo({
      url: '/pages/address/edit'
    })
  },

  // 编辑地址
  onEditAddress(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/address/edit?id=${id}`
    })
  },

  // 删除地址
  async onDeleteAddress(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '提示',
      content: '确定要删除这个地址吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.address.delete(id)
            wx.showToast({ title: '已删除', icon: 'success' })
            this.loadAddresses()
          } catch (error) {
            console.error('删除地址失败:', error)
          }
        }
      }
    })
  },

  // 设置默认地址
  async onSetDefault(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.address.update(id, { is_default: 1 })
      wx.showToast({ title: '已设置默认', icon: 'success' })
      this.loadAddresses()
    } catch (error) {
      console.error('设置默认地址失败:', error)
    }
  }
})
