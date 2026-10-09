// utils/websocket.js - WebSocket 连接管理

class WebSocketManager {
  constructor() {
    this.socketTask = null
    this.isConnected = false
    this.reconnectTimer = null
    this.heartbeatTimer = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 3000 // 30秒心跳
    this.heartbeatInterval = 30000
    this.messageHandlers = []
    this.lastAdminAlertKey = ''
    this.adminAlertQueue = []
    this.isShowingAdminAlert = false
  }

  // 连接 WebSocket
  connect() {
    let app
    try {
      app = getApp()
    } catch (e) {
      console.log('App 实例未初始化，延迟连接 WebSocket')
      setTimeout(() => this.connect(), 1000)
      return
    }

    if (!app || !app.globalData) {
      console.log('App 数据未就绪，延迟连接 WebSocket')
      setTimeout(() => this.connect(), 1000)
      return
    }

    if (!app.globalData.isLogin) {
      console.log('用户未登录，跳过 WebSocket 连接')
      return
    }

    const token = wx.getStorageSync('token') || app.globalData.token
    if (!token) {
      console.log('Token 不存在，跳过 WebSocket 连接')
      return
    }

    if (this.socketTask) {
      this.close()
    }
//核心连接代码
    const baseURL = app.globalData.baseURL || 'http://localhost:8000'
    const wsURL = baseURL.replace(/^http/, 'ws').replace(/\/api$/, '')
    const url = `${wsURL}/api/ws/notifications?token=${token}`

    console.log('正在连接 WebSocket:', url)

    this.socketTask = wx.connectSocket({
      url: url,
      success: () => {
        console.log('WebSocket 连接请求已发送')
      },
      fail: (err) => {
        console.error('WebSocket 连接失败:', err)
        this.scheduleReconnect()
      }
    })

    this.socketTask.onOpen(() => {
      console.log('WebSocket 连接已建立')
      this.isConnected = true
      this.reconnectAttempts = 0
      this.startHeartbeat()
    })

    this.socketTask.onMessage((res) => {
      try {
        const data = JSON.parse(res.data)
        console.log('收到 WebSocket 消息:', data)
        this.handleMessage(data)
      } catch (e) {
        console.error('解析 WebSocket 消息失败:', e, res.data)
      }
    })

    this.socketTask.onClose((res) => {
      console.log('WebSocket 连接已关闭:', res)
      this.isConnected = false
      this.stopHeartbeat()

      if (res.code !== 1000) {
        this.scheduleReconnect()
      }
    })

    this.socketTask.onError((err) => {
      console.error('WebSocket 错误:', err)
      this.isConnected = false
    })
  }

  // 发送消息
  send(data) {
    if (!this.isConnected || !this.socketTask) {
      console.warn('WebSocket 未连接，无法发送消息')
      return false
    }

    try {
      this.socketTask.send({
        data: JSON.stringify(data),
        success: () => {
          console.log('消息发送成功:', data)
        },
        fail: (err) => {
          console.error('消息发送失败:', err)
        }
      })
      return true
    } catch (e) {
      console.error('发送消息异常:', e)
      return false
    }
  }

  // 关闭连接
  close() {
    if (this.socketTask) {
      this.socketTask.close({
        code: 1000,
        reason: '主动关闭'
      })
      this.socketTask = null
    }
    this.isConnected = false
    this.stopHeartbeat()
    this.stopReconnect()
  }

  // 处理接收到的消息
  handleMessage(data) {
    if (data.type === 'pong') {
      return
    }

    if (['new_paid_order', 'order_accepted', 'order_ready_for_pickup', 'order_cancelled', 'refund_request_created', 'refund_status_update'].includes(data.type)) {
      this.handleAdminOrderAlert(data)
    }

    if (data.type === 'new_order') {
      this.handleNewOrder(data)
    }

    if (data.type === 'order_status_update') {
      this.handleOrderStatusUpdate(data)
    }

    if (data.type === 'order_ready') {
      this.handleOrderReady(data)
    }

    if (data.type === 'pickup_timeout') {
      this.handlePickupTimeout(data)
    }

    if (data.type === 'refund_status_update') {
      this.handleRefundStatusUpdate(data)
    }

    if (data.type === 'notification') {
      this.handleGeneralNotification(data)
    }

    this.messageHandlers.forEach(handler => {
      try {
        handler(data)
      } catch (e) {
        console.error('消息处理器执行失败:', e)
      }
    })
  }

