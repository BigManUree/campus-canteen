// app.js
const config = require('./utils/config')

App({
  onLaunch() {
    this.initAdminAlertState()

    // 检查登录状态
    this.checkLogin()
    
    // 获取系统信息
    this.getSystemInfo()
    
    // 检查更新
    this.checkUpdate()
    
    // 定期检查 Token 是否过期
    this.startTokenCheck()
    
    // 启动全局消息轮询
    this.startMessagePolling()
    
    // 启动 WebSocket 连接
    this.connectWebSocket()
  },

  onShow() {
    // 小程序从后台进入前台时，重新连接 WebSocket
    if (this.globalData.isLogin && this.globalData.wsManager) {
      if (!this.globalData.wsManager.isConnected) {
        console.log('小程序进入前台，重新连接 WebSocket')
        // 延迟一下，避免 app 实例未就绪
        setTimeout(() => {
          this.globalData.wsManager.connect()
        }, 500)
      }
    }
  },

  onHide() {
    // 小程序从前台进入后台时，保持 WebSocket 连接
    // 不主动断开，让系统自动管理
  },

  initAdminAlertState() {
    this.globalData.adminAlertOverlay = {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  updateAdminAlertOverlay(patch = {}) {
    const nextState = {
      ...(this.globalData.adminAlertOverlay || {
        show: false,
        alert: null,
        queueLength: 0
      }),
      ...patch
    }

    this.globalData.adminAlertOverlay = nextState

    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    if (currentPage && typeof currentPage.setData === 'function') {
      currentPage.setData({
        adminAlertOverlay: nextState
      })
    }
  },

  bindAdminAlertToPage(page) {
    if (!page || typeof page.setData !== 'function') return
    page.setData({
      adminAlertOverlay: this.globalData.adminAlertOverlay || {
        show: false,
        alert: null,
        queueLength: 0
      }
    })
  },

  // 检查登录状态
  checkLogin() {
    const token = wx.getStorageSync('token')
    const userInfo = wx.getStorageSync('userInfo')
    
    if (token && userInfo) {
      this.globalData.token = token
      this.globalData.userInfo = userInfo
      this.globalData.isLogin = true
    } else {
      this.globalData.isLogin = false
    }
  },

  // 获取系统信息
  getSystemInfo() {
    try {
      // 使用新的 API 替代已弃用的 wx.getSystemInfo
      const windowInfo = wx.getWindowInfo()
      const deviceInfo = wx.getDeviceInfo()
      const appBaseInfo = wx.getAppBaseInfo()
      
      // 合并信息以保持兼容性
      const systemInfo = {
        ...windowInfo,
        ...deviceInfo,
        ...appBaseInfo,
        statusBarHeight: windowInfo.statusBarHeight || 0
      }
      
      this.globalData.systemInfo = systemInfo
      this.globalData.statusBarHeight = windowInfo.statusBarHeight || 0
      this.globalData.navBarHeight = (windowInfo.statusBarHeight || 0) + 44
    } catch (error) {
      // 如果新 API 不支持，回退到旧 API（兼容旧版本）
      wx.getSystemInfo({
        success: (res) => {
          this.globalData.systemInfo = res
          this.globalData.statusBarHeight = res.statusBarHeight || 0
          this.globalData.navBarHeight = (res.statusBarHeight || 0) + 44
        }
      })
    }
  },

  // 检查更新
  checkUpdate() {
    if (wx.canIUse('getUpdateManager')) {
      const updateManager = wx.getUpdateManager()
      updateManager.onCheckForUpdate((res) => {
        if (res.hasUpdate) {
          updateManager.onUpdateReady(() => {
            wx.showModal({
              title: '更新提示',
              content: '新版本已经准备好，是否重启应用？',
              success: (res) => {
                if (res.confirm) {
                  updateManager.applyUpdate()
                }
              }
            })
          })
        }
      })
    }
  },

  login(userInfo, token) {
    wx.setStorageSync('token', token)
    wx.setStorageSync('userInfo', userInfo)
    
    this.globalData.token = token
    this.globalData.userInfo = userInfo
    this.globalData.isLogin = true
    
    // 登录成功后连接 WebSocket
    this.connectWebSocket()
  },

  // 退出登录
  logout() {
    wx.removeStorageSync('token')
    wx.removeStorageSync('userInfo')
    this.globalData.token = ''
    this.globalData.userInfo = null
    this.globalData.isLogin = false
    
    // 清除 Token 检查定时器
    if (this.globalData._tokenCheckTimer) {
      clearInterval(this.globalData._tokenCheckTimer)
      this.globalData._tokenCheckTimer = null
    }
    
    // 清除消息轮询定时器
    if (this.globalData._messagePollingTimer) {
      clearInterval(this.globalData._messagePollingTimer)
      this.globalData._messagePollingTimer = null
    }
    
    // 断开 WebSocket 连接
    if (this.globalData.wsManager) {
      this.globalData.wsManager.close()
    }

    this.updateAdminAlertOverlay({
      show: false,
      alert: null,
      queueLength: 0
    })
    
    // 清除 TabBar 角标
    wx.removeTabBarBadge({ index: 4 }).catch(() => {})
  },

  startMessagePolling() {
    this.globalData._messagePollingTimer = setInterval(async () => {
      if (!this.globalData.isLogin) return
      
      try {
        const api = require('./utils/api.js')
        const res = await api.notification.unreadCount()
        const count = (res && res.unread_count) || (res && res.count) || 0
        
        if (count > 0) {
          wx.setTabBarBadge({
            index: 4,
            text: count > 99 ? '99+' : String(count)
          }).catch(() => {})
        } else {
          wx.removeTabBarBadge({ index: 4 }).catch(() => {})
        }
        
        this.globalData.unreadMessageCount = count
      } catch (error) {
        console.error('获取未读消息数量失败:', error)
      }
    }, 60000)
    
    if (this.globalData.isLogin) {
      setTimeout(() => {
        const api = require('./utils/api.js')
        api.notification.unreadCount().then(res => {
          const count = (res && res.unread_count) || (res && res.count) || 0
          if (count > 0) {
            wx.setTabBarBadge({
              index: 4,
              text: count > 99 ? '99+' : String(count)
            }).catch(() => {})
          }
          this.globalData.unreadMessageCount = count
        }).catch(() => {})
      }, 2000)
    }
  },

  startTokenCheck() {
    this.globalData._tokenCheckTimer = setInterval(() => {
      if (!this.globalData.isLogin) return
      
      const util = require('./utils/util.js')
      if (util.isTokenExpired()) {
        this.logout()
        
        wx.showModal({
          title: '登录已过期',
          content: '您的登录已过期，请重新登录',
          showCancel: false,
          success: () => {
            wx.reLaunch({
              url: '/pages/auth/login'
            })
          }
        })
      }
    }, 60000)
  },

  // 连接 WebSocket
  connectWebSocket() {
    if (!this.globalData.isLogin) {
      console.log('用户未登录，跳过 WebSocket 连接')
      return
    }

    // 延迟连接，确保 app 实例完全初始化
    setTimeout(() => {
      // 初始化 WebSocket 管理器
      if (!this.globalData.wsManager) {
        const wsManager = require('./utils/websocket.js')
        this.globalData.wsManager = wsManager
      }

      // 连接 WebSocket
      this.globalData.wsManager.connect()
    }, 500)
  },

  globalData: {
    userInfo: null,
    token: '',
    isLogin: false,
    systemInfo: null,
    statusBarHeight: 0,
    navBarHeight: 0,
    baseURL: config.baseURL,
    host: config.host,
    _authRedirecting: false,
    unreadMessageCount: 0,
    checkoutItems: null,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  }
})

