// pages/activity/detail.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

function normalizeActivity(item = {}) {
  const start = item.start_time ? new Date(item.start_time) : null
  const end = item.end_time ? new Date(item.end_time) : null
  const now = Date.now()
  const startTime = start && !isNaN(start.getTime()) ? start.getTime() : 0
  const endTime = end && !isNaN(end.getTime()) ? end.getTime() : 0

  let statusText = '活动预告'
  let statusClass = 'status-upcoming'
  if (Number(item.status) !== 1) {
    statusText = '已结束'
    statusClass = 'status-ended'
  } else if (startTime && endTime && now >= startTime && now <= endTime) {
    statusText = '进行中'
    statusClass = 'status-active'
  } else if (endTime && now > endTime) {
    statusText = '已结束'
    statusClass = 'status-ended'
  }

  return {
    ...item,
    activity_id: item.activity_id || item.id,
    title: item.title || '校园活动',
    subtitle: item.subtitle || item.summary || '食堂主题活动',
    content: item.content || item.description || '暂无活动详情',
    cover_image: util.formatImageUrl(item.cover_image || item.image || '') || '/static/logo.png',
    organizer: item.organizer || '校园食堂',
    location: item.location || '校内食堂',
    contact_name: item.contact_name || '食堂服务台',
    contact_phone: item.contact_phone || '请到店咨询',
    start_time_text: item.start_time ? util.formatDate(item.start_time, 'YYYY-MM-DD HH:mm') : '待定',
    end_time_text: item.end_time ? util.formatDate(item.end_time, 'YYYY-MM-DD HH:mm') : '待定',
    status_text: statusText,
    status_class: statusClass
  }
}

Page({
  data: {
    activityId: null,
    activity: null,
    loading: true,
    error: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    const activityId = options.id
    if (!activityId) {
      wx.showToast({ title: '活动不存在', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 800)
      return
    }
    this.setData({ activityId })
    this.loadDetail()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
  },

  onPullDownRefresh() {
    this.loadDetail().finally(() => wx.stopPullDownRefresh())
  },

  onShareAppMessage() {
    const activity = this.data.activity || {}
    return {
      title: activity.title || '校园活动',
      path: `/pages/activity/detail?id=${this.data.activityId}`,
      imageUrl: activity.cover_image || ''
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

  async loadDetail() {
    try {
      this.setData({ loading: true, error: false })
      const listRes = await api.activity.list()
      const list = Array.isArray(listRes)
        ? listRes
        : (Array.isArray(listRes?.items) ? listRes.items : (Array.isArray(listRes?.data) ? listRes.data : []))
      const raw = list.find(item => String(item.activity_id || item.id) === String(this.data.activityId))
      if (!raw) {
        this.setData({ loading: false, error: true })
        wx.showToast({ title: '活动不存在', icon: 'none' })
        return
      }
      this.setData({
        activity: normalizeActivity(raw),
        loading: false,
        error: false
      })
    } catch (err) {
      console.error('加载活动详情失败:', err)
      this.setData({ loading: false, error: true })
      wx.showToast({ title: err.message, icon: 'none' })
    }
  },

  onBack() {
    wx.navigateBack({ delta: 1 })
  },

  onPreviewImage() {
    const current = this.data.activity?.cover_image
    if (!current) return
    wx.previewImage({ current, urls: [current] })
  },

  onCallContact() {
    const phone = this.data.activity?.contact_phone
    if (!phone || phone === '请到店咨询') {
      wx.showToast({ title: '暂无联系电话', icon: 'none' })
      return
    }
    wx.makePhoneCall({ phoneNumber: phone })
  },

  onRetry() {
    this.loadDetail()
  }
})