  // 管理端订单类居中强提醒
  handleAdminOrderAlert(data) {
    const app = getApp()
    const role = app.globalData.userInfo?.role
    const isAdminSide = ['admin', 'merchant', 'sys_admin', 'canteen_admin'].includes(role)
    if (!isAdminSide) return

    const alertKey = `${data.type}_${data.order_id || data.refund_id || ''}_${data.timestamp || ''}`
    if (this.lastAdminAlertKey === alertKey) return
    this.lastAdminAlertKey = alertKey

    this.enqueueAdminAlert(data)
  }

  enqueueAdminAlert(data) {
    this.adminAlertQueue.push(data)
    this.syncAdminAlertOverlay()
    this.processAdminAlertQueue()
  }

  processAdminAlertQueue() {
    if (this.isShowingAdminAlert || !this.adminAlertQueue.length) {
      this.syncAdminAlertOverlay()
      return
    }

    const data = this.adminAlertQueue.shift()
    this.isShowingAdminAlert = true
    this.showAdminAlertOverlay(data)
  }

  buildAdminAlertViewModel(data) {
    const titleMap = {
      new_paid_order: '新支付订单已到账',
      order_accepted: '商家已接单',
      order_ready_for_pickup: '订单制作完成',
      order_cancelled: '订单已取消',
      refund_request_created: '新的退款申请',
      refund_status_update: '退款状态有更新'
    }

    const accentMap = {
      new_paid_order: { accent: '#ff6b35', accentSoft: '#fff1eb', icon: '💸', tagText: '支付成功', iconBg: 'linear-gradient(135deg, #ff922b 0%, #ff6b35 100%)' },
      order_accepted: { accent: '#2f80ed', accentSoft: '#edf4ff', icon: '🧾', tagText: '商家接单', iconBg: 'linear-gradient(135deg, #4dabf7 0%, #2f80ed 100%)' },
      order_ready_for_pickup: { accent: '#12b886', accentSoft: '#ebfbf6', icon: '🍱', tagText: '制作完成', iconBg: 'linear-gradient(135deg, #20c997 0%, #12b886 100%)' },
      order_cancelled: { accent: '#fa5252', accentSoft: '#fff5f5', icon: '🛑', tagText: '订单取消', iconBg: 'linear-gradient(135deg, #ff8787 0%, #fa5252 100%)' },
      refund_request_created: { accent: '#7048e8', accentSoft: '#f3f0ff', icon: '💰', tagText: '退款申请', iconBg: 'linear-gradient(135deg, #9775fa 0%, #7048e8 100%)' },
      refund_status_update: { accent: '#e8590c', accentSoft: '#fff4e6', icon: '📣', tagText: '退款状态', iconBg: 'linear-gradient(135deg, #ff922b 0%, #e8590c 100%)' }
    }

    const appearance = accentMap[data.type] || { accent: '#5c7cfa', accentSoft: '#edf2ff', icon: '🔔', tagText: '实时提醒', iconBg: 'linear-gradient(135deg, #5c7cfa 0%, #7c5cff 100%)' }

    let content = data.message || '订单状态有更新'
    if (data.order_no) {
      content += `\n订单号：${data.order_no}`
    }
    if (data.pickup_code) {
      content += `\n取餐码：${data.pickup_code}`
    }

    return {
      ...appearance,
      type: data.type,
      title: titleMap[data.type] || '订单提醒',
      content,
      order_id: data.order_id,
      refund_id: data.refund_id,
      order_no: data.order_no || '',
      pay_amount_text: data.pay_amount ? `¥${Number(data.pay_amount).toFixed(2)}` : '',
      refund_amount_text: data.refund_amount ? `¥${Number(data.refund_amount).toFixed(2)}` : '',
      pickup_code: data.pickup_code || ''
    }
  }

