// pages/refund/apply.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')

Page({
  data: {
    orderId: null,
    order: null,
    refundType: 'full', // full: 全额退款, partial: 部分退款
    selectedDishes: [], // 选中的菜品（部分退款）
    refundAmount: 0,
    refundAmountText: '0.00',
    selectedDishCount: 0,
    selectedDishQuantity: 0,
    // 退款原因
    reasonCategory: 'dont_want',
    reasonOptions: [
      { value: 'dont_want', label: '不想要了' },
      { value: 'too_long', label: '等太久' },
      { value: 'quality', label: '质量问题' },
      { value: 'other', label: '其他原因' }
    ],
    reasonDetail: '',
    
    loading: true,
    submitting: false
  },

  onLoad(options) {
    if (options.order_id) {
      this.setData({ orderId: options.order_id })
      this.loadOrderDetail()
    } else {
      wx.showToast({
        title: '订单信息错误',
        icon: 'none'
      })
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    }
  },

  // 加载订单详情
  async loadOrderDetail() {
    try {
      this.setData({ loading: true })
      
      const order = await api.order.detail(this.data.orderId)
      
      // 检查订单状态是否可以退款
      if (order.pay_status !== 1) {
        wx.showModal({
          title: '无法退款',
          content: '该订单尚未支付，无法申请退款',
          showCancel: false,
          success: () => {
            wx.navigateBack()
          }
        })
        return
      }
      
      if (order.order_status >= 4) {
        wx.showModal({
          title: '无法退款',
          content: '该订单已完成，无法申请退款',
          showCancel: false,
          success: () => {
            wx.navigateBack()
          }
        })
        return
      }
      
      const payAmount = Number(order.pay_amount || order.final_amount || 0)
      const totalAmount = Number(order.total_amount || order.original_amount || order.pay_amount || order.final_amount || 0)
      const rawDishes = Array.isArray(order.items) ? order.items : (Array.isArray(order.dishes) ? order.dishes : [])
      const dishes = this.buildRefundableDishes(rawDishes, totalAmount, payAmount)
      
      this.setData({
        order: {
          ...order,
          dishes,
          pay_amount: payAmount,
          pay_amount_text: util.formatPrice(payAmount),
          total_amount: totalAmount,
          total_amount_text: util.formatPrice(totalAmount),
          create_time_text: util.formatDate(order.create_time, 'YYYY-MM-DD HH:mm')
        },
        refundAmount: payAmount,
        refundAmountText: util.formatPrice(payAmount),
        selectedDishes: [],
        selectedDishCount: 0,
        selectedDishQuantity: 0,
        loading: false
      })
      
    } catch (e) {
      console.error('加载订单失败:', e)
      wx.showToast({
        title: e.message,
        icon: 'none'
      })
      this.setData({ loading: false })
    }
  },

  buildRefundableDishes(dishes = [], totalAmount = 0, payAmount = 0) {
    const normalizedTotal = Number(totalAmount) || 0
    const normalizedPay = Number(payAmount) || 0
    const ratio = normalizedTotal > 0 ? normalizedPay / normalizedTotal : 1

    return dishes.map((dish, index) => {
      const price = Number(dish.price || dish.dish_price || 0)
      const quantity = Math.max(1, Number(dish.quantity || 1))
      const lineOriginalAmount = price * quantity
      const lineRefundableAmount = this.roundPrice(lineOriginalAmount * ratio)
      const unitRefundableAmount = quantity > 0
        ? this.roundPrice(lineRefundableAmount / quantity)
        : 0

      return {
        ...dish,
        selected: false,
        selectedQuantity: 0,
        maxRefundQuantity: quantity,
        dish_id: dish.dish_id || dish.id,
        name: dish.name || dish.dish_name,
        price,
        quantity,
        image: util.formatImageUrl(dish.image || dish.cover || dish.cover_url || '/static/default-dish.png'),
        lineOriginalAmount,
        lineOriginalAmountText: util.formatPrice(lineOriginalAmount),
        lineRefundableAmount,
        lineRefundableAmountText: util.formatPrice(lineRefundableAmount),
        unitRefundableAmount,
        unitRefundableAmountText: util.formatPrice(unitRefundableAmount),
        refund_amount: 0,
        refund_amount_text: '0.00',
        manualRefundAmountInput: '',
        isManualAmountEdited: false,
        _index: index
      }
    })
  },

  roundPrice(amount) {
    return Math.round((Number(amount) || 0) * 100) / 100
  },

  parseRefundAmount(value) {
    const cleaned = String(value ?? '').replace(/[^\d.]/g, '')
    if (!cleaned) return 0
    const parsed = parseFloat(cleaned)
    if (Number.isNaN(parsed)) return 0
    return this.roundPrice(parsed)
  },

  formatRefundInput(amount) {
    const normalized = this.roundPrice(amount)
    return normalized > 0 ? util.formatPrice(normalized) : ''
  },

  getDishMaxRefundAmount(dish) {
    return this.roundPrice((Number(dish.unitRefundableAmount) || 0) * (Number(dish.selectedQuantity) || 0))
  },

  clampDishRefundQuantity(value, maxQuantity) {
    const parsed = parseInt(value, 10)
    if (Number.isNaN(parsed)) return 0
    return Math.max(0, Math.min(Number(maxQuantity) || 0, parsed))
  },

  normalizeRefundAmount(selectedDishes = [], maxRefundAmount = 0) {
    const normalizedMax = this.roundPrice(maxRefundAmount)
    const dishes = selectedDishes.map(dish => ({ ...dish }))
    let total = this.roundPrice(dishes.reduce((sum, dish) => sum + (Number(dish.refund_amount) || 0), 0))

    if (total <= normalizedMax) {
      return {
        selectedDishes: dishes,
        refundAmount: total
      }
    }

    let overflow = this.roundPrice(total - normalizedMax)
    for (let i = dishes.length - 1; i >= 0 && overflow > 0; i--) {
      const current = Number(dishes[i].refund_amount) || 0
      const nextAmount = this.roundPrice(Math.max(0, current - overflow))
      overflow = this.roundPrice(overflow - (current - nextAmount))
      dishes[i].refund_amount = nextAmount
      dishes[i].refund_amount_text = util.formatPrice(nextAmount)
    }

    total = this.roundPrice(dishes.reduce((sum, dish) => sum + (Number(dish.refund_amount) || 0), 0))
    return {
      selectedDishes: dishes,
      refundAmount: Math.min(total, normalizedMax)
    }
  },

  recalculatePartialRefund(dishes = []) {
    const payAmount = Number(this.data.order?.pay_amount || 0)
    const selectedDishes = dishes
      .filter(dish => Number(dish.selectedQuantity) > 0)
      .map(dish => {
        const maxDishRefundAmount = this.getDishMaxRefundAmount(dish)
        const desiredRefundAmount = dish.isManualAmountEdited
          ? this.parseRefundAmount(dish.manualRefundAmountInput)
          : maxDishRefundAmount
        const refundAmount = this.roundPrice(Math.min(Math.max(desiredRefundAmount, 0), maxDishRefundAmount))

        return {
          ...dish,
          selected: true,
          refund_quantity: dish.selectedQuantity,
          max_dish_refund_amount: maxDishRefundAmount,
          max_dish_refund_amount_text: util.formatPrice(maxDishRefundAmount),
          refund_amount: refundAmount,
          refund_amount_text: util.formatPrice(refundAmount),
          manualRefundAmountInput: dish.isManualAmountEdited
            ? this.formatRefundInput(refundAmount)
            : this.formatRefundInput(refundAmount)
        }
      })

    const normalized = this.normalizeRefundAmount(selectedDishes, payAmount)
    const finalSelectedDishes = normalized.selectedDishes
    const refundAmount = normalized.refundAmount
    const selectedDishQuantity = finalSelectedDishes.reduce((sum, dish) => {
      return sum + (Number(dish.refund_quantity) || 0)
    }, 0)

    const mergedDishes = dishes.map(dish => {
      const matchedDish = finalSelectedDishes.find(item => item.dish_id === dish.dish_id && item._index === dish._index)
      if (!matchedDish) {
        return {
          ...dish,
          refund_amount: 0,
          refund_amount_text: '0.00',
          manualRefundAmountInput: '',
          isManualAmountEdited: false
        }
      }

      return {
        ...dish,
        refund_amount: matchedDish.refund_amount,
        refund_amount_text: matchedDish.refund_amount_text,
        max_dish_refund_amount: matchedDish.max_dish_refund_amount,
        max_dish_refund_amount_text: matchedDish.max_dish_refund_amount_text,
        manualRefundAmountInput: matchedDish.manualRefundAmountInput,
        isManualAmountEdited: matchedDish.isManualAmountEdited,
        selected: true
      }
    })

    this.setData({
      'order.dishes': mergedDishes,
      selectedDishes: finalSelectedDishes,
      selectedDishCount: finalSelectedDishes.length,
      selectedDishQuantity,
      refundAmount,
      refundAmountText: util.formatPrice(refundAmount)
    })
  },

  // 切换退款类型
  onRefundTypeChange(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ refundType: type })
    
    if (type === 'full') {
      // 全额退款
      const dishes = this.data.order.dishes.map(dish => ({
        ...dish,
        selected: false,
        selectedQuantity: 0
      }))

      this.setData({
        'order.dishes': dishes,
        refundAmount: this.data.order.pay_amount,
        refundAmountText: util.formatPrice(this.data.order.pay_amount),
        selectedDishes: [],
        selectedDishCount: 0,
        selectedDishQuantity: 0
      })
    } else {
      // 部分退款：默认不选，由用户自行选择退款份数
      const dishes = this.data.order.dishes.map(dish => ({
        ...dish,
        selected: false,
        selectedQuantity: 0
      }))
      this.setData({
        'order.dishes': dishes,
        refundAmount: 0,
        refundAmountText: '0.00',
        selectedDishes: [],
        selectedDishCount: 0,
        selectedDishQuantity: 0
      })
    }
  },

  // 调整部分退款数量
  onChangeDishQuantity(e) {
    if (this.data.refundType !== 'partial') return

    const index = Number(e.currentTarget.dataset.index)
    const action = e.currentTarget.dataset.action
    const dishes = this.data.order.dishes.map((dish, dishIndex) => {
      if (dishIndex !== index) return dish

      const currentQuantity = Number(dish.selectedQuantity) || 0
      const maxQuantity = Number(dish.maxRefundQuantity || dish.quantity || 0)
      let nextQuantity = currentQuantity

      if (action === 'increase') {
        nextQuantity = Math.min(maxQuantity, currentQuantity + 1)
      } else if (action === 'decrease') {
        nextQuantity = Math.max(0, currentQuantity - 1)
      }

      return {
        ...dish,
        selectedQuantity: nextQuantity,
        selected: nextQuantity > 0
      }
    })

    this.recalculatePartialRefund(dishes)
  },

  onDishQuantityInput(e) {
    if (this.data.refundType !== 'partial') return

    const index = Number(e.currentTarget.dataset.index)
    const value = e.detail.value
    const dishes = this.data.order.dishes.map((dish, dishIndex) => {
      if (dishIndex !== index) return dish

      const nextQuantity = this.clampDishRefundQuantity(value, dish.maxRefundQuantity || dish.quantity || 0)
      return {
        ...dish,
        selectedQuantity: nextQuantity,
        selected: nextQuantity > 0
      }
    })

    this.recalculatePartialRefund(dishes)
  },

  onDishQuantityBlur(e) {
    if (this.data.refundType !== 'partial') return

    const index = Number(e.currentTarget.dataset.index)
    const value = e.detail.value
    const dishes = this.data.order.dishes.map((dish, dishIndex) => {
      if (dishIndex !== index) return dish

      const nextQuantity = this.clampDishRefundQuantity(value, dish.maxRefundQuantity || dish.quantity || 0)
      return {
        ...dish,
        selectedQuantity: nextQuantity,
        selected: nextQuantity > 0,
        manualRefundAmountInput: nextQuantity > 0 ? dish.manualRefundAmountInput : '',
        isManualAmountEdited: nextQuantity > 0 ? dish.isManualAmountEdited : false
      }
    })

    this.recalculatePartialRefund(dishes)
  },

  onDishRefundAmountInput(e) {
    if (this.data.refundType !== 'partial') return

    const index = Number(e.currentTarget.dataset.index)
    const value = e.detail.value
    const dishes = this.data.order.dishes.map((dish, dishIndex) => {
      if (dishIndex !== index) return dish

      return {
        ...dish,
        manualRefundAmountInput: String(value ?? ''),
        isManualAmountEdited: true
      }
    })

    this.recalculatePartialRefund(dishes)
  },

  onDishRefundAmountBlur(e) {
    if (this.data.refundType !== 'partial') return

    const index = Number(e.currentTarget.dataset.index)
    const value = e.detail.value
    const dishes = this.data.order.dishes.map((dish, dishIndex) => {
      if (dishIndex !== index) return dish

      const maxDishRefundAmount = this.getDishMaxRefundAmount(dish)
      const nextAmount = this.roundPrice(Math.min(Math.max(this.parseRefundAmount(value), 0), maxDishRefundAmount))
      return {
        ...dish,
        manualRefundAmountInput: this.formatRefundInput(nextAmount),
        isManualAmountEdited: nextAmount > 0
      }
    })

    this.recalculatePartialRefund(dishes)
  },

  // 选择退款原因
  onReasonChange(e) {
    this.setData({ reasonCategory: e.currentTarget.dataset.value })
  },

  // 输入退款详情
  onReasonInput(e) {
    this.setData({ reasonDetail: e.detail.value })
  },

  // 提交退款申请
  async onSubmit() {
    const { orderId, refundType, selectedDishes, reasonCategory, reasonDetail, refundAmount } = this.data
    
    // 验证
    if (refundType === 'partial' && selectedDishes.length === 0) {
      wx.showToast({
        title: '请选择要退款的菜品',
        icon: 'none'
      })
      return
    }
    
    if (!reasonDetail || reasonDetail.trim() === '') {
      wx.showToast({
        title: '请填写退款原因',
        icon: 'none'
      })
      return
    }
    
    if (refundAmount <= 0) {
      wx.showToast({
        title: '退款金额错误',
        icon: 'none'
      })
      return
    }

    if (refundAmount > Number(this.data.order?.pay_amount || 0)) {
      wx.showToast({
        title: '退款金额不能超过实付金额',
        icon: 'none'
      })
      return
    }
    
    // 确认提交
    wx.showModal({
      title: '确认申请退款',
      content: `退款金额：¥${util.formatPrice(refundAmount)}\n\n提交后将由商家审核，请耐心等待`,
      confirmText: '确认提交',
      confirmColor: '#ff6b6b',
      success: async (res) => {
        if (!res.confirm) return
        
        try {
          this.setData({ submitting: true })
          wx.showLoading({ title: '提交中...', mask: true })
          
          // 构建请求数据
          const requestData = {
            order_id: orderId,
            reason: reasonDetail.trim(),
            reason_category: reasonCategory
          }
          
          // 部分退款需要传递菜品信息
          if (refundType === 'partial') {
            requestData.refund_items = selectedDishes.map(dish => ({
              dish_id: dish.dish_id,
              quantity: dish.refund_quantity
            }))
          }
          
          const result = await api.refund.create(requestData)
          
          wx.hideLoading()
          
          wx.showModal({
            title: '申请成功',
            content: `退款申请已提交\n退款金额：¥${util.formatPrice(result.refund_amount || refundAmount)}\n\n请等待商家审核`,
            showCancel: false,
            confirmText: '查看详情',
            success: () => {
              // 跳转到退款详情页
              wx.redirectTo({
                url: `/pages/refund/detail?id=${result.refund_id}`
              })
            }
          })
          
        } catch (error) {
          wx.hideLoading()
          console.error('提交退款申请失败:', error)
          
          wx.showModal({
            title: '提交失败',
            content: error.message,
            showCancel: false
          })
          
          this.setData({ submitting: false })
        }
      }
    })
  },

  // 返回
  onBack() {
    wx.navigateBack()
  }
})

