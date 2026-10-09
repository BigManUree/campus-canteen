// pages/order/list.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

const ORDER_LIST_STATUS_STORAGE_KEY = 'order_list_current_status'

function normalizeOrderStats(summary = {}) {
  return {
    pending: Number(summary?.pending || 0),
    preparing: Number(summary?.preparing || 0),
    ready: Number(summary?.ready || 0),
    delivering: Number(summary?.delivering || 0)
  }
}

function toStatusCount(summary = {}) {
  const stats = normalizeOrderStats(summary)
  return {
    all: stats.pending + stats.preparing + stats.ready + stats.delivering,
    pending: stats.pending,
    preparing: stats.preparing,
    ready: stats.ready,
    delivering: stats.delivering
  }
}

Page({
  data: {
    orders: [],
    loading: true,
    refreshing: false,
    loadingMore: false,
    
    page: 1,
    pageSize: 10,
    hasMore: true,
    
    showSearch: false,
    keyword: '',
    searchTimer: null,
    
    currentStatus: 'all',
    
    statusCount: {
      all: 0,
      pending: 0,
      preparing: 0,
      ready: 0,
      delivering: 0
    },
    
    pollingTimer: null,
    countdownTimer: null,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    const storedStatus = wx.getStorageSync(ORDER_LIST_STATUS_STORAGE_KEY)
    const initialStatus = options.status || storedStatus || 'all'

    this.setData({ currentStatus: initialStatus })
    wx.removeStorageSync(ORDER_LIST_STATUS_STORAGE_KEY)
    
    this.loadStatusCount()
    this.loadOrders(true)
    this.startCountdownTimer()
  },

  onShow() {
    app.bindAdminAlertToPage(this)

    const storedStatus = wx.getStorageSync(ORDER_LIST_STATUS_STORAGE_KEY)
    if (storedStatus && storedStatus !== this.data.currentStatus) {
      this.setData({ currentStatus: storedStatus })
      wx.removeStorageSync(ORDER_LIST_STATUS_STORAGE_KEY)
      this.loadStatusCount()
      this.loadOrders(true)
      this.startPollingIfNeeded()
      return
    }

    if (storedStatus) {
      wx.removeStorageSync(ORDER_LIST_STATUS_STORAGE_KEY)
    }

    this.loadStatusCount()

    if (this.data.orders.length > 0) {
      this.loadOrders(true)
    }
    
    this.startPollingIfNeeded()
  },

  onHide() {
    this.stopPolling()
    this.clearSearchTimer()
  },

  onUnload() {
    this.stopPolling()
    this.stopCountdownTimer()
    this.clearSearchTimer()
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

  /**
   * 页面相关事件处理函数--监听用户下拉动作
   */
  onPullDownRefresh() {
    this.onRefresh()
  },

  /**
   * 页面上拉触底事件的处理函数
   */
  onReachBottom() {
    this.onLoadMore()
  },

  /**
   * 显示搜索框
   */
  onSearchTap() {
    this.setData({ showSearch: true })
  },

  /**
   * 搜索输入
   */
  onSearchInput(e) {
    const keyword = e.detail.value
    this.setData({ keyword })
    this.triggerSearchWithDebounce()
  },

  /**
   * 延迟触发实时搜索
   */
  triggerSearchWithDebounce() {
    this.clearSearchTimer()
    this.data.searchTimer = setTimeout(() => {
      this.loadOrders(true)
    }, 320)
  },

  /**
   * 清理搜索定时器
   */
  clearSearchTimer() {
    if (this.data.searchTimer) {
      clearTimeout(this.data.searchTimer)
      this.data.searchTimer = null
    }
  },

  /**
   * 执行搜索
   */
  onSearch() {
    this.clearSearchTimer()
    this.loadOrders(true)
  },

  /**
   * 清空搜索
   */
  onClearSearch() {
    this.clearSearchTimer()
    this.setData({ keyword: '' })
    this.loadOrders(true)
  },

  /**
   * 取消搜索
   */
  onCancelSearch() {
    this.clearSearchTimer()
    this.setData({ 
      showSearch: false,
      keyword: ''
    })
    this.loadOrders(true)
  },

  /**
   * 切换状态筛选
   */
  async onStatusChange(e) {
    const status = e.currentTarget.dataset.status
    if (status === this.data.currentStatus) return

    wx.setStorageSync(ORDER_LIST_STATUS_STORAGE_KEY, status)
    this.setData({ currentStatus: status })

    const viewedScopeMap = {
      all: 'all',
      pending: 'pending',
      preparing: 'preparing',
      ready: 'ready',
      delivering: 'delivering'
    }
    const scope = viewedScopeMap[status]
    if (scope) {
      await this.markStatusViewed(scope)
    } else {
      this.loadStatusCount()
    }

    this.loadOrders(true)
  },

  /**
   * 下拉刷新
   */
  async onRefresh() {
    this.setData({ refreshing: true })
    await this.loadStatusCount()
    this.loadOrders(true).finally(() => {
      this.setData({ refreshing: false })
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 加载更多
   */
  onLoadMore() {
    if (this.data.loading || this.data.loadingMore || !this.data.hasMore) {
      return
    }

    this.setData({ 
      loadingMore: true,
      page: this.data.page + 1
    })

    this.loadOrders(false).finally(() => {
      this.setData({ loadingMore: false })
    })
  },

  /**
   * 加载顶部状态数量
   */
  async loadStatusCount() {
    try {
      const summary = await api.order.statusSummary()
      this.setData({
        statusCount: toStatusCount(summary)
      })
    } catch (error) {
      console.error('加载顶部状态数量失败:', error)
    }
  },

  /**
   * 标记状态已查看并刷新顶部数量
   */
  async markStatusViewed(scope) {
    try {
      const summary = await api.order.markStatusViewed(scope)
      this.setData({
        statusCount: toStatusCount(summary)
      })
    } catch (error) {
      console.error('标记订单列表状态已查看失败:', error)
      this.loadStatusCount()
    }
  },

  /**
   * 加载订单列表
   */
  async loadOrders(reset = false) {
    try {
      if (reset) {
        this.setData({ 
          loading: true, 
          page: 1, 
          hasMore: true 
        })
      }

      const { page, pageSize, keyword, currentStatus } = this.data

      // 构建请求参数
      const params = {
        page,
        page_size: pageSize
      }

      if (currentStatus !== 'all') {
        const statusParams = this.getStatusRequestParams(currentStatus)
        Object.assign(params, statusParams)
      }

      // 添加搜索关键词
      if (keyword) {
        params.keyword = keyword
      }

      // 调用API获取订单列表
      const res = await api.order.list(params)
      let list = Array.isArray(res) ? res : (res?.items || res?.data || [])

      if (reset) {
        this.loadStatusCount()
      }

      // 处理订单数据
      let orders = list.map(order => this.processOrderData(order))

      // 前端筛选状态（如果后端不支持状态筛选）
      if (currentStatus !== 'all') {
        orders = orders.filter(order => this.matchOrderStatus(order, currentStatus))
      }

      // 为每条订单生成前端唯一 key，避免 wx:key 冲突
      const baseIndex = reset ? 0 : this.data.orders.length
      orders = orders.map((order, index) => ({
        ...order,
        _key: `${baseIndex + index}_${order.order_id || order.id || order.order_no || ''}`
      }))

      // 合并数据
      const finalOrders = reset ? orders : [...this.data.orders, ...orders]
      const hasMore = orders.length >= pageSize

      this.setData({
        orders: finalOrders,
        hasMore,
        loading: false
      })
      
      // 检查是否需要启动轮询
      this.startPollingIfNeeded()

    } catch (error) {
      console.error('加载订单失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
      this.setData({ loading: false })
    }
  },

  /**
   * 启动轮询（如果有未完成的订单）
   */
  startPollingIfNeeded() {
    const hasActiveOrders = this.data.orders.some(o => o.order_status < 4)
    
    if (hasActiveOrders && !this.data.pollingTimer) {
      this.startPolling()
    } else if (!hasActiveOrders && this.data.pollingTimer) {
      this.stopPolling()
    }
  },

  /**
   * 启动轮询
   */
  startPolling() {
    // 如果已经有定时器，先清除
    this.stopPolling()
    
    // 每10秒刷新一次订单列表
    this.data.pollingTimer = setInterval(() => {
      this.loadStatusCount()
      this.loadOrders(true)
    }, 10000)
    
    console.log('订单列表轮询已启动')
  },

  /**
   * 停止轮询
   */
  stopPolling() {
    if (this.data.pollingTimer) {
      clearInterval(this.data.pollingTimer)
      this.data.pollingTimer = null
      console.log('订单列表轮询已停止')
    }
  },

  /**
   * 获取状态请求参数
   */
  getStatusRequestParams(status) {
    switch (status) {
      case 'pending':
        return { order_status: 0, pay_status: 0 }
      case 'preparing':
        return { order_status: 1 }
      case 'ready':
        return { order_status: 2 }
      case 'delivering':
        return { order_status: 3 }
      case 'completed':
        return { order_status: 4 }
      case 'cancelled':
        return { order_status: 5 }
      default:
        return {}
    }
  },

  /**
   * 处理订单数据
   */
  processOrderData(order) {
    // 计算金额
    const payAmount = Number(order.pay_amount) || Number(order.final_amount) || 0
    const totalAmount = Number(order.total_amount) || 0
    const discountAmount = totalAmount - payAmount

    // 兼容不同接口返回的订单商品字段
    const rawDishList =
      (Array.isArray(order.dishes) && order.dishes) ||
      (Array.isArray(order.items) && order.items) ||
      (Array.isArray(order.order_items) && order.order_items) ||
      (Array.isArray(order.details) && order.details) ||
      []

    const dishes = rawDishList.map((dish, index) => {
      const rawPrice = dish.price || dish.unit_price || dish.amount || dish.dish?.price || 0
      const quantity = Number(dish.quantity || dish.count || dish.num || 1) || 1
      const name =
        dish.name ||
        dish.dish_name ||
        dish.item_name ||
        dish.goods_name ||
        dish.product_name ||
        dish.title ||
        dish.dish?.name ||
        `商品${index + 1}`

      return {
        ...dish,
        dish_id: dish.dish_id || dish.id || dish.item_id || `dish_${index}`,
        image: util.formatImageUrl(
          dish.image ||
          dish.cover_url ||
          dish.cover ||
          dish.pic ||
          dish.image_url ||
          dish.dish?.image ||
          dish.dish?.cover_url ||
          dish.dish?.cover ||
          '/static/default-dish.png'
        ),
        name,
        price: util.formatPrice(rawPrice),
        quantity
      }
    })

    const dishesSummary = dishes.length
      ? dishes
          .slice(0, 2)
          .map(dish => `${dish.name}×${dish.quantity}`)
          .join('、') + (dishes.length > 2 ? ` 等${dishes.length}件` : '')
      : '暂无菜品信息'

    // 获取状态样式
    const statusStyle = this.getOrderStatusStyle(order.order_status, order.pay_status)

    // 计算进度百分比
    const progressPercent = this.calculateProgress(order.order_status)

    // 获取档口名称（后端已优化，直接从 canteen 对象获取）
    const canteenName = order.canteen?.canteen_name || order.canteen_name || '未知档口'

    // 计算倒计时（新增）
    const countdownInfo = this.calculateCountdown(order)

    return {
      ...order,
      order_id: order.order_id || order.id,
      canteen_name: canteenName,
      create_time_text: util.formatDate(order.create_time, 'MM-DD HH:mm'),
      order_status_text: this.getOrderStatusText(order.order_status, order.pay_status),
      status_bg: statusStyle.bg,
      status_color: statusStyle.color,
      pay_amount: payAmount,
      total_amount: totalAmount,
      discount_amount: discountAmount,
      pay_amount_text: util.formatPrice(payAmount),
      total_amount_text: util.formatPrice(totalAmount),
      discount_amount_text: util.formatPrice(discountAmount),
      dishes,
      dishes_summary: dishesSummary,
      delivery_address: order.address?.detail || order.delivery_address || '',
      delivery_type: order.delivery_type || 0, // 0-自取 1-配送
      pickup_code: order.pickup_code || '',
      is_reviewed: !!(order.is_reviewed || order.reviewed),
      progress_percent: progressPercent,
      // 倒计时相关（新增）
      countdown: countdownInfo.countdown,
      showCountdown: countdownInfo.showCountdown,
      countdownWarning: countdownInfo.warning
    }
  },

  /**
   * 获取订单状态文本
   */
  getOrderStatusText(orderStatus, payStatus) {
    if (orderStatus === 0 && payStatus === 0) return '待支付'
    if (orderStatus === 0 && payStatus === 1) return '待接单'
    if (orderStatus === 1) return '制作中'
    if (orderStatus === 2) return '待取餐'
    if (orderStatus === 3) return '配送中'
    if (orderStatus === 4) return '已完成'
    if (orderStatus === 5) return '已取消'
    return '未知状态'
  },

  /**
   * 获取订单状态样式
   */
  getOrderStatusStyle(orderStatus, payStatus) {
    if (orderStatus === 0 && payStatus === 0) {
      return { bg: 'linear-gradient(135deg, #ffe8e8 0%, #ffd6d6 100%)', color: '#ff4757' }
    } else if (orderStatus === 1) {
      return { bg: 'linear-gradient(135deg, #fff4e6 0%, #ffe8cc 100%)', color: '#ff9500' }
    } else if (orderStatus === 2) {
      return { bg: 'linear-gradient(135deg, #e6f7ff 0%, #cceeff 100%)', color: '#007aff' }
    } else if (orderStatus === 3) {
      return { bg: 'linear-gradient(135deg, #e6ffe6 0%, #ccffcc 100%)', color: '#34c759' }
    } else if (orderStatus === 4) {
      return { bg: 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)', color: '#8e8e93' }
    } else if (orderStatus === 5) {
      return { bg: 'linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%)', color: '#8e8e93' }
    }
    return { bg: '#f5f5f5', color: '#666666' }
  },

  /**
   * 计算订单进度百分比
   */
  calculateProgress(orderStatus) {
    if (orderStatus === 0) return 0
    if (orderStatus === 1) return 33
    if (orderStatus === 2) return 66
    if (orderStatus === 3) return 66
    if (orderStatus === 4) return 100
    return 0
  },

  /**
   * 计算倒计时（新增）
   */
  calculateCountdown(order) {
    // 只对未支付订单显示倒计时
    if (order.pay_status === 0 && order.order_status === 0) {
      const createTime = new Date(order.create_time)
      const now = new Date()
      const elapsed = Math.floor((now - createTime) / 1000 / 60) // 已过去的分钟数
      const remaining = 30 - elapsed // 剩余分钟数（30分钟超时）
      
      if (remaining > 0) {
        return {
          countdown: `${remaining}分钟后自动取消`,
          showCountdown: true,
          warning: remaining <= 5 // 剩余5分钟以内显示警告样式
        }
      } else {
        return {
          countdown: '即将取消',
          showCountdown: true,
          warning: true
        }
      }
    }
    
    return {
      countdown: '',
      showCountdown: false,
      warning: false
    }
  },

  /**
   * 启动倒计时定时器（新增）
   */
  startCountdownTimer() {
    // 如果已经有定时器，先清除
    this.stopCountdownTimer()
    
    // 每分钟更新一次倒计时
    this.data.countdownTimer = setInterval(() => {
      this.updateCountdown()
    }, 60000)
    
    console.log('倒计时定时器已启动')
  },

  /**
   * 停止倒计时定时器（新增）
   */
  stopCountdownTimer() {
    if (this.data.countdownTimer) {
      clearInterval(this.data.countdownTimer)
      this.data.countdownTimer = null
      console.log('倒计时定时器已停止')
    }
  },

  /**
   * 更新倒计时（新增）
   */
  updateCountdown() {
    const orders = this.data.orders.map(order => {
      const countdownInfo = this.calculateCountdown(order)
      return {
        ...order,
        countdown: countdownInfo.countdown,
        showCountdown: countdownInfo.showCountdown,
        countdownWarning: countdownInfo.warning
      }
    })
    
    this.setData({ orders })
  },

  /**
   * 匹配订单状态
   */
  matchOrderStatus(order, status) {
    switch (status) {
      case 'pending':
        return order.order_status === 0 && order.pay_status === 0
      case 'preparing':
        return order.order_status === 1
      case 'ready':
        return order.order_status === 2
      case 'delivering':
        return order.order_status === 3
      case 'completed':
        return order.order_status === 4
      case 'cancelled':
        return order.order_status === 5
      default:
        return true
    }
  },

  /**
   * 查看订单详情
   */
  onOrderDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/order/detail?id=${id}`
    })
  },

  /**
   * 支付订单
   */
  async onPayOrder(e) {
    const id = e.currentTarget.dataset.id
    
    // 找到对应的订单
    const order = this.data.orders.find(o => (o.order_id || o.id) === id)
    if (!order) {
      wx.showToast({ 
        title: '订单信息错误', 
        icon: 'none' 
      })
      return
    }
    
    // 确认支付
    wx.showModal({
      title: '确认支付',
      content: `订单金额：¥${order.pay_amount_text}\n\n确认支付此订单吗？`,
      confirmText: '确认支付',
      confirmColor: '#5b7dff',
      success: async (res) => {
        if (!res.confirm) return
        
    try {
          wx.showLoading({ title: '支付中...', mask: true })
      
      // 🎯 模拟支付：直接调用支付API，不调起微信支付
      await api.order.pay(id)
      
          wx.showModal({
            title: '支付成功',
            content: '订单支付成功，商家正在准备您的餐品',
            showCancel: false,
            confirmText: '知道了',
            success: () => {
      // 刷新订单列表
        this.loadOrders(true)
            }
          })
      
    } catch (error) {
      wx.hideLoading()
        console.error('支付失败:', error)
          
          wx.showModal({
            title: '支付失败',
            content: error.message,
            showCancel: false,
            confirmText: '知道了'
      })
    }
      }
    })
  },

  /**
   * 取消订单
   */
  onCancelOrder(e) {
    const id = e.currentTarget.dataset.id

    if (!id) {
      wx.showToast({ title: '订单ID不存在', icon: 'none' })
      return
    }

    // 找到对应的订单
    const order = this.data.orders.find(o => (o.order_id || o.id) === id)
    if (!order) {
      wx.showToast({ title: '订单信息错误', icon: 'none' })
      return
    }

    const cancelReasons = [
      '不想要了',
      '下错单了',
      '等待时间太长',
      '价格不合适',
      '其他原因'
    ]

    wx.showActionSheet({
      itemList: cancelReasons,
      success: (sheetRes) => {
        const reason = cancelReasons[sheetRes.tapIndex]

        // 根据支付状态显示不同的确认提示
        const isPaid = order.pay_status === 1
        const confirmTitle = isPaid ? '申请退款' : '确认取消订单'
        const confirmContent = isPaid 
          ? `取消原因：${reason}\n\n订单已支付，取消后需要等待管理员审批退款\n退款金额：¥${order.pay_amount_text}`
          : `取消原因：${reason}\n\n确认取消此订单？`
        const confirmText = isPaid ? '申请退款' : '确认取消'

        wx.showModal({
          title: confirmTitle,
          content: confirmContent,
          confirmText: confirmText,
          confirmColor: '#ff4757',
          success: async (modalRes) => {
            if (!modalRes.confirm) return
            
            try {
              wx.showLoading({ 
                title: isPaid ? '提交申请中...' : '取消中...', 
                mask: true 
              })
              
              const result = await api.order.cancel(id, { reason })
              
              wx.hideLoading()
              
              // 根据返回结果显示不同提示
              if (result.need_approval) {
                // 已支付订单，需要审批
                wx.showModal({
                  title: '退款申请已提交',
                  content: `退款金额：¥${result.refund_amount}\n\n请等待管理员审批，审批结果将通过消息通知您`,
                  showCancel: false,
                  confirmText: '知道了',
                  success: () => {
                    // 刷新订单列表
              this.loadOrders(true)
                  }
                })
              } else {
                // 未支付订单，直接取消成功
                wx.showToast({ 
                  title: '订单已取消', 
                  icon: 'success' 
                })
                
                // 刷新订单列表
                setTimeout(() => {
                  this.loadOrders(true)
                }, 1500)
              }
              
            } catch (error) {
              wx.hideLoading()
              console.error('取消订单失败:', error)
              wx.showToast({ 
                title: error.message, 
                icon: 'none' 
              })
            }
          }
        })
      }
    })
  },

  /**
   * 确认取餐（会触发后端更新菜品销量）
   */
  onConfirmPickup(e) {
    const id = e.currentTarget.dataset.id
    
    // 找到对应的订单
    const order = this.data.orders.find(o => (o.order_id || o.id) === id)
    
    wx.showModal({
      title: '确认取餐',
      content: order?.pickup_code 
        ? `取餐码：${order.pickup_code}\n\n确认已取到餐品了吗？确认后订单将完成。`
        : '确认已取到餐品了吗？确认后订单将完成。',
      confirmText: '确认取餐',
      confirmColor: '#5b7dff',
      success: async (res) => {
        if (res.confirm) {
          let loadingShown = false
          try {
            wx.showLoading({ title: '确认中...', mask: true })
            loadingShown = true
            
            // 调用确认接口，后端会自动更新菜品销量
            await api.order.confirm(id)
            
            if (loadingShown) {
            wx.hideLoading()
              loadingShown = false
            }
            
            // 成功提示
            wx.showModal({
              title: '取餐成功',
              content: '已确认取餐，感谢您的光临！\n\n期待您的评价，帮助其他用户做出选择',
              showCancel: false,
              confirmText: '知道了',
              success: () => {
                // 刷新订单列表
            this.loadOrders(true)
              }
            })
            
          } catch (error) {
            if (loadingShown) {
            wx.hideLoading()
            }
            console.error('确认取餐失败:', error)
            
            wx.showModal({
              title: '确认失败',
              content: error.message,
              showCancel: false,
              confirmText: '知道了'
            })
          }
        }
      }
    })
  },

  /**
   * 评价订单
   */
  onReviewOrder(e) {
    const id = e.currentTarget.dataset.id
    if (!id) {
      wx.showToast({
        title: '订单信息错误',
        icon: 'none'
      })
      return
    }

    const order = this.data.orders.find(o => String(o.order_id || o.id) === String(id))
    if (!order) {
      wx.showToast({
        title: '订单信息错误',
        icon: 'none'
      })
      return
    }

    if (order.is_reviewed) {
      wx.showToast({
        title: '该订单已评价',
        icon: 'none'
      })
      return
    }
    
    // 友好提示
    wx.showModal({
      title: '评价订单',
      content: '您的评价对其他用户很重要，快来分享您的用餐体验吧！',
      confirmText: '去评价',
      cancelText: '稍后再说',
      confirmColor: '#5b7dff',
      success: (res) => {
        if (res.confirm) {
          // 跳转到评价页面（批量评价模式），与订单详情页保持一致
    wx.navigateTo({
      url: `/pages/review/review?order_id=${id}`
          })
        }
      }
    })
  },

  /**
   * 再来一单
   */
  async onReorder(e) {
    const id = e.currentTarget.dataset.id
    if (!id) {
      wx.showToast({
        title: '订单ID不存在',
        icon: 'none'
      })
      return
    }

    console.log('再来一单（加入购物车），订单ID:', id)
    
    // 友好确认
    wx.showModal({
      title: '再来一单',
      content: '将本订单的所有商品重新加入购物车？',
      confirmText: '确定',
      confirmColor: '#5b7dff',
      success: async (res) => {
        if (!res.confirm) return

    try {
      wx.showLoading({ title: '添加中...', mask: true })

      // 先获取订单详情，拿到菜品列表
      const order = await api.order.detail(id)
      const items = Array.isArray(order?.items) ? order.items : (order?.dishes || [])

      if (!items || items.length === 0) {
        wx.hideLoading()
        wx.showToast({
          title: '订单中没有可添加的商品',
          icon: 'none'
        })
        return
      }

      // 逐个商品添加到购物车（按原数量）
          let successCount = 0
      for (const item of items) {
        const dishId = item.dish_id || item.dish?.dish_id || item.dish?.id
        const quantity = Number(item.quantity) || 1

        if (!dishId || quantity <= 0) continue

            try {
        // eslint-disable-next-line no-await-in-loop
        await api.cart.add({
          dish_id: dishId,
          quantity: quantity
        })
              successCount++
            } catch (err) {
              console.error('添加商品失败:', err)
            }
      }

      wx.hideLoading()
          
          if (successCount > 0) {
            wx.showModal({
              title: '添加成功',
              content: `已将 ${successCount} 个商品添加到购物车\n\n是否立即前往购物车查看？`,
              confirmText: '去购物车',
              cancelText: '继续逛逛',
              confirmColor: '#5b7dff',
              success: (modalRes) => {
                if (modalRes.confirm) {
                  wx.switchTab({ url: '/pages/cart/cart' })
                }
              }
            })
          } else {
      wx.showToast({
              title: '添加失败，请稍后重试',
              icon: 'none'
      })
          }

    } catch (error) {
      wx.hideLoading()
      console.error('再来一单失败:', error)
          wx.showModal({
            title: '操作失败',
            content: error.message,
            showCancel: false,
            confirmText: '知道了'
      })
    }
      }
    })
  },

  /**
   * 催单
   */
  async onRemindOrder(e) {
    const id = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '催单',
      content: '提醒商家加快制作速度？\n\n温馨提示：频繁催单可能影响商家服务质量',
      confirmText: '确认催单',
      confirmColor: '#ff9500',
      success: async (res) => {
        if (!res.confirm) return
        
        try {
          wx.showLoading({ title: '催单中...', mask: true })
          
      await api.order.remind(id)
          
          wx.hideLoading()
          wx.showModal({
            title: '催单成功',
            content: '已提醒商家加快制作，请耐心等待',
            showCancel: false,
            confirmText: '知道了'
      })
    } catch (error) {
          wx.hideLoading()
      console.error('催单失败:', error)
          
          wx.showModal({
            title: '催单失败',
            content: error.message,
            showCancel: false,
            confirmText: '知道了'
          })
    }
      }
    })
  },

  /**
   * 查看物流
   */
  onViewLogistics(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/order/logistics?id=${id}`
    })
  },

  /**
   * 联系客服
   */
  onContactService(e) {
    const id = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '联系客服',
      content: '是否拨打客服电话？',
      confirmText: '拨打',
      success: (res) => {
        if (res.confirm) {
          wx.makePhoneCall({
            phoneNumber: '400-123-4567'
          })
        }
      }
    })
  },

  /**
   * 删除订单
   */
  onDeleteOrder(e) {
    const id = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '删除订单',
      content: '确定要删除这个订单吗？\n\n删除后将无法恢复订单信息',
      confirmText: '确认删除',
      cancelText: '再想想',
      confirmColor: '#ff4757',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.order.delete(id)
            
            wx.showToast({ 
              title: '订单已删除', 
              icon: 'success',
              duration: 1500
            })
            
            // 延迟刷新，让用户看到成功提示
            setTimeout(() => {
            this.loadOrders(true)
            }, 1500)
            
          } catch (error) {
            console.error('删除订单失败:', error)
            
            wx.showModal({
              title: '删除失败',
              content: error.message,
              showCancel: false,
              confirmText: '知道了'
            })
          }
        }
      }
    })
  },

  /**
   * 去首页
   */
  onGoHome() {
    wx.switchTab({
      url: '/pages/index/index'
    })
  }
})
