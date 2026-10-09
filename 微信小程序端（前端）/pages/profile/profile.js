// pages/profile/profile.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

const ORDER_LIST_STATUS_STORAGE_KEY = 'order_list_current_status'

function normalizeOrderStats(summary = {}) {
  return {
    pending: Number(summary?.pending || 0),
    preparing: Number(summary?.preparing || 0),
    ready: Number(summary?.ready || 0),
    delivering: Number(summary?.delivering || 0),
    refund: Number(summary?.refund || 0)
  }
}

Page({
  data: {
    userInfo: null,
    isLogin: false,
    useTestOrderStats: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    },
    
    // 会员等级
    memberLevel: {
      name: '普通会员',
      icon: '🥉',
      color: '#cd7f32',
      progress: 0,
      needPoints: 0
    },
    
    // 统计数据
    stats: {
      points: 0,
      balance: '0.00',
      coupons: 0
    },
    
    // 订单统计
    orderStats: {
      pending: 0,      // 待支付
      preparing: 0,    // 制作中
      ready: 0,        // 待取餐
      delivering: 0,   // 配送中
      refund: 0        // 退款
    },
    
    // 未读消息数
    unreadCount: 0
  },

  onLoad() {
    this.loadData()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    this.setData({ 
      isLogin: app.globalData.isLogin,
      unreadCount: Number(app.globalData.unreadMessageCount || 0)
    })
    if (app.globalData.isLogin) {
      this.loadData()

      // 同步底部“我的”Tab 角标：根据全局未读消息数动态更新/清零
      const count = app.globalData.unreadMessageCount || 0
      if (count > 0) {
        wx.setTabBarBadge({
          index: 4,
          text: count > 99 ? '99+' : String(count)
        }).catch(() => {})
      } else {
        wx.removeTabBarBadge({ index: 4 }).catch(() => {})
      }
    } else {
      // 未登录时确保角标被清除
      wx.removeTabBarBadge({ index: 4 }).catch(() => {})
    }
  },

  onPullDownRefresh() {
    this.loadData().finally(() => {
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

  // 加载所有数据
  async loadData() {
    if (!app.globalData.isLogin) return
    
    await Promise.all([
      this.loadUserInfo(),
      this.loadStats(),
      this.loadOrderStats(),
      this.loadUnreadCount()
    ])
  },

  // 加载用户信息
  async loadUserInfo() {
    if (!app.globalData.isLogin) return
    
    try {
      const res = await api.user.getInfo()
      
      // 处理头像URL
      if (res.avatar) {
        res.avatar = util.formatImageUrl(res.avatar)
      }
      
      this.setData({ userInfo: res })
      
      // 计算会员等级
      this.calculateMemberLevel(res)
    } catch (error) {
      console.error('加载用户信息失败:', error)
    }
  },

  // 计算会员等级
  calculateMemberLevel(userInfo) {
    const points = userInfo.points || 0
    let level = {
      name: '普通会员',
      icon: '🥉',
      color: '#cd7f32',
      progress: 0,
      needPoints: 100
    }
    
    if (points >= 1000) {
      level = {
        name: '钻石会员',
        icon: '💎',
        color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        progress: 100,
        needPoints: 0
      }
    } else if (points >= 500) {
      level = {
        name: '黄金会员',
        icon: '🥇',
        color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        progress: Math.floor((points - 500) / 500 * 100),
        needPoints: 1000 - points
      }
    } else if (points >= 100) {
      level = {
        name: '白银会员',
        icon: '🥈',
        color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        progress: Math.floor((points - 100) / 400 * 100),
        needPoints: 500 - points
      }
    } else {
      level.progress = Math.floor(points / 100 * 100)
      level.needPoints = 100 - points
    }
    
    this.setData({ memberLevel: level })
  },

  // 加载统计数据
  async loadStats() {
    if (!app.globalData.isLogin) return
    
    try {
      // 加载积分和余额
      const userInfo = await api.user.getInfo()
      
      // 加载优惠券数量
      const coupons = await api.coupon.my('available').catch(() => [])
      const couponCount = Array.isArray(coupons) ? coupons.length : (coupons?.items?.length || 0)
      
      this.setData({
        stats: {
          points: userInfo.points || 0,
          balance: (userInfo.balance || 0).toFixed(2),
          coupons: couponCount
        }
      })
    } catch (error) {
      console.error('加载统计数据失败:', error)
    }
  },

  // 加载订单统计
  async loadOrderStats() {
    if (!app.globalData.isLogin) return

    if (this.data.useTestOrderStats) {
      this.setData({
        orderStats: {
          pending: 2,
          preparing: 3,
          ready: 1,
          delivering: 4,
          refund: 2
        }
      })
      return
    }
    
    try {
      const summary = await api.order.statusSummary()
      this.setData({
        orderStats: normalizeOrderStats(summary)
      })
    } catch (error) {
      console.error('加载订单统计失败:', error)
    }
  },

  async markOrderStatsViewed(scope) {
    if (!app.globalData.isLogin) return

    try {
      const summary = await api.order.markStatusViewed(scope)
      this.setData({
        orderStats: normalizeOrderStats(summary)
      })
    } catch (error) {
      console.error('标记订单统计已查看失败:', error)
    }
  },

  // 加载未读消息数
  async loadUnreadCount() {
    if (!app.globalData.isLogin) return
    
    try {
      const res = await api.notification.unreadCount()
      const unreadCount = (res && (res.unread_count ?? res.count)) || 0
      this.setData({ unreadCount })
      app.globalData.unreadMessageCount = unreadCount
    } catch (error) {
      console.error('加载未读消息数失败:', error)
    }
  },

  // 跳转登录
  onLogin() {
    wx.navigateTo({
      url: '/pages/auth/login'
    })
  },

  // 我的订单
  onMyOrders() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }

    wx.setStorageSync(ORDER_LIST_STATUS_STORAGE_KEY, 'all')
    this.markOrderStatsViewed('all')

    wx.switchTab({
      url: '/pages/order/list'
    })
  },

  // 订单状态跳转
  onOrderStatus(e) {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    const status = e.currentTarget.dataset.status

    if (status === 'refund') {
      this.markOrderStatsViewed('refund')

      wx.navigateTo({
        url: '/pages/refund/list'
      })
      return
    }

    const statusKeyMap = {
      '0': 'pending',
      '1': 'preparing',
      '2': 'ready',
      '3': 'delivering'
    }
    const key = statusKeyMap[status]
    if (key) {
      wx.setStorageSync(ORDER_LIST_STATUS_STORAGE_KEY, key)
      this.markOrderStatsViewed(key)
    }

    wx.switchTab({
      url: '/pages/order/list'
    })
  },

  // 地址管理
  onAddress() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/address/address'
    })
  },

  // 我的收藏
  onFavorites() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/favorite/favorite'
    })
  },

  // 浏览历史
  onHistory() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/history/history'
    })
  },

  // 编辑资料
  onNotifications() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    
    wx.navigateTo({
      url: '/pages/notification/notification'
    })
  },

  // 消息中心
  onMessages() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/message/message'
    })
  },

  // 编辑资料
  onEditProfile() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/profile/edit'
    })
  },

  // 我的优惠券
  onCoupons() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/coupon/coupon'
    })
  },

  // 修改密码
  onChangePassword() {
    if (!app.globalData.isLogin) {
      this.onLogin()
      return
    }
    wx.navigateTo({
      url: '/pages/profile/change-password'
    })
  },

  // 关于我们
  onAbout() {
    wx.showModal({
      title: '关于我们',
      content: '校园食堂订餐系统 v1.0.0\n\n为校园师生提供便捷的订餐服务',
      showCancel: false,
      confirmText: '知道了'
    })
  },

  // 活动中心
  onActivityCenter() {
    wx.navigateTo({
      url: '/pages/activity/activity'
    })
  },

  // 常见问题
  onFAQ() {
    wx.navigateTo({
      url: '/pages/faq/faq'
    })
  },

  // 退出登录
  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出登录吗？',
      confirmColor: '#ff4757',
      success: (res) => {
        if (res.confirm) {
          app.logout()
          this.setData({ 
            isLogin: false,
            userInfo: null,
            stats: {
              points: 0,
              balance: '0.00',
              coupons: 0
            },
            orderStats: {
              pending: 0,
              preparing: 0,
              ready: 0,
              delivering: 0,
              refund: 0
            },
            unreadCount: 0
          })
          wx.showToast({
            title: '已退出登录',
            icon: 'success'
          })
        }
      }
    })
  }
})