  showAdminAlertOverlay(data) {
    wx.vibrateShort()
    const app = getApp()
    const alert = this.buildAdminAlertViewModel(data)
    app.updateAdminAlertOverlay({
      show: true,
      alert,
      queueLength: this.adminAlertQueue.length
    })
  }

  syncAdminAlertOverlay() {
    const app = getApp()
    const currentState = app.globalData.adminAlertOverlay || {}
    app.updateAdminAlertOverlay({
      ...currentState,
      queueLength: this.adminAlertQueue.length,
      show: this.isShowingAdminAlert,
      alert: currentState.alert || null
    })
  }

  dismissAdminAlert(openDetail = false) {
    const app = getApp()
    const currentAlert = app.globalData.adminAlertOverlay?.alert || null

    app.updateAdminAlertOverlay({
      show: false,
      alert: null,
      queueLength: this.adminAlertQueue.length
    })

    this.isShowingAdminAlert = false
    this.refreshCurrentPage()

    if (openDetail && currentAlert) {
      this.navigateByAlert(currentAlert)
    }

    setTimeout(() => {
      this.processAdminAlertQueue()
    }, 120)
  }

  refreshCurrentPage() {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    if (!currentPage) return

    if (typeof currentPage.loadOrders === 'function') currentPage.loadOrders(true)
    if (typeof currentPage.loadList === 'function') currentPage.loadList()
    if (typeof currentPage.loadRefunds === 'function') currentPage.loadRefunds(true)
    if (typeof currentPage.loadData === 'function') currentPage.loadData()
  }

  navigateByAlert(data) {
    if (data.refund_id) {
      wx.navigateTo({
        url: `/pages/refund/detail?id=${data.refund_id}`,
        fail: () => {
          wx.navigateTo({
            url: '/pages/refund/list'
          })
        }
      })
      return
    }

    if (data.order_id) {
      wx.navigateTo({
        url: `/pages/order/detail?id=${data.order_id}`,
        fail: () => {
          wx.switchTab({
            url: '/pages/order/list'
          })
        }
      })
      return
    }

    wx.navigateTo({
      url: '/pages/notification/notification'
    })
  }

  // 新订单通知
  handleNewOrder(data) {
    console.log('收到新订单通知:', data)

    wx.vibrateShort()

    let title = '新订单提醒'
    let content = '有新订单需要处理，请及时查看'

    if (data.order_info) {
      const info = data.order_info
      title = '新订单 ¥' + (info.total_price || '0.00')
      content = info.order_no || '有新订单需要处理'
      if (info.table_number) {
        content += ' | 桌号' + info.table_number
      }
    } else if (data.message) {
      content = data.message.length > 50 ? data.message.substring(0, 50) + '...' : data.message
    }

    wx.showModal({
      title: title,
      content: content,
      showCancel: true,
      cancelText: '稍后',
      confirmText: '查看',
      confirmColor: '#5C7CFA',
      success: (res) => {
        if (res.confirm && data.order_id) {
          wx.navigateTo({
            url: `/pages/order/detail?id=${data.order_id}`,
            fail: () => {
              wx.switchTab({
                url: '/pages/order/list'
              })
            }
          })
        }
      }
    })
  }

  // 处理订单状态更新
  handleOrderStatusUpdate(data) {
    console.log('订单状态更新:', data)

    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]

