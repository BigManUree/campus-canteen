// pages/notification/notification.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    allNotifications: [],
    notifications: [],
    unreadCount: 0,
    loading: true,
    loadingMore: false,
    page: 1,
    pageSize: 10,
    hasMore: true,
    error: false,
    editMode: false,
    selectedIds: [],
    pollingTimer: null,
    focusRefundId: null,
    hasAutoClearedUnread: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options = {}) {
    if (options.focus_refund_id) {
      this.setData({ focusRefundId: String(options.focus_refund_id) })
    }

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

    const currentUnreadCount = Number(app.globalData.unreadMessageCount || 0)
    this.setData({ unreadCount: currentUnreadCount })
    
    this.loadNotifications()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (app.globalData.isLogin) {
      const currentUnreadCount = Number(app.globalData.unreadMessageCount || 0)
      this.setData({ unreadCount: currentUnreadCount })

      this.loadNotifications()
      this.startPolling()
    }
  },

  onHide() {
    this.stopPolling()
  },

  onUnload() {
    this.stopPolling()
  },

  onPullDownRefresh() {
    this.loadNotifications().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  // 同步未读数和角标
  syncUnreadState(list = [], options = {}) {
    const { keepCleared = false } = options
    const unreadCount = keepCleared ? 0 : (list || []).filter(item => !item.is_read).length
    this.setData({ unreadCount })
    this.updateTabBarBadge(unreadCount)
    app.globalData.unreadMessageCount = unreadCount
  },

  // 加载通知列表
  async loadNotifications() {
    try {
      this.setData({ loading: true, page: 1, hasMore: true, error: false })
      const res = await api.notification.recent()
      const list = Array.isArray(res) ? res : (res && res.items) ? res.items : []
      const sortedList = [...list].sort((a, b) => {
        const timeA = new Date(a.create_time || a.update_time || 0).getTime()
        const timeB = new Date(b.create_time || b.update_time || 0).getTime()
        return timeB - timeA
      })
      const allNotifications = sortedList.map(n => ({
        ...n,
        type_text: this.getNotificationTypeText(n.notification_type),
        time_text: util.formatDate(n.create_time, 'MM-DD HH:mm')
      }))
      this.setData({
        allNotifications,
        loading: false
      })
      this.syncUnreadState(allNotifications, { keepCleared: this.data.unreadCount === 0 })
      this.applyPagination(true)
      this.tryOpenFocusedRefund()
    } catch (error) {
      console.error('加载通知失败:', error)
      this.setData({ loading: false, error: true })
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

  onRetry() {
    this.loadNotifications()
  },

  // 自动清空未读（进入通知中心后）
  async autoClearUnread() {
    try {
      await api.notification.readAll()

      const allNotifications = this.data.allNotifications.map(item => ({
        ...item,
        is_read: true
      }))

      this.setData({
        allNotifications,
        unreadCount: 0,
        hasAutoClearedUnread: true
      })
      this.applyPagination(true)

      this.updateTabBarBadge(0)
      app.globalData.unreadMessageCount = 0
      
      console.log('✅ 已清空未读消息，角标已移除')
    } catch (error) {
      console.error('自动清空未读失败:', error)
    }
  },

  // 更新 TabBar 角标
  updateTabBarBadge(count) {
    if (count > 0) {
      wx.setTabBarBadge({
        index: 4,  // 假设"我的"是第5个tab（索引从0开始）
        text: count > 99 ? '99+' : String(count)
      })
    } else {
      wx.removeTabBarBadge({ index: 4 })
    }
  },

  // 启动轮询
  startPolling() {
    // 如果已经有定时器，先清除
    this.stopPolling()
    
    // 每30秒刷新一次消息（但不刷新未读数，避免角标重新出现）
    this.data.pollingTimer = setInterval(() => {
      this.loadNotifications()
    }, 30000)
    
    console.log('消息轮询已启动')
  },

  // 停止轮询
  stopPolling() {
    if (this.data.pollingTimer) {
      clearInterval(this.data.pollingTimer)
      this.data.pollingTimer = null
      console.log('消息轮询已停止')
    }
  },

  // 自动跳转聚焦的退款消息
  tryOpenFocusedRefund() {
    const focusRefundId = this.data.focusRefundId
    if (!focusRefundId) return

    const target = (this.data.allNotifications || []).find(item => {
      if (String(item.related_id || '') !== focusRefundId) return false
      const text = `${item.title || ''}${item.message || ''}`
      return item.notification_type === 'refund' || text.includes('退款')
    })

    if (!target) return

    this.setData({ focusRefundId: null })
    wx.navigateTo({
      url: `/pages/refund/detail?id=${target.related_id}`
    })
  },

  // 点击消息
  async onNotificationTap(e) {
    const notification = e.currentTarget.dataset.item
    
    // 如果未读，标记为已读
    if (!notification.is_read) {
      try {
        await api.notification.read(notification.notification_id)
        
        // 更新本地状态
        const allNotifications = this.data.allNotifications.map(item => {
          if (item.notification_id === notification.notification_id) {
            return { ...item, is_read: true }
          }
          return item
        })
        
        this.setData({ allNotifications })
        this.syncUnreadState(allNotifications)
        this.applyPagination(true)
      } catch (error) {
        console.error('标记已读失败:', error)
      }
    }
    
    // 如果是订单消息，跳转到订单详情
    if (notification.related_id) {
      const text = `${notification.title || ''}${notification.message || ''}`
      if (notification.notification_type === 'order' || notification.notification_type === 'order_status') {
      wx.navigateTo({
          url: `/pages/order/detail?id=${notification.related_id}`
      })
        return
      }

      if (notification.notification_type === 'refund' || text.includes('退款')) {
        wx.navigateTo({
          url: `/pages/refund/detail?id=${notification.related_id}`
        })
      }
    }
  },

  // 标记全部为已读
  async onMarkAllRead() {
    wx.showModal({
      title: '提示',
      content: '确定要标记所有通知为已读吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.notification.readAll()

            const allNotifications = this.data.allNotifications.map(item => ({
              ...item,
              is_read: true
            }))

            this.setData({ allNotifications })
            this.syncUnreadState(allNotifications, { keepCleared: true })
            this.applyPagination(true)
            wx.showToast({ title: '已全部标记', icon: 'success' })
          } catch (error) {
            console.error('标记全部已读失败:', error)
          }
        }
      }
    })
  },

  // 分页（客户端）
  applyPagination(reset = false) {
    const { allNotifications, page, pageSize, selectedIds } = this.data
    const nextPage = reset ? 1 : page
    const end = nextPage * pageSize
    const slice = (allNotifications || []).slice(0, end).map(item => ({
      ...item,
      checked: selectedIds.includes(String(item.notification_id))
    }))
    const hasMore = slice.length < (allNotifications || []).length
    this.setData({
      notifications: slice,
      page: nextPage,
      hasMore
    })
  },

  onReachBottom() {
    this.loadMore()
  },

  onNoop() {},

  loadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) return
    this.setData({ loadingMore: true, page: this.data.page + 1 })
    this.applyPagination(false)
    setTimeout(() => this.setData({ loadingMore: false }), 200)
  },

  // 查看订单详情
  onViewOrder(e) {
    const orderId = e.currentTarget.dataset.orderId
    if (orderId) {
      wx.navigateTo({
        url: `/pages/order/detail?id=${orderId}`
      })
    }
  },

  // 获取通知类型文本
  getNotificationTypeText(type) {
    const typeMap = {
      order: '订单通知',
      order_status: '订单通知',
      refund: '退款通知',
      system: '系统通知',
      promotion: '活动通知',
      activity: '活动通知'
    }
    return typeMap[type] || '通知'
  },

  // 切换编辑模式
  onToggleEditMode() {
    this.setData({
      editMode: !this.data.editMode,
      selectedIds: []
    })
  },

  // 选择/取消选择通知
  onToggleSelect(e) {
    const id = String(e.currentTarget.dataset.id)
    const { selectedIds } = this.data
    const index = selectedIds.indexOf(id)
    
    if (index > -1) {
      selectedIds.splice(index, 1)
    } else {
      selectedIds.push(id)
    }
    
    this.setData({ selectedIds: [...selectedIds] })
    this.applyPagination(true)
  },

  // 全选/取消全选
  onToggleSelectAll() {
    const { notifications, selectedIds } = this.data

    if (!notifications.length) return
    
    if (selectedIds.length === notifications.length) {
      // 取消全选
      this.setData({ selectedIds: [] })
    } else {
      // 全选
      const allIds = notifications.map(item => String(item.notification_id))
      this.setData({ selectedIds: allIds })
    }

    this.applyPagination(true)
  },

  // 批量删除
  async onBatchDelete() {
    const { selectedIds } = this.data
    
    if (selectedIds.length === 0) {
      wx.showToast({
        title: '请选择要删除的通知',
        icon: 'none'
      })
      return
    }
    
    wx.showModal({
      title: '提示',
      content: `确定要删除选中的 ${selectedIds.length} 条通知吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '删除中...', mask: true })
            await api.notification.batchDelete(selectedIds)
            wx.hideLoading()
            wx.showToast({ title: '删除成功', icon: 'success' })
            
            const allNotifications = this.data.allNotifications.filter(
              item => !selectedIds.includes(String(item.notification_id))
            )
            
            this.setData({
              allNotifications,
              selectedIds: [],
              editMode: false
            })
            
            this.syncUnreadState(allNotifications)
            this.applyPagination(true)
          } catch (error) {
            wx.hideLoading()
            console.error('批量删除失败:', error)
            wx.showToast({
              title: error.message,
              icon: 'none'
            })
          }
        }
      }
    })
  },

  // 批量标记已读
  async onBatchMarkRead() {
    const { selectedIds } = this.data
    
    if (selectedIds.length === 0) {
      wx.showToast({
        title: '请选择要标记的通知',
        icon: 'none'
      })
      return
    }
    
    try {
      wx.showLoading({ title: '处理中...', mask: true })
      
      // 逐个标记为已读
      await Promise.all(
        selectedIds.map(id => api.notification.read(id))
      )
      
      wx.hideLoading()
      wx.showToast({ title: '标记成功', icon: 'success' })
      
      // 更新本地状态
      const allNotifications = this.data.allNotifications.map(item => {
        if (selectedIds.includes(String(item.notification_id))) {
          return { ...item, is_read: true }
        }
        return item
      })
      
      this.setData({
        allNotifications,
        selectedIds: [],
        editMode: false
      })
      
      this.syncUnreadState(allNotifications)
      this.applyPagination(true)
    } catch (error) {
      wx.hideLoading()
      console.error('批量标记失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 清空所有消息
  async onClearAll() {
    if (this.data.notifications.length === 0) {
      wx.showToast({ title: '暂无消息', icon: 'none' })
      return
    }

    wx.showModal({
      title: '清空所有消息',
      content: '确定要清空所有消息吗？此操作不可恢复。',
      confirmText: '清空',
      confirmColor: '#ff4757',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '清空中...', mask: true })
            await api.notification.clear()
            wx.hideLoading()
            wx.showToast({ title: '已清空', icon: 'success' })
            
            this.setData({ 
              allNotifications: [],
              notifications: [],
              unreadCount: 0,
              page: 1,
              hasMore: false,
              selectedIds: [],
              editMode: false
            })
            
            this.updateTabBarBadge(0)
            app.globalData.unreadMessageCount = 0
          } catch (error) {
            wx.hideLoading()
            console.error('清空失败:', error)
            wx.showToast({ 
              title: error.message, 
              icon: 'none' 
            })
          }
        }
      }
    })
  }
})
