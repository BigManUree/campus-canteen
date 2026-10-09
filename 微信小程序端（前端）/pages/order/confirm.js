// pages/order/confirm.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    canteenId: null,
    canteen: null,
    items: [],
    addresses: [],
    selectedAddress: null,
    orderType: 'pickup', // pickup/delivery
    pickupTime: '尽快送达',
    timePickerValue: [0, 0],
    timePickerRange: [[], []],
    remark: '',
    totalAmount: 0,
    totalAmountText: '0.00',
    discountAmount: 0,
    discountAmountText: '0.00',
    payAmount: 0,
    payAmountText: '0.00',
    loading: true,
    coupons: [],
    selectedCoupon: null,
    tempSelectedCoupon: null,
    hasExplicitNoCoupon: false,
    showCouponModal: false,
    canSubmitOrder: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    // 初始化时间选择器
    this.initTimePicker()

    // 从购物车或立即购买传入
    if (options.canteen_id) {
      this.setData({ canteenId: options.canteen_id })
    }
    
    if (options.dish_id) {
      // 立即购买
      this.loadDishItem(options.dish_id, parseInt(options.quantity || 1))
    } else if (options.from === 'cart') {
      // 从购物车结算
      this.loadCartItemsFromGlobal()
    } else {
      // 兼容旧版本：从本地存储加载
      this.loadCartItems()
    }
    
    this.loadAddresses()
    this.loadCanteen()
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    // 页面显示时重新加载地址（可能从地址页返回）
    this.loadAddresses()
  },

  // 初始化时间选择器
  initTimePicker() {
    const dates = []
    const times = []
    const today = new Date()
    
    // 生成未来7天的日期
    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() + i)
      const month = date.getMonth() + 1
      const day = date.getDate()
      const weekDay = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][date.getDay()]
      
      if (i === 0) {
        dates.push(`今天 ${month}月${day}日`)
      } else if (i === 1) {
        dates.push(`明天 ${month}月${day}日`)
      } else {
        dates.push(`${month}月${day}日 ${weekDay}`)
      }
    }
    
    // 生成时间段（默认包含“尽快送达”）
    times.push('尽快送达')
    for (let hour = 8; hour <= 20; hour++) {
      for (let minute = 0; minute < 60; minute += 30) {
        if (hour === 20 && minute > 0) break
        const timeStr = `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
        times.push(timeStr)
      }
    }
    
    this.setData({
      timePickerRange: [dates, times]
    })
  },

  // 时间选择器改变
  onTimePickerChange(e) {
    const [dateIndex, timeIndex] = e.detail.value
    const dateStr = this.data.timePickerRange[0][dateIndex]
    const timeStr = this.data.timePickerRange[1][timeIndex]
    const pickupTime = timeStr === '尽快送达' ? timeStr : `${dateStr} ${timeStr}`
    
    this.setData({
      timePickerValue: [dateIndex, timeIndex],
      pickupTime
    })
    this.updateSubmitState()
  },

  // 加载食堂信息
  async loadCanteen() {
    if (!this.data.canteenId) return
    
    try {
      const res = await api.canteen.detail(this.data.canteenId)
      this.setData({ 
        canteen: {
          ...res,
          is_open: true // 简化处理，实际应根据营业时间判断
        }
      })
    } catch (error) {
      console.error('加载食堂失败:', error)
    }
  },

  // 从全局数据加载购物车商品（新版本）
  async loadCartItemsFromGlobal() {
    try {
      const checkoutItems = app.globalData.checkoutItems || []
      
      if (checkoutItems.length === 0) {
        wx.showToast({ 
          title: '购物车为空', 
          icon: 'none' 
        })
        setTimeout(() => wx.navigateBack(), 1500)
        return
      }

      // 处理商品数据
      const items = checkoutItems.map(item => {
        const price = Number(item.price) || 0
        const quantity = Number(item.quantity) || 0
        const total = (price * quantity).toFixed(2)
        
        return {
          item_id: item.item_id,
          dish_id: item.dish_id,
          dish_name: item.dish_name,
          cover_url: util.formatImageUrl(item.cover_url || '/static/default-dish.png'),
          price: price.toFixed(2),
          quantity: quantity,
          total: total,
          tags: item.tags || [],
          remark: ''
        }
      })
      
      // 获取食堂ID
      if (items.length > 0 && checkoutItems[0].canteen_id) {
        this.setData({ canteenId: checkoutItems[0].canteen_id })
        this.loadCanteen()
      }
      
      this.setData({ 
        items, 
        loading: false 
      })
      
      this.calculateTotal()
      this.loadMyCoupons()
      this.updateSubmitState()
      
      // 清空全局数据
      app.globalData.checkoutItems = null
    } catch (e) {
      console.error('加载购物车失败:', e)
      this.setData({ loading: false })
      wx.showToast({ 
        title: e.message, 
        icon: 'none' 
      })
    }
  },

  // 加载购物车商品（兼容旧版本）
  async loadCartItems() {
    try {
      // 从本地存储读取购物车
      const cart = wx.getStorageSync('cart') || []
      
      if (cart.length === 0) {
        wx.showToast({ 
          title: '购物车为空', 
          icon: 'none' 
        })
        setTimeout(() => wx.navigateBack(), 1500)
        return
      }

      // 处理商品数据
      const items = cart.map(item => {
        const price = Number(item.price) || 0
        const quantity = Number(item.quantity) || 0
        const total = (price * quantity).toFixed(2)
        
        return {
          dish_id: item.dish_id,
          dish_name: item.name,
          cover_url: util.formatImageUrl(item.cover_url || '/static/default-dish.png'),
          price: price.toFixed(2),
          quantity: quantity,
          total: total,
          tags: item.tags || [],
          remark: ''
        }
      })
      
      // 获取食堂ID（假设购物车中的商品都是同一个食堂的）
      if (items.length > 0 && cart[0].canteen_id) {
        this.setData({ canteenId: cart[0].canteen_id })
        this.loadCanteen()
      }
      
      this.setData({ 
        items, 
        loading: false 
      })
      
      this.calculateTotal()
      this.loadMyCoupons()
      this.updateSubmitState()
    } catch (error) {
      console.error('加载购物车失败:', error)
      this.setData({ loading: false })
      wx.showToast({ 
        title: error.message, 
        icon: 'none' 
      })
    }
  },

  // 加载单品
  async loadDishItem(dishId, quantity) {
    try {
      const dish = await api.dish.detail(dishId)
      
      // 检查菜品状态
      if (!dish || dish.status !== 1) {
        wx.showToast({ 
          title: '菜品已下架', 
          icon: 'none' 
        })
        setTimeout(() => wx.navigateBack(), 1500)
        return
      }

      const price = Number(dish.price) || 0
      const qty = Math.max(1, parseInt(quantity) || 1)
      const total = (price * qty).toFixed(2)
      
      // 处理图片
      let cover_url = '/static/default-dish.png'
      if (dish.images) {
        if (Array.isArray(dish.images)) {
          cover_url = util.formatImageUrl(dish.images[0] || cover_url)
        } else if (typeof dish.images === 'string') {
          try {
            const images = JSON.parse(dish.images)
            cover_url = util.formatImageUrl(images[0] || cover_url)
          } catch (e) {
            cover_url = util.formatImageUrl(dish.images)
          }
        }
      }

      // 处理标签
      let tags = []
      if (dish.tags) {
        if (Array.isArray(dish.tags)) {
          tags = dish.tags
        } else if (typeof dish.tags === 'string') {
          try {
            tags = JSON.parse(dish.tags)
          } catch (e) {
            tags = dish.tags.split(',').map(t => t.trim()).filter(t => t)
          }
        }
      }
      
      this.setData({
        items: [{
          dish_id: dish.dish_id,
          dish_name: dish.name,
          cover_url: cover_url,
          price: price.toFixed(2),
          quantity: qty,
          total: total,
          tags: tags,
          remark: ''
        }],
        canteenId: dish.canteen_id,
        loading: false
      })
      
      this.loadCanteen()
      this.calculateTotal()
      this.loadMyCoupons()
      this.updateSubmitState()
    } catch (error) {
      console.error('加载菜品失败:', error)
      this.setData({ loading: false })
      wx.showToast({ 
        title: error.message, 
        icon: 'none' 
      })
    }
  },

  // 加载地址列表
  async loadAddresses() {
    try {
      const res = await api.address.list()
      const addresses = Array.isArray(res) ? res : []
      const defaultAddr = addresses.find(addr => addr.is_default === 1) || addresses[0]
      
      this.setData({
        addresses,
        selectedAddress: defaultAddr
      })
      this.updateSubmitState()
    } catch (error) {
      console.error('加载地址失败:', error)
      this.updateSubmitState()
    }
  },

  // 加载我的优惠券
  async loadMyCoupons() {
    try {
      const res = await api.coupon.my(0) // 获取未使用的优惠券
      const list = Array.isArray(res) ? res : []
      const now = Date.now()
      
      // 根据订单金额筛选可用优惠券，并排除已过期优惠券
      const total = Number(this.data.totalAmount) || 0
      const availableCoupons = list.filter(coupon => {
        if (!coupon || !coupon.coupon || coupon.status !== 0) return false

        const expireTime = coupon.expire_time ? new Date(coupon.expire_time).getTime() : NaN
        if (!Number.isNaN(expireTime) && expireTime <= now) return false

        const minAmount = Number(coupon.coupon.min_amount) || 0
        return total >= minAmount
      }).map((coupon, index) => {
        const couponInfo = coupon.coupon || {}
        const couponType = couponInfo.coupon_type || couponInfo.discount_type || 'cash'
        const discountValue = Number(couponInfo.discount_value) || 0
        const minAmount = Number(couponInfo.min_amount) || 0
        let expire_time_text = ''
        if (coupon.expire_time) {
          expire_time_text = util.formatDate(coupon.expire_time, 'YYYY-MM-DD')
        }
        return {
          ...coupon,
          _selectKey: String(coupon.user_coupon_id || `${coupon.coupon_id || couponInfo.coupon_id || 'coupon'}_${index}`),
          coupon: {
            ...couponInfo,
            coupon_type: couponType
          },
          coupon_display_value: this.formatCouponValue(couponType, discountValue),
          coupon_unit_text: this.formatCouponUnit(couponType),
          coupon_suffix_text: this.formatCouponSuffix(couponType),
          min_amount_text: util.formatPrice(minAmount),
          expire_time_text
        }
      })
      
      this.setData({ 
        coupons: availableCoupons
      })

      const { selectedCoupon, hasExplicitNoCoupon } = this.data
      const defaultCoupon = this.getBestCoupon(availableCoupons, total)

      if (selectedCoupon) {
        const stillAvailableCoupon = availableCoupons.find(item => item.user_coupon_id === selectedCoupon.user_coupon_id)
        const nextCoupon = stillAvailableCoupon || defaultCoupon
        this.setData({
          selectedCoupon: nextCoupon,
          tempSelectedCoupon: nextCoupon || '__NO_COUPON__',
          hasExplicitNoCoupon: !nextCoupon && hasExplicitNoCoupon
        })
        this.calculateTotal()
      } else if (hasExplicitNoCoupon) {
        this.setData({
          selectedCoupon: null,
          tempSelectedCoupon: '__NO_COUPON__'
        })
        this.calculateTotal()
      } else {
        if (defaultCoupon) {
          this.setData({
            selectedCoupon: defaultCoupon,
            tempSelectedCoupon: defaultCoupon,
            hasExplicitNoCoupon: false
          })
        } else {
          this.setData({
            selectedCoupon: null,
            tempSelectedCoupon: '__NO_COUPON__',
            hasExplicitNoCoupon: false
          })
        }
        this.calculateTotal()
      }
    } catch (error) {
      console.error('加载优惠券失败:', error)
    }
  },

  formatCouponValue(couponType, discountValue) {
    const value = Number(discountValue) || 0
    if (couponType === 'cash' || couponType === 'amount') {
      const fixed = value.toFixed(2)
      return fixed.endsWith('.00') ? String(Math.trunc(value)) : fixed
    }

    return value % 1 === 0 ? String(value) : String(parseFloat(value.toFixed(2)))
  },

  formatCouponUnit(couponType) {
    return couponType === 'cash' || couponType === 'amount' ? '¥' : ''
  },

  formatCouponSuffix(couponType) {
    return couponType === 'cash' || couponType === 'amount' ? '' : '折'
  },

  getBestCoupon(coupons = [], total = 0) {
    if (!Array.isArray(coupons) || coupons.length === 0) return null

    let bestCoupon = coupons[0]
    let bestDiscount = this.getCouponDiscount(total, bestCoupon)

    coupons.forEach(coupon => {
      const discount = this.getCouponDiscount(total, coupon)
      if (discount > bestDiscount) {
        bestCoupon = coupon
        bestDiscount = discount
      }
    })

    return bestCoupon
  },

  // 计算优惠金额
  getCouponDiscount(total, selectedCoupon) {
    if (!selectedCoupon || !selectedCoupon.coupon) return 0

    const coupon = selectedCoupon.coupon
    const minAmount = Number(coupon.min_amount) || 0
    if (total < minAmount) return 0

    const couponType = coupon.discount_type || coupon.coupon_type || 'amount'
    const discountValue = Number(coupon.discount_value) || 0

    if (couponType === 'amount' || couponType === 'cash') {
      return discountValue
    }

    if (couponType === 'percent' || couponType === 'discount') {
      if (discountValue <= 0) return 0
      let discount = 0
      if (discountValue <= 1) {
        discount = total * (1 - discountValue)
      } else if (discountValue <= 10) {
        discount = total * (1 - discountValue / 10)
      } else {
        discount = total * (1 - discountValue / 100)
      }

      const maxDiscount = Number(coupon.max_discount) || 0
      return maxDiscount > 0 ? Math.min(discount, maxDiscount) : discount
    }

    return 0
  },

  // 计算提交按钮是否可点击
  updateSubmitState() {
    const { orderType, pickupTime, selectedAddress, loading } = this.data

    let canSubmitOrder = false
    if (!loading) {
      if (orderType === 'pickup') {
        canSubmitOrder = !!(pickupTime && pickupTime.trim())
      } else {
        canSubmitOrder = !!(pickupTime && pickupTime.trim() && selectedAddress && selectedAddress.address_id)
      }
    }

    this.setData({ canSubmitOrder })
  },

  // 计算总价
  calculateTotal() {
    const { items, selectedCoupon } = this.data
    
    // 计算商品总额
    const total = items.reduce((sum, item) => {
      const price = Number(item.price) || 0
      const quantity = Number(item.quantity) || 0
      return sum + (price * quantity)
    }, 0)
    
    // 计算优惠金额
    let discount = this.getCouponDiscount(total, selectedCoupon)
    
    // 确保折扣不超过总金额
    discount = Math.min(discount, total)
    const payAmount = Math.max(0, total - discount)
    
    this.setData({
      totalAmount: total,
      totalAmountText: util.formatPrice(total),
      discountAmount: discount,
      discountAmountText: util.formatPrice(discount),
      payAmount: payAmount,
      payAmountText: util.formatPrice(payAmount)
    })
  },

  // 切换取餐方式
  onOrderTypeChange(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ orderType: type })
    this.updateSubmitState()
  },

  // 选择地址
  onSelectAddress() {
    if (this.data.addresses.length === 0) {
      wx.showModal({
        title: '提示',
        content: '您还没有添加地址，是否现在添加？',
        success: (res) => {
          if (res.confirm) {
            wx.navigateTo({
              url: '/pages/address/edit'
            })
          }
        }
      })
      return
    }

    const addressNames = this.data.addresses.map(addr => 
      `${addr.receiver} ${addr.phone}\n${addr.building} ${addr.room}`
    )

    wx.showActionSheet({
      itemList: addressNames,
      success: (res) => {
        this.setData({
          selectedAddress: this.data.addresses[res.tapIndex]
        })
        this.updateSubmitState()
      }
    })
  },

  // 添加地址
  onAddAddress() {
    wx.navigateTo({
      url: '/pages/address/edit'
    })
  },

  // 备注输入
  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  // 打开优惠券弹窗
  onSelectCoupon() {
    const { selectedCoupon, coupons, totalAmount } = this.data
    const bestCoupon = this.getBestCoupon(coupons, Number(totalAmount) || 0)
    const nextTempCoupon = selectedCoupon || bestCoupon || '__NO_COUPON__'

    this.setData({ 
      showCouponModal: true,
      tempSelectedCoupon: nextTempCoupon
    })
  },

  // 关闭优惠券弹窗
  onCloseCouponModal() {
    this.setData({ showCouponModal: false })
  },

  // 选择优惠券
  onCouponSelect(e) {
    const index = Number(e.currentTarget.dataset.index)
    
    if (index === -1) {
      this.setData({ tempSelectedCoupon: '__NO_COUPON__' })
      return
    }

    const selectedCoupon = this.data.coupons[index] || null
    this.setData({ tempSelectedCoupon: selectedCoupon })
  },

  // 确认选择优惠券
  onConfirmCoupon() {
    const nextCoupon = this.data.tempSelectedCoupon === '__NO_COUPON__'
      ? null
      : this.data.tempSelectedCoupon

    this.setData({ 
      selectedCoupon: nextCoupon,
      tempSelectedCoupon: nextCoupon,
      hasExplicitNoCoupon: this.data.tempSelectedCoupon === '__NO_COUPON__',
      showCouponModal: false
    })
    this.calculateTotal()
  },

  // 阻止冒泡
  stopPropagation() {},

  // 提交订单
  async onSubmitOrder() {
    const { items, canteenId, orderType, selectedAddress, pickupTime, remark, payAmount, canSubmitOrder } = this.data

    if (!canSubmitOrder) {
      const message = orderType === 'delivery' ? '请选择配送时间和地址' : '请选择取餐时间'
      wx.showToast({
        title: message,
        icon: 'none'
      })
      return
    }

    // 验证商品
    if (!items || items.length === 0) {
      wx.showToast({ 
        title: '请选择商品', 
        icon: 'none' 
      })
      return
    }

    // 验证档口
    if (!canteenId) {
      wx.showToast({ 
        title: '档口信息错误', 
        icon: 'none' 
      })
      return
    }

    // 验证配送地址
    if (orderType === 'delivery') {
      if (!selectedAddress) {
        wx.showToast({ 
          title: '请选择配送地址', 
          icon: 'none' 
        })
        return
      }
      if (!selectedAddress.address_id) {
        wx.showToast({ 
          title: '地址信息错误', 
          icon: 'none' 
        })
        return
      }
    }

    // 验证金额：允许优惠券全额抵扣后的 0 元订单
    if (payAmount < 0) {
      wx.showToast({ 
        title: '订单金额异常', 
        icon: 'none' 
      })
      return
    }

    try {
      wx.showLoading({ 
        title: '提交中...', 
        mask: true 
      })

      const orderData = {
        canteen_id: canteenId,
        order_type: orderType,
        items: items.map(item => ({
          dish_id: item.dish_id,
          quantity: item.quantity,
          remark: item.remark && item.remark.trim() ? item.remark.trim() : undefined
        })),
        remark: remark && remark.trim() ? remark.trim() : undefined
      }

      // 添加优惠券
      if (this.data.selectedCoupon && this.data.selectedCoupon.coupon_id) {
        orderData.coupon_id = this.data.selectedCoupon.coupon_id
      }

      // 添加配送地址
      if (orderType === 'delivery' && selectedAddress) {
        orderData.address_id = selectedAddress.address_id
      }

      // 添加取餐时间
      if (pickupTime && pickupTime.trim()) {
        orderData.pickup_time = pickupTime.trim()
      }

      const res = await api.order.create(orderData)

      // 验证返回结果
      if (!res || !res.order_id) {
        throw new Error('订单创建失败，返回数据异常')
      }

      wx.hideLoading()
      wx.showToast({ 
        title: '下单成功', 
        icon: 'success' 
      })

      // 清空购物车（如果是从购物车结算的，需要删除已结算的商品）
      if (items && items.length > 0) {
        try {
          // 删除已结算的购物车商品
          const deletePromises = items
            .filter(item => item.item_id) // 只删除有item_id的（从购物车来的）
            .map(item => api.cart.remove(item.item_id))
          
          if (deletePromises.length > 0) {
            await Promise.all(deletePromises)
          }
        } catch (error) {
          console.error('清空购物车失败:', error)
        }
      }

      // 跳转到订单详情
      setTimeout(() => {
        wx.redirectTo({
          url: `/pages/order/detail?id=${res.order_id}`
        })
      }, 1500)

    } catch (error) {
      wx.hideLoading()
      console.error('下单失败:', error)
      
      // 优化库存不足提示
      const errorMessage = error.message
      
      if (errorMessage.includes('库存不足')) {
        // 库存不足使用 Modal 显示详细信息
        wx.showModal({
          title: '库存不足',
          content: errorMessage,
          showCancel: false,
          confirmText: '知道了',
          confirmColor: '#ff6b6b',
          success: () => {
            // 返回上一页重新选择
            wx.navigateBack()
          }
        })
      } else {
        // 其他错误使用 Toast
        wx.showToast({
          title: errorMessage.length > 20 ? errorMessage.substring(0, 20) + '...' : errorMessage,
          icon: 'none',
          duration: 2000
        })
      }
    }
  },

  // 返回
  onBack() {
    wx.navigateBack()
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
  }
})
