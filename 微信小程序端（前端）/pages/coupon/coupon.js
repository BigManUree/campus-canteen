// pages/coupon/coupon.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    // 原始数据
    allAvailableCoupons: [],
    allMyCoupons: [],
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    },

    tabIndex: 0, // 0-可领取, 1-我的优惠券
    availableCoupons: [], // 可领取的优惠券（分页后）
    myCoupons: [], // 我的优惠券（分页后）
    status: 0, // 0-未使用, 1-已使用, 2-已过期
    loading: true,
    loadingMore: false,
    page: 1,
    pageSize: 10,
    hasMore: true,
    errorAvailable: false,
    errorMy: false
  },

  onLoad() {
    if (!app.globalData.isLogin) {
      wx.showModal({
        title: '提示',
        content: '请先登录',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({
              url: '/pages/auth/login'
            })
          } else {
            wx.navigateBack()
          }
        }
      })
      return
    }
    this.loadAvailableCoupons()
    this.loadMyCoupons()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (app.globalData.isLogin) {
      this.loadMyCoupons()
    }
  },

  onPullDownRefresh() {
    const task = this.data.tabIndex === 0 ? this.loadAvailableCoupons() : this.loadMyCoupons()
    task.finally(() => wx.stopPullDownRefresh())
  },

  onTabChange(e) {
    const index = parseInt(e.currentTarget.dataset.index)
    this.setData({ 
      tabIndex: index,
      page: 1, 
      hasMore: true 
    })
    this.applyPagination(true)
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

  async loadAvailableCoupons() {
    try {
      this.setData({ loading: true, page: 1, hasMore: true, errorAvailable: false })
      const res = await api.coupon.list()
      console.log('优惠券中心-可领取原始响应:', res)
      const list = Array.isArray(res)
        ? res
        : (Array.isArray(res?.items) ? res.items : (Array.isArray(res?.data) ? res.data : []))
      const now = new Date()
      const allAvailableCoupons = list.map(c => {
        const validStart = c.valid_start || c.validStart || c.start_time || c.startTime
        const validEnd = c.valid_end || c.validEnd || c.end_time || c.endTime
        const couponType = c.coupon_type || c.discount_type || 'cash'
        const discountValue = Number(c.discount_value) || 0
        const minAmount = Number(c.min_amount) || 0
        const endTime = validEnd ? new Date(validEnd) : null
        const isAvailable = !!(endTime && now <= endTime && Number(c.status) === 1)
        return {
          ...c,
          coupon_type: couponType,
          coupon_value_text: this.formatCouponValue(couponType, discountValue),
          coupon_unit_text: this.formatCouponUnit(couponType),
          coupon_suffix_text: this.formatCouponSuffix(couponType),
          min_amount_text: util.formatPrice(minAmount),
          valid_start_text: validStart ? util.formatDate(validStart, 'YYYY-MM-DD') : '未设置',
          valid_end_text: validEnd ? util.formatDate(validEnd, 'YYYY-MM-DD') : '未设置',
          desc_text: this.formatCouponDesc({ ...c, coupon_type: couponType }),
          isAvailable
        }
      })
      console.log('优惠券中心-可领取解析后:', allAvailableCoupons)
      this.setData({
        allAvailableCoupons,
        loading: false
      })
      this.applyPagination(true)
    } catch (error) {
      console.error('加载优惠券失败:', error)
      this.setData({ loading: false, errorAvailable: true })
    }
  },

  formatCouponValue(couponType, discountValue) {
    const value = Number(discountValue) || 0
    if (couponType === 'cash' || couponType === 'amount') {
      return util.formatPrice(value)
    }

    const normalized = value % 1 === 0 ? String(value) : String(parseFloat(value.toFixed(2)))
    return normalized
  },

  formatCouponUnit(couponType) {
    return couponType === 'cash' || couponType === 'amount' ? '¥' : ''
  },

  formatCouponSuffix(couponType) {
    return couponType === 'cash' || couponType === 'amount' ? '' : '折'
  },

  // 加载我的优惠券
  async loadMyCoupons() {
    try {
      this.setData({ loading: true, page: 1, hasMore: true, errorMy: false })
      const res = await api.coupon.my()
      console.log('优惠券中心-我的优惠券原始响应:', res)
      const list = Array.isArray(res)
        ? res
        : (Array.isArray(res?.items) ? res.items : (Array.isArray(res?.data) ? res.data : []))
      const now = Date.now()
      const allMyCoupons = list
        .map(c => {
          const coupon = c.coupon || {}
          const couponType = coupon.coupon_type || coupon.discount_type || 'cash'
          const discountValue = Number(coupon.discount_value) || 0
          const minAmount = Number(coupon.min_amount) || 0
          const expireTime = c.expire_time ? new Date(c.expire_time) : null
          const isExpired = Number(c.status) !== 1 && !!(expireTime && !Number.isNaN(expireTime.getTime()) && now > expireTime.getTime())
          const displayStatus = Number(c.status) === 1 ? 1 : (isExpired ? 2 : 0)
          return {
            ...c,
            status: displayStatus,
            coupon: {
              ...coupon,
              coupon_type: couponType
            },
            discount_text: this.formatCouponValue(couponType, discountValue),
            coupon_unit_text: this.formatCouponUnit(couponType),
            coupon_suffix_text: this.formatCouponSuffix(couponType),
            min_amount_text: util.formatPrice(minAmount),
            claim_time_text: util.formatDate(c.claim_time || c.get_time, 'YYYY-MM-DD HH:mm'),
            expire_time_text: util.formatDate(c.expire_time, 'YYYY-MM-DD HH:mm'),
            desc_text: coupon ? (coupon.description || this.formatCouponDesc({ ...coupon, coupon_type: couponType })) : ''
          }
        })
        .filter(item => item.status === this.data.status)
      console.log('优惠券中心-我的优惠券解析后:', allMyCoupons)
      this.setData({
        allMyCoupons,
        loading: false
      })
      this.applyPagination(true)
    } catch (error) {
      console.error('加载我的优惠券失败:', error)
      this.setData({ loading: false, errorMy: true })
    }
  },

  onRetryAvailable() {
    this.loadAvailableCoupons()
  },

  onRetryMy() {
    this.loadMyCoupons()
  },

  onStatusChange(e) {
    const status = parseInt(e.currentTarget.dataset.status)
    this.setData({ status })
    this.loadMyCoupons()
  },

  // 领取优惠券
  async onClaimCoupon(e) {
    const couponId = e.currentTarget.dataset.id
    const coupon = this.data.availableCoupons.find(c => c.coupon_id === couponId)

    if (!coupon) return
    
    // 检查优惠券是否可用
    if (!coupon.isAvailable) {
      wx.showToast({ title: '优惠券已过期', icon: 'none' })
      return
    }

    return util.withLock('coupon_claim', async () => {
      try {
        wx.showLoading({ title: '领取中...', mask: true })
        await api.coupon.claim(couponId)
        wx.hideLoading()
        wx.showToast({ title: '领取成功', icon: 'success' })
        
        // 刷新列表
        this.loadAvailableCoupons()
        this.loadMyCoupons()
      } catch (error) {
        wx.hideLoading()
        console.error('领取优惠券失败:', error)
      }
    }, 1200)
  },

  // 客户端分页（可领取 / 我的）共用
  applyPagination(reset = false) {
    const { tabIndex, page, pageSize } = this.data
    const isAvailable = tabIndex === 0
    const all = isAvailable ? this.data.allAvailableCoupons : this.data.allMyCoupons
    const nextPage = reset ? 1 : page
    const end = nextPage * pageSize
    const slice = (all || []).slice(0, end)
    const hasMore = slice.length < (all || []).length
    if (isAvailable) {
      this.setData({ availableCoupons: slice, page: nextPage, hasMore })
    } else {
      this.setData({ myCoupons: slice, page: nextPage, hasMore })
    }
  },

  onReachBottom() {
    this.loadMore()
  },

  loadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) return
    this.setData({ loadingMore: true, page: this.data.page + 1 })
    this.applyPagination(false)
    setTimeout(() => this.setData({ loadingMore: false }), 200)
  },

  // 判断优惠券是否可用
  isCouponAvailable(coupon) {
    const now = new Date()
    const startTime = new Date(coupon.valid_start)
    const endTime = new Date(coupon.valid_end)
    return now >= startTime && now <= endTime && coupon.status === 1
  },

  // 格式化优惠券描述
  formatCouponDesc(coupon) {
    const couponType = coupon.coupon_type || coupon.discount_type || 'cash'
    const minAmount = Number(coupon.min_amount) || 0
    const discountValue = Number(coupon.discount_value) || 0
    if (couponType === 'cash' || couponType === 'amount') {
      return `满¥${util.formatPrice(minAmount)}减¥${util.formatPrice(discountValue)}`
    }
    return `满¥${util.formatPrice(minAmount)}打${util.formatPrice(discountValue)}折`
  }
})
