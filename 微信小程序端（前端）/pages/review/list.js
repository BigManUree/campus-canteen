// pages/review/list.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    dishId: null,
    dishName: '',
    reviews: [],
    page: 1,
    pageSize: 10,
    total: 0,
    loading: true,
    loadingMore: false,
    refreshing: false,
    hasMore: true,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options = {}) {
    const dishId = Number(options.dish_id)
    const dishName = options.dish_name ? decodeURIComponent(options.dish_name) : ''

    if (!dishId) {
      wx.showToast({
        title: '评价信息错误',
        icon: 'none'
      })
      setTimeout(() => wx.navigateBack(), 1200)
      return
    }

    this.setData({ dishId, dishName })
    if (dishName) {
      wx.setNavigationBarTitle({
        title: `${dishName}评价`
      })
    }
    this.loadReviews(true)
  },

  onShow() {
    app.bindAdminAlertToPage(this)
  },

  onPullDownRefresh() {
    this.loadReviews(true).finally(() => {
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

  async loadReviews(reset = false) {
    if (!this.data.dishId) return

    const nextPage = reset ? 1 : this.data.page

    try {
      if (reset) {
        this.setData({
          loading: true,
          refreshing: true,
          page: 1,
          hasMore: true
        })
      } else {
        this.setData({ loadingMore: true })
      }

      const res = await api.review.list(this.data.dishId, {
        page: nextPage,
        page_size: this.data.pageSize
      })

      const list = Array.isArray(res) ? res : (res?.items || res?.data || [])
      const total = Array.isArray(res) ? list.length : (res?.total || res?.count || 0)
      const mapped = list.map(item => this.normalizeReview(item))
      const reviews = reset ? mapped : [...this.data.reviews, ...mapped]
      const resolvedTotal = total || reviews.length
      const hasMore = list.length >= this.data.pageSize && reviews.length < resolvedTotal

      this.setData({
        reviews,
        total: resolvedTotal,
        page: nextPage,
        hasMore,
        loading: false,
        loadingMore: false,
        refreshing: false
      })
    } catch (error) {
      console.error('加载全部评价失败:', error)
      this.setData({
        loading: false,
        loadingMore: false,
        refreshing: false
      })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  loadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) return
    this.setData({ page: this.data.page + 1 })
    this.loadReviews(false)
  },

  normalizeReview(review = {}) {
    const isAnonymous = review.is_anonymous === true || review.is_anonymous === 1
    return {
      ...review,
      is_anonymous: isAnonymous,
      user_name: this.getReviewDisplayName(review, isAnonymous),
      user_avatar: this.getReviewAvatar(review, isAnonymous),
      create_time_text: util.formatDate(review.create_time, 'YYYY-MM-DD HH:mm'),
      rating: review.rating || 5,
      images: this.parseReviewImages(review.images),
      reply_content: this.getReviewReplyContent(review),
      reply_time_text: this.getReviewReplyTime(review)
    }
  },

  getReviewDisplayName(review = {}, isAnonymous = null) {
    const hidden = isAnonymous === null
      ? (review.is_anonymous === true || review.is_anonymous === 1)
      : isAnonymous
    if (hidden) {
      return '匿名用户'
    }
    return review.user?.nickname || '实名用户'
  },

  getReviewAvatar(review = {}, isAnonymous = null) {
    const hidden = isAnonymous === null
      ? (review.is_anonymous === true || review.is_anonymous === 1)
      : isAnonymous
    if (hidden) {
      return '/static/default-avatar.png'
    }
    return review.user?.avatar || '/static/default-avatar.png'
  },

  getReviewReplyContent(review = {}) {
    return review.reply_content || ''
  },

  getReviewReplyTime(review = {}) {
    return review.reply_time ? util.formatDate(review.reply_time, 'YYYY-MM-DD HH:mm') : ''
  },

  parseReviewImages(images) {
    if (!images) return []
    if (Array.isArray(images)) return images
    if (typeof images === 'string') {
      try {
        const parsed = JSON.parse(images)
        return Array.isArray(parsed) ? parsed : []
      } catch (e) {
        return images.split(',').map(img => img.trim()).filter(Boolean)
      }
    }
    return []
  },

  onPreviewReviewImage(e) {
    const images = e.currentTarget.dataset.images || []
    const index = e.currentTarget.dataset.index || 0
    if (!images.length) return
    wx.previewImage({
      urls: images,
      current: images[index]
    })
  }
})