    if (currentPage && currentPage.route === 'pages/order/list') {
      if (typeof currentPage.loadOrders === 'function') {
        currentPage.loadOrders()
      }
    }
  }

  // 处理订单完成通知（用户接收）
  handleOrderReady(data) {
    console.log('订单已完成:', data)

    wx.vibrateShort()

    let title = '订单完成'
    let content = '您的订单已完成，请取餐'

    if (data.message) {
      content = data.message.length > 40 ? data.message.substring(0, 40) + '...' : data.message
    }

    wx.showModal({
      title: title,
      content: content,
      showCancel: false,
      confirmText: '知道了',
      confirmColor: '#5C7CFA',
      success: (res) => {
        if (res.confirm && data.order_id) {
          wx.navigateTo({
            url: `/pages/order/detail?id=${data.order_id}`,
            fail: () => {}
          })
        }
      }
    })
  }

  // 处理取餐超时提醒
  handlePickupTimeout(data) {
    console.log('收到取餐超时提醒:', data)

    wx.vibrateShort()

    wx.showModal({
      title: '取餐提醒',
      content: data.message || '您的订单已准备好，请尽快取餐',
      showCancel: true,
      cancelText: '稍后',
      confirmText: '立即查看',
      confirmColor: '#ff9500',
      success: (res) => {
        if (res.confirm && data.order_id) {
          wx.navigateTo({
            url: `/pages/order/detail?id=${data.order_id}`,
            fail: () => {
              wx.switchTab({
                url: '/pages/order/list'
              })
            }
          })
        }
      }
    })

    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]

    if (currentPage && currentPage.route === 'pages/order/list') {
      if (typeof currentPage.loadOrders === 'function') {
        currentPage.loadOrders(true)
      }
    }
  }

  // 处理退款状态更新
  handleRefundStatusUpdate(data) {
    console.log('收到退款状态更新:', data)

    const app = getApp()
    const role = app.globalData.userInfo?.role
    const isAdminSide = ['admin', 'merchant', 'sys_admin', 'canteen_admin'].includes(role)
    if (isAdminSide) {
      return
    }

    wx.vibrateShort()

    const statusMap = {
      approved: { title: '退款已批准', color: '#34c759' },
      rejected: { title: '退款已拒绝', color: '#ff4757' },
      completed: { title: '退款已完成', color: '#5b7dff' }
    }

    const statusInfo = statusMap[data.status] || { title: '退款状态更新', color: '#5b7dff' }

    wx.showModal({
      title: statusInfo.title,
      content: data.message || '您的退款申请状态已更新',
      showCancel: true,
      cancelText: '稍后',
      confirmText: '查看详情',
      confirmColor: statusInfo.color,
      success: (res) => {
        if (res.confirm && data.refund_id) {
          wx.navigateTo({
            url: `/pages/refund/detail?id=${data.refund_id}`,
            fail: () => {
              wx.navigateTo({
                url: '/pages/refund/list'
              })
            }
          })
        }
      }
    })

    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]

    if (currentPage && currentPage.route === 'pages/refund/list') {
      if (typeof currentPage.loadRefunds === 'function') {
        currentPage.loadRefunds(true)
      }
    }
  }

  // 处理通用通知
  handleGeneralNotification(data) {
    console.log('收到通用通知:', data)

    if (data.priority >= 1) {
      wx.vibrateShort()
    }

    if (data.notification_type === 'urgent') {
      wx.showModal({
        title: data.title || '紧急通知',
        content: data.message,
        showCancel: false,
        confirmText: '知道了',
        confirmColor: '#ff4757'
      })
    } else if (data.notification_type === 'marketing') {
      wx.showToast({
        title: data.title || data.message,
        icon: 'none',
        duration: 3000
      })
    } else {
      wx.showToast({
        title: data.title || data.message,
        icon: 'none',
        duration: 2000
      })
    }

    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]

    if (currentPage && currentPage.route === 'pages/notification/list') {
      if (typeof currentPage.loadNotifications === 'function') {
        currentPage.loadNotifications(true)
      }
      if (typeof currentPage.loadUnreadCount === 'function') {
        currentPage.loadUnreadCount()
      }
    }
  }

  // 注册消息处理器
  onMessage(handler) {
    if (typeof handler === 'function') {
      this.messageHandlers.push(handler)
    }
  }

  // 移除消息处理器
  offMessage(handler) {
    const index = this.messageHandlers.indexOf(handler)
    if (index > -1) {
      this.messageHandlers.splice(index, 1)
    }
  }

  // 开始心跳
  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' })
      }
    }, this.heartbeatInterval)
  }

  // 停止心跳
  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  // 计划重连
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('达到最大重连次数，停止重连')
      return
    }

    this.stopReconnect()

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts)
    console.log(`将在 ${delay}ms 后重连 (第 ${this.reconnectAttempts + 1} 次)`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }

  // 停止重连
  stopReconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }

  // 重置重连计数
  resetReconnect() {
    this.reconnectAttempts = 0
    this.stopReconnect()
  }
}

const wsManager = new WebSocketManager()

module.exports = wsManager
