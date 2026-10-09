// pages/activity/activity.js
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
  if (item.status !== 1) {
    statusText = '已结束'
    statusClass = 'status-ended'
  } else if (startTime && endTime && now >= startTime && now <= endTime) {
    statusText = '进行中'
    statusClass = 'status-active'
  } else if (endTime && now > endTime) {
    statusText = '已结束'
    statusClass = 'status-ended'
  }

  const cover = util.formatImageUrl(item.cover_image || item.image || '') || '/static/logo.png'
  const content = item.content || item.description || '敬请关注活动详情'
  const subtitle = item.subtitle || item.summary || '校园食堂精彩活动'

  return {
    ...item,
    activity_id: item.activity_id || item.id,
    title: item.title || '校园活动',
    subtitle,
    content,
    cover_image: cover,
    organizer: item.organizer || '校园食堂',
    location: item.location || '校内食堂',
    contact_name: item.contact_name || '',
    contact_phone: item.contact_phone || '',
    start_time_text: item.start_time ? util.formatDate(item.start_time, 'YYYY-MM-DD HH:mm') : '待定',
    end_time_text: item.end_time ? util.formatDate(item.end_time, 'YYYY-MM-DD HH:mm') : '待定',
    status_text: statusText,
    status_class: statusClass,
    hero_tag: statusText === '进行中' ? 'HOT EVENT' : 'CAMPUS FOOD'
  }
}

Page({
  data: {
    activities: [],
    loading: true,
    refreshing: false,
    error: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad() {
    this.loadActivities()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (!this.data.loading) {
      this.loadActivities(false)
    }
  },

  onPullDownRefresh() {
    this.loadActivities(true).finally(() => {
      wx.stopPullDownRefresh()
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

  async loadActivities(isRefresh = false) {
    try {
      this.setData({ loading: !isRefresh, refreshing: isRefresh, error: false })
      const res = await api.activity.list()
      const list = Array.isArray(res)
        ? res
        : (Array.isArray(res?.items) ? res.items : (Array.isArray(res?.data) ? res.data : []))

      const activities = list
        .filter(item => Number(item.status) === 1 || item.status === undefined || item.status === null)
        .map(normalizeActivity)

      this.setData({
        activities,
        loading: false,
        refreshing: false
      })
    } catch (error) {
      console.error('加载活动列表失败:', error)
      this.setData({ loading: false, refreshing: false, error: true })
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },

  onActivityTap(e) {
    const activityId = e.currentTarget.dataset.id
    if (!activityId) {
      console.warn('活动ID缺失，点击数据：', e.currentTarget.dataset)
      return
    }
    wx.navigateTo({
      url: `/pages/activity/detail?id=${activityId}`
    })
  },

  onRetry() {
    this.loadActivities(false)
  }
})
