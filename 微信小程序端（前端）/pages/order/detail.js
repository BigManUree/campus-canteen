// pages/order/detail.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    orderId: null,
    order: null,
    timeline: [],
    loading: true,
    timelineLoading: false,
    paying: false,  // 支付中标志，防止重复点击
    pollingTimer: null,  // 轮询定时器
    lastOrderStatus: null,  // 上次的订单状态，用于检测状态变化
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  // 错误消息映射
  ERROR_MESSAGES: {
    '订单已支付': '订单已支付，无需重复支付',
    '订单已取消，无法支付': '订单已取消，请重新下单',
    '订单不存在': '订单不存在，请刷新后重试',
    '订单状态异常': '订单状态异常，无法支付',
    '支付金额异常': '支付金额异常，请联系客服'
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ orderId: options.id })
      this.loadOrder()
    } else {
      wx.showToast({ title: '未获取到订单信息', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1200)
    }
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (!this.data.orderId) return
    this.loadOrder()
    this.loadTimeline()
    
    // 启动轮询（只对未完成的订单）
    if (this.data.order && this.data.order.order_status < 4) {
      this.startPolling()
    }
  },

  onHide() {
    // 页面隐藏时停止轮询
    this.stopPolling()
  },

  onUnload() {
    // 页面卸载时停止轮询
    this.stopPolling()
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

  // 加载订单详情
  async loadOrder(silent = false) {
    if (!this.data.orderId) return
    try {
      if (!silent) {
        this.setData({ loading: true })
      }
      
      const res = await api.order.detail(this.data.orderId)
      
      if (!res) {
        this.setData({ loading: false })
        return
      }
      
      // 检测订单状态变化
      const oldStatus = this.data.lastOrderStatus
      const newStatus = res.order_status
      
      // 处理订单项，为每个 item 添加格式化的 total
      let items = []
      if (res.items && Array.isArray(res.items)) {
        items = res.items.map(item => {
          const price = Number(item.price) || 0
          const quantity = Number(item.quantity) || 0
          const total = price * quantity
          return {
            ...item,
            image: util.formatImageUrl(
              item.image ||
              item.cover ||
              item.cover_url ||
              item.image_url ||
              '/static/default-dish.png'
            ),
            price: util.formatPrice(price),
            quantity: quantity,
            total: total,
            total_text: util.formatPrice(total)
          }
        })
      }
      
      // 格式化金额字段（统一使用Number处理）
      const totalAmount = Number(res.total_amount) || 0
      const discountAmount = Number(res.discount_amount) || 0
      const payAmount = Number(res.pay_amount) || 0
      
      const order = {
        ...res,
        is_reviewed: !!(res.is_reviewed || res.reviewed),
        items: items,
        total_amount: totalAmount,
        discount_amount: discountAmount,
        pay_amount: payAmount,
        total_amount_text: util.formatPrice(totalAmount),
        discount_amount_text: util.formatPrice(discountAmount),
        pay_amount_text: util.formatPrice(payAmount),
        create_time_text: util.formatDate(res.create_time, 'YYYY-MM-DD HH:mm'),
        create_time_full_text: util.formatDate(res.create_time, 'YYYY-MM-DD HH:mm:ss'),
        pickup_time_text: res.pickup_time ? util.formatDate(res.pickup_time, 'YYYY-MM-DD HH:mm') : '',
        order_status_text: util.getOrderStatusText(res.order_status),
        order_status_color: util.getOrderStatusColor(res.order_status),
        pay_status_text: res.pay_status === 1 ? '已支付' : '未支付',
        cancel_reason_text: res.cancel_reason || '',
        canteen_display_name: res.canteen?.canteen_name || '食堂档口',
        canteen_location_text: [res.canteen?.building, res.canteen?.floor, res.canteen?.window_no ? `窗口 ${res.canteen.window_no}` : '']
          .filter(Boolean)
          .join(' · '),
        progress_percent: this.getProgressPercent(res.order_status),
        progress_steps: this.buildProgressSteps(res),
        status_meta: this.getStatusMeta(res.order_status, res.pay_status)
      }
      
      this.setData({
        order: order,
        loading: false,
        lastOrderStatus: newStatus
      })
      
      // 如果状态发生变化，显示通知并刷新时间线
      if (oldStatus !== null && oldStatus !== newStatus) {
        this.showStatusChangeNotification(order)
        this.loadTimeline()
      }
      
      // 如果订单已完成或已取消，停止轮询
      if (newStatus >= 4) {
        this.stopPolling()
      } else if (!this.data.pollingTimer) {
        // 如果订单未完成且轮询未启动，启动轮询
        this.startPolling()
      }
      
      // 首次加载时也加载时间线
      if (!silent) {
        this.loadTimeline()
      }
    } catch (error) {
      console.error('加载订单失败:', error)
      this.setData({ loading: false })
    }
  },

  // 启动轮询
  startPolling() {
    // 如果已经有定时器，先清除
    this.stopPolling()
    
    // 每5秒刷新一次订单状态
    this.data.pollingTimer = setInterval(() => {
      this.loadOrder(true)  // 静默刷新，不显示loading
    }, 5000)
    
    console.log('订单状态轮询已启动')
  },

  // 停止轮询
  stopPolling() {
    if (this.data.pollingTimer) {
      clearInterval(this.data.pollingTimer)
      this.data.pollingTimer = null
      console.log('订单状态轮询已停止')
    }
  },

  // 显示状态变更通知
  showStatusChangeNotification(order) {
    const statusMessages = {
      1: '商家已接单，正在制作中',
      2: `制作完成，请前往取餐\n取餐码：${order.pickup_code || ''}`,
      3: '订单正在配送中',
      4: '订单已完成',
      5: '订单已取消'
    }
    
    const message = statusMessages[order.order_status]
    if (message) {
      wx.showModal({
        title: '订单状态更新',
        content: message,
        showCancel: false,
        confirmText: '知道了'
      })
      
      // 播放提示音和震动
      wx.vibrateShort()
    }
  },

  // 加载订单时间线
  async loadTimeline() {
    if (!this.data.orderId) return
    
    try {
      this.setData({ timelineLoading: true })
      const res = await api.order.timeline(this.data.orderId)
      
      // 处理时间线数据
      const timeline = (res.timeline || []).map(item => ({
        ...item,
        time_text: util.formatDate(item.timestamp, 'MM-DD HH:mm')
      }))
      
      this.setData({
        timeline,
        timelineLoading: false
      })
    } catch (error) {
      console.error('加载订单时间线失败:', error)
      this.setData({ timelineLoading: false })
    }
  },

  // 取消订单
  async onCancelOrder() {
    const { order } = this.data
    
    // 验证订单状态
    if (!order || !order.order_id) {
      wx.showToast({ title: '订单信息错误', icon: 'none' })
      return
    }

    // 检查订单是否可以取消
    if (order.order_status > 1) {
      wx.showToast({ 
        title: '订单已在制作或配送中，无法取消', 
        icon: 'none',
        duration: 2000
      })
      return
    }

    if (order.order_status === 5) {
      wx.showToast({ title: '订单已取消', icon: 'none' })
      return
    }

    // 弹出取消原因选择
    const cancelReasons = [
      '不想要了',
      '下错单了',
      '等待时间太长',
      '价格不合适',
      '其他原因'
    ]

    wx.showActionSheet({
      itemList: cancelReasons,
      success: async (res) => {
        const reason = cancelReasons[res.tapIndex]
        
        // 根据支付状态显示不同的确认提示
        const isPaid = order.pay_status === 1
        const confirmTitle = isPaid ? '申请退款' : '确认取消订单'
        const confirmContent = isPaid 
          ? `取消原因：${reason}\n\n订单已支付，取消后需要等待管理员审批退款\n退款金额：¥${order.pay_amount_text}`
          : `取消原因：${reason}\n\n确认取消此订单？`
        const confirmText = isPaid ? '申请退款' : '确认取消'
        
        // 二次确认
        wx.showModal({
          title: confirmTitle,
          content: confirmContent,
          confirmText: confirmText,
          confirmColor: '#ff5252',
          success: async (modalRes) => {
            if (modalRes.confirm) {
              try {
                wx.showLoading({ 
                  title: isPaid ? '提交申请中...' : '取消中...', 
                  mask: true 
                })
                
                // 发送取消请求
                const result = await api.order.cancel(this.data.orderId, { reason })
                
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
                      // 刷新订单详情
                      this.loadOrder()
                      this.loadTimeline()
                    }
                  })
                } else {
                  // 未支付订单，直接取消成功
                  wx.showToast({ 
                    title: '订单已取消', 
                    icon: 'success',
                    duration: 2000
                  })
                  
                  // 刷新订单详情
                  setTimeout(() => {
                    this.loadOrder()
                    this.loadTimeline()
                  }, 1500)
                }
                
              } catch (error) {
                wx.hideLoading()
                console.error('取消订单失败:', error)
                
                wx.showToast({
                  title: error.message,
                  icon: 'none',
                  duration: 2000
                })
              }
            }
          }
        })
      }
    })
  },

  // 导航到档口
  onNavigate() {
    const { order } = this.data
    if (order && order.canteen) {
      if (order.canteen.latitude && order.canteen.longitude) {
        util.openLocation(order.canteen.latitude, order.canteen.longitude, order.canteen.canteen_name)
      }
    }
  },

  // 支付订单（模拟支付）
  async onPayOrder() {
    const { order, paying } = this.data
    
    // ✅ 防止重复点击
    if (paying) {
      console.log('支付进行中，请勿重复点击')
      return
    }
    
    // 验证订单信息
    if (!order || !order.order_id) {
      wx.showToast({ title: '订单信息错误', icon: 'none' })
      return
    }

    // ✅ 检查订单支付状态
    if (order.pay_status === 1) {
      wx.showToast({ 
        title: '订单已支付，无需重复支付', 
        icon: 'none',
        duration: 2000
      })
      // 刷新订单详情，显示最新状态
      this.loadOrder()
      return
    }

    // 验证支付金额：允许 0 元订单免支付完成
    const payAmount = Number(order.pay_amount) || 0
    if (payAmount < 0) {
      wx.showToast({ title: '支付金额异常', icon: 'none' })
      return
    }

    // ✅ 检查订单状态是否可以支付
    if (order.order_status === 5) {
      wx.showToast({ 
        title: '订单已取消，无法支付', 
        icon: 'none',
        duration: 2000
      })
      return
    }

    wx.showModal({
      title: '确认支付',
      content: `确认支付 ¥${util.formatPrice(payAmount)} 吗？`,
      success: async (res) => {
        if (res.confirm) {
          // ✅ 设置支付中状态
          this.setData({ paying: true })
          
          try {
            wx.showLoading({ title: '支付中...', mask: true })
            
            // 🎯 模拟支付：通过状态更新接口将订单置为已支付/制作中
            await api.order.pay(this.data.orderId)
            
            wx.showToast({ 
              title: '支付成功', 
              icon: 'success',
              duration: 2000
            })
            
            // 延迟刷新订单详情
            setTimeout(() => {
              this.loadOrder()
              this.loadTimeline()
            }, 1500)
            
          } catch (error) {
            wx.hideLoading()
            console.error('支付失败:', error)
            
            // ✅ 友好的错误提示
            const friendlyMessage = this.ERROR_MESSAGES[error.message] || error.message
            
            wx.showToast({
              title: friendlyMessage,
              icon: 'none',
              duration: 2500
            })
            
            // ✅ 如果是"订单已支付"错误，刷新订单详情
            if (error.message === '订单已支付') {
              setTimeout(() => {
                this.loadOrder()
                this.loadTimeline()
              }, 1500)
            }
            
          } finally {
            // ✅ 重置支付中状态
            this.setData({ paying: false })
          }
        }
      }
    })
  },

  // 获取进度百分比
  getProgressPercent(status) {
    if (status === 0) return 12
    if (status === 1) return 42
    if (status === 2) return 72
    if (status === 3) return 86
    if (status === 4) return 100
    return 0
  },

  // 构建进度步骤
  buildProgressSteps(order) {
    const isDelivery = order.order_type === 'delivery'
    return [
      {
        key: 'paid',
        label: order.pay_status === 1 ? '支付完成' : '等待支付',
        active: order.pay_status === 1 || order.order_status > 0,
        current: order.order_status === 0,
        done: order.pay_status === 1
      },
      {
        key: 'making',
        label: '商家制作',
        active: order.order_status >= 1,
        current: order.order_status === 1,
        done: order.order_status > 1
      },
      {
        key: 'fulfill',
        label: isDelivery ? '配送中' : '待取餐',
        active: order.order_status >= 2,
        current: order.order_status === 2 || order.order_status === 3,
        done: order.order_status > 3
      },
      {
        key: 'finish',
        label: order.order_status === 5 ? '订单取消' : '订单完成',
        active: order.order_status === 4 || order.order_status === 5,
        current: order.order_status === 4 || order.order_status === 5,
        done: order.order_status === 4
      }
    ]
  },

  // 获取状态展示信息
  getStatusMeta(status, payStatus) {
    if (status === 0 && payStatus === 0) {
      return {
        icon: '⌛',
        badge: '待支付',
        title: '订单等待支付',
        desc: '完成支付后商家将立即开始处理你的餐品。',
        theme: 'pending'
      }
    }
    if (status === 0 && payStatus === 1) {
      return {
        icon: '🧾',
        badge: '待接单',
        title: '订单已支付，等待商家确认',
        desc: '商家确认后会进入制作流程，你可以在这里实时查看进度。',
        theme: 'paid'
      }
    }
    if (status === 1) {
      return {
        icon: '👨‍🍳',
        badge: '制作中',
        title: '商家正在制作你的餐品',
        desc: '可以稍后回来查看，取餐码准备好后会第一时间展示。',
        theme: 'making'
      }
    }
    if (status === 2) {
      return {
        icon: '📦',
        badge: '待取餐',
        title: '餐品已准备完成',
        desc: '请尽快前往档口取餐，出示取餐码可快速核销。',
        theme: 'ready'
      }
    }
    if (status === 3) {
      return {
        icon: '🛵',
        badge: '配送中',
        title: '订单正在配送途中',
        desc: '请保持电话畅通，配送完成后可在详情页查看状态更新。',
        theme: 'delivery'
      }
    }
    if (status === 4) {
      return {
        icon: '✓',
        badge: '已完成',
        title: '订单已完成',
        desc: '味道如何？欢迎评价本次订单，也可以一键再来一单。',
        theme: 'success'
      }
    }
    return {
      icon: '×',
      badge: '已取消',
      title: '订单已取消',
      desc: '如果你还想吃这份餐品，可以稍后重新下单。',
      theme: 'cancel',
      action: 'back'
    }
  },

  onHeroIconTap() {
    const { order } = this.data
    if (!order || !order.status_meta || !order.status_meta.action) return

    if (order.status_meta.action === 'back') {
      wx.navigateBack({
        fail: () => {
          wx.switchTab({ url: '/pages/profile/profile' })
        }
      })
    }
  },

  // 催单
  async onRemind() {
    return util.withLock('order_remind', async () => {
      try {
        await api.order.remind(this.data.orderId)
        wx.showToast({ title: '催单成功', icon: 'success' })
      } catch (error) {
        console.error('催单失败:', error)
      }
    }, 2000)
  },

  // 再次下单
  async onReorder() {
    const { order } = this.data
    
    if (!order) {
      wx.showToast({ title: '订单信息错误', icon: 'none' })
      return
    }

    const orderId = order.order_id || order.id
    
    if (!orderId) {
      wx.showToast({ title: '订单ID不存在', icon: 'none' })
      return
    }

    console.log('再来一单（加入购物车），订单ID:', orderId)

    wx.showModal({
      title: '再来一单',
      content: '将本订单商品重新加入购物车？',
      confirmText: '确定',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '添加中...', mask: true })

            // 直接使用当前详情里的订单项
            const items = Array.isArray(order.items) ? order.items : (order.dishes || [])

            if (!items || items.length === 0) {
              wx.hideLoading()
              wx.showToast({
                title: '订单中没有可添加的商品',
                icon: 'none'
              })
              return
            }

            for (const item of items) {
              const dishId = item.dish_id || item.dish?.dish_id || item.dish?.id
              const quantity = Number(item.quantity) || 1

              if (!dishId || quantity <= 0) continue

              // eslint-disable-next-line no-await-in-loop
              await api.cart.add({
                dish_id: dishId,
                quantity: quantity
              })
            }

            wx.hideLoading()
            wx.showToast({
              title: '已添加到购物车',
              icon: 'success',
              duration: 1500
            })

            setTimeout(() => {
              wx.switchTab({ url: '/pages/cart/cart' })
            }, 1500)
          } catch (error) {
            wx.hideLoading()
            console.error('再来一单失败:', error)
            
            wx.showToast({ 
              title: error.message, 
              icon: 'none',
              duration: 2000
            })
          }
        }
      }
    })
  },

  // 复制取餐码
  onCopyPickupCode() {
    if (this.data.order.pickup_code) {
      wx.setClipboardData({
        data: this.data.order.pickup_code,
        success: () => {
          wx.showToast({ title: '已复制', icon: 'success' })
        }
      })
    }
  },

  // 申请退款
  onRefund() {
    const { order } = this.data
    
    if (!order) {
      wx.showToast({ 
        title: '订单信息错误', 
        icon: 'none' 
      })
      return
    }
    
    // 检查订单是否可以退款
    if (order.pay_status !== 1) {
      wx.showToast({ 
        title: '订单尚未支付，无法申请退款', 
        icon: 'none' 
      })
      return
    }
    
    if (order.order_status >= 4) {
      wx.showToast({ 
        title: '订单已完成，无法申请退款', 
        icon: 'none' 
      })
      return
    }
    
    if (order.order_status === 5) {
      wx.showToast({ 
        title: '订单已取消', 
        icon: 'none' 
      })
      return
    }
    
    // 跳转到退款申请页面
    wx.navigateTo({
      url: `/pages/refund/apply?order_id=${this.data.orderId}`
    })
  },

  // 去评价
  onReview() {
    const { order } = this.data
    console.log('点击评价按钮，订单数据:', order)
    
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
    
    const orderId = order.order_id || order.id
    
    if (!orderId) {
      wx.showToast({ 
        title: '订单ID不存在', 
        icon: 'none' 
      })
      return
    }
    
    // 检查订单是否已完成
    if (order.order_status !== 4) {
      wx.showToast({ 
        title: '订单未完成，暂不能评价', 
        icon: 'none' 
      })
      return
    }
    
    // 跳转到评价页面，不指定菜品ID，进入批量评价模式
    console.log('跳转到评价页面，订单ID:', orderId)
    wx.navigateTo({
      url: `/pages/review/review?order_id=${orderId}`,
      fail: (err) => {
        console.error('跳转评价页面失败:', err)
        wx.showToast({ 
          title: '页面跳转失败', 
          icon: 'none' 
        })
      }
    })
  },

  // 获取订单状态文本
  getOrderStatusText(status) {
    const statusMap = {
      0: '待确认',
      1: '制作中',
      2: '待取餐',
      3: '配送中',
      4: '已完成',
      5: '已取消'
    }
    return statusMap[status] || '未知状态'
  },

  // 获取订单状态颜色
  getOrderStatusColor(status) {
    const colorMap = {
      0: '#ff9800',
      1: '#2196f3',
      2: '#9c27b0',
      3: '#00bcd4',
      4: '#4caf50',
      5: '#9e9e9e'
    }
    return colorMap[status] || '#757575'
  },

  // 获取支付状态文本
  getPayStatusText(payStatus) {
    return payStatus === 1 ? '已支付' : '未支付'
  }
})
