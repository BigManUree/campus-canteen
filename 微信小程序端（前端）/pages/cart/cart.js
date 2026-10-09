// pages/cart/cart.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    // 购物车数据
    cartItems: [],
    validItems: [],      // 有效商品
    invalidItems: [],    // 失效商品
    recommendItems: [],  // 推荐商品
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    },
    
    // 加载状态
    loading: true,
    refreshing: false,
    
    // 管理模式
    isManage: false,
    
    // 选择状态
    selectedAll: false,
    selectedCount: 0,
    
    // 价格信息
    totalPrice: '0.00',
    originalPrice: 0,
    discountAmount: '0.00'
  },

  /**
   * 生命周期函数--监听页面加载
   */
  onLoad() {
    // 检查登录状态
    if (!app.globalData.isLogin) {
      util.checkLogin()
      return
    }
    
    this.loadCart()
    this.loadRecommend()
  },

  /**
   * 生命周期函数--监听页面显示
   */
  onShow() {
    app.bindAdminAlertToPage(this)
    if (app.globalData.isLogin) {
      this.loadCart()
    }
  },

  /**
   * 下拉刷新
   */
  onRefresh() {
    this.setData({ refreshing: true })
    Promise.all([
      this.loadCart(),
      this.loadRecommend()
    ]).finally(() => {
      this.setData({ refreshing: false })
    })
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

  /**
   * 加载购物车
   */
  async loadCart() {
    try {
      this.setData({ loading: true })
      
      const res = await api.cart.list()
      const list = Array.isArray(res) ? res : (res?.items || res?.data || [])
      
      console.log('购物车原始数据:', JSON.stringify(list, null, 2))
      
      // 处理购物车数据，并补充档口信息
      const cartItems = await Promise.all(list.map(item => this.processCartItemWithCanteen(item)))
      
      console.log('处理后的购物车数据:', cartItems)
      
      // 分离有效和失效商品
      let validItems = cartItems.filter(item => this.isValidItem(item))
      const invalidItems = cartItems.filter(item => !this.isValidItem(item))
      validItems = this.restoreSelection(validItems)
      const selectedAll = validItems.length > 0 && validItems.every(item => item.selected)
      const selectedCount = validItems.filter(item => item.selected).length
      
      this.setData({
        cartItems,
        validItems,
        invalidItems,
        selectedAll,
        selectedCount,
        loading: false
      })
      
      // 计算总价
      this.calculateTotal()
      
    } catch (error) {
      console.error('加载购物车失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
      this.setData({ loading: false })
    }
  },

  /**
   * 处理购物车商品数据并补充档口信息
   */
  async processCartItemWithCanteen(item) {
    const processedItem = this.processCartItem(item)
    
    // 如果已经有档口ID，直接返回
    if (processedItem.canteen_id) {
      return processedItem
    }
    
    // 如果没有档口ID，尝试从菜品详情获取
    try {
      const dishDetail = await api.dish.detail(processedItem.dish_id)
      const canteenId = dishDetail.canteen_id
      
      if (canteenId) {
        processedItem.canteen_id = canteenId
        processedItem.dish.canteen_id = canteenId
      }
      
      console.log(`菜品 ${processedItem.dish_name} 的档口ID:`, canteenId)
    } catch (error) {
      console.error(`获取菜品 ${processedItem.dish_id} 的档口信息失败:`, error)
    }
    
    return processedItem
  },

  /**
   * 处理购物车商品数据
   */
  processCartItem(item) {
    const dish = item.dish || {}
    const price = Number(item.price) || Number(dish.price) || 0
    const originalPrice = Number(dish.original_price) || price
    
    // 处理商品图片
    const coverUrl = this.getDishCoverUrl(dish)
    
    // 处理商品标签
    let tags = []
    if (dish.is_new) tags.push('新品')
    if (dish.is_hot) tags.push('热销')
    if (dish.is_recommend) tags.push('推荐')
    
    // 获取商品状态和库存
    const dishStatus = dish.status !== undefined ? dish.status : 1
    const stock = dish.stock !== undefined ? dish.stock : 999
    
    // 获取档口ID（优先从dish对象，其次从item）
    const canteenId = dish.canteen_id || item.canteen_id
    
    return {
      ...item,
      item_id: item.item_id || item.cart_id || item.id,
      dish_id: dish.dish_id || dish.id || item.dish_id,
      dish_name: item.dish_name || dish.name || '未知商品',
      dish_desc: dish.description || dish.desc || '',
      dish_price: price,
      dish_price_text: util.formatPrice(price),
      original_price: originalPrice,
      original_price_text: util.formatPrice(originalPrice),
      cover_url: coverUrl,
      quantity: item.quantity || 1,
      selected: item.selected || false,
      tags: tags,
      // 商品状态（确保有值）
      dish_status: dishStatus,
      stock: stock,
      // 保留原始dish对象，并确保包含canteen_id
      dish: {
        ...dish,
        canteen_id: canteenId
      },
      // 同时在顶层也保存canteen_id，方便访问
      canteen_id: canteenId
    }
  },

  /**
   * 获取商品封面图
   */
  getDishCoverUrl(dish) {
    const fallback = '/static/default-dish.png'
    if (!dish) {
      console.log('getDishCoverUrl: dish为空')
      return fallback
    }
    
    const raw = dish.images || dish.image
    console.log('getDishCoverUrl - 原始图片数据:', raw, '类型:', typeof raw)
    
    if (!raw) {
      console.log('getDishCoverUrl: raw为空')
      return fallback
    }
    
    try {
      // 如果是数组，取第一张
      if (Array.isArray(raw)) {
        console.log('getDishCoverUrl: 数组格式，第一张:', raw[0])
        if (raw.length > 0 && raw[0]) {
          const url = util.formatImageUrl(raw[0])
          console.log('getDishCoverUrl: 处理后URL:', url)
          return url
        }
        return fallback
      }
      
      // 如果是字符串
      if (typeof raw === 'string') {
        const s = raw.trim()
        if (!s) return fallback
        
        // 尝试解析JSON数组
        if (s.startsWith('[')) {
          console.log('getDishCoverUrl: JSON字符串格式')
          const arr = JSON.parse(s)
          console.log('getDishCoverUrl: 解析后数组:', arr)
          if (Array.isArray(arr) && arr.length > 0 && arr[0]) {
            const url = util.formatImageUrl(arr[0])
            console.log('getDishCoverUrl: 处理后URL:', url)
            return url
          }
          return fallback
        }
        
        // 直接是图片路径
        console.log('getDishCoverUrl: 直接字符串路径')
        const url = util.formatImageUrl(s)
        console.log('getDishCoverUrl: 处理后URL:', url)
        return url
      }
    } catch (e) {
      console.error('getDishCoverUrl 解析图片失败:', e, 'raw:', raw)
    }
    
    return fallback
  },

  /**
   * 判断商品是否有效
   */
  isValidItem(item) {
    // 商品状态为1表示正常，如果没有状态信息则默认为有效
    const status = item.dish_status !== undefined ? item.dish_status : 1
    if (status !== 1) {
      console.log('商品失效 - 状态异常:', item.dish_name, 'status:', status)
      return false
    }
    
    // 库存充足（如果没有库存信息则默认为有效）
    const stock = item.stock !== undefined ? item.stock : 999
    if (stock <= 0) {
      console.log('商品失效 - 库存不足:', item.dish_name, 'stock:', stock)
      return false
    }
    
    return true
  },

  // 恢复选中状态
  restoreSelection(validItems) {
    const selectedIds = app.globalData.cartSelectedItemIds || []
    const selectedIdSet = new Set(selectedIds)

    return validItems.map(item => ({
      ...item,
      selected: selectedIdSet.has(item.item_id)
    }))
  },

  // 持久化当前选中状态
  persistSelection(validItems = this.data.validItems) {
    const selectedIds = validItems
      .filter(item => item.selected)
      .map(item => item.item_id)

    app.globalData.cartSelectedItemIds = selectedIds
  },

  /**
   * 加载推荐商品
   */
  async loadRecommend() {
    try {
      // 这里可以调用推荐商品API
      // const res = await api.dish.recommend({ limit: 10 })
      
      // 模拟推荐数据
      const recommendItems = []
      
      this.setData({ recommendItems })
      
    } catch (error) {
      console.error('加载推荐商品失败:', error)
    }
  },

  onToggleManage() {
    const isManage = !this.data.isManage
    this.setData({ isManage })
    
    // 退出管理模式时取消所有选择
    if (!isManage) {
      this.clearSelection()
    }
  },

  /**
   * 选择商品
   */
  onSelectItem(e) {
    const id = e.currentTarget.dataset.id
    const { validItems } = this.data
    
    const index = validItems.findIndex(item => item.item_id === id)
    if (index === -1) return
    
    validItems[index].selected = !validItems[index].selected
    
    this.setData({ validItems })
    this.persistSelection(validItems)
    this.updateSelection()
  },

  /**
   * 全选/取消全选
   */
  onSelectAll() {
    const { selectedAll, validItems } = this.data
    const newSelectedAll = !selectedAll
    
    validItems.forEach(item => {
      item.selected = newSelectedAll
    })
    
    this.setData({ 
      validItems,
      selectedAll: newSelectedAll
    })
    this.persistSelection(validItems)
    this.updateSelection()
  },

  /**
   * 更新选择状态
   */
  updateSelection() {
    const { validItems } = this.data
    const selectedItems = validItems.filter(item => item.selected)
    const selectedAll = validItems.length > 0 && selectedItems.length === validItems.length
    
    this.setData({
      selectedCount: selectedItems.length,
      selectedAll
    })
    
    this.persistSelection(validItems)
    this.calculateTotal()
  },

  /**
   * 清空选择
   */
  clearSelection() {
    const { validItems } = this.data
    validItems.forEach(item => {
      item.selected = false
    })
    
    this.setData({
      validItems,
      selectedAll: false,
      selectedCount: 0
    })
    app.globalData.cartSelectedItemIds = []
    this.calculateTotal()
  },

  /**
   * 计算总价
   */
  calculateTotal() {
    const { validItems } = this.data
    const selectedItems = validItems.filter(item => item.selected)
    
    if (selectedItems.length === 0) {
      this.setData({
        totalPrice: '0.00',
        originalPrice: 0,
        discountAmount: '0.00'
      })
      return
    }
    
    let total = 0
    let original = 0
    
    selectedItems.forEach(item => {
      const price = Number(item.dish_price) || 0
      const originalPrice = Number(item.original_price) || price
      const quantity = Number(item.quantity) || 0
      
      total += price * quantity
      original += originalPrice * quantity
    })
    
    const discount = original - total
    
    this.setData({
      totalPrice: util.formatPrice(total),
      originalPrice: original,
      discountAmount: util.formatPrice(discount)
    })
  },

  /**
   * 减少数量
   */
  async onDecreaseQuantity(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.validItems.find(item => item.item_id === id)
    
    if (!item) return
    
    const newQuantity = item.quantity - 1
    
    if (newQuantity <= 0) {
      this.onDeleteItem(e)
      return
    }
    
    await this.updateQuantity(id, newQuantity)
  },

  /**
   * 增加数量
   */
  async onIncreaseQuantity(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.validItems.find(item => item.item_id === id)
    
    if (!item) return
    
    const newQuantity = item.quantity + 1
    
    // 检查库存
    if (newQuantity > item.stock) {
      wx.showToast({
        title: `库存不足，仅剩${item.stock}件`,
        icon: 'none'
      })
      return
    }
    
    // 限制最大数量
    if (newQuantity > 99) {
      wx.showToast({
        title: '数量不能超过99',
        icon: 'none'
      })
      return
    }
    
    await this.updateQuantity(id, newQuantity)
  },

  /**
   * 数量输入
   */
  onQuantityInput(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.validItems.find(item => item.item_id === id)
    
    if (!item) return
    
    wx.showModal({
      title: '修改数量',
      editable: true,
      placeholderText: '请输入数量',
      content: String(item.quantity),
      success: async (res) => {
        if (res.confirm) {
          const newQuantity = parseInt(res.content)
          
          if (isNaN(newQuantity) || newQuantity <= 0) {
            wx.showToast({
              title: '请输入有效数量',
              icon: 'none'
            })
            return
          }
          
          if (newQuantity > item.stock) {
            wx.showToast({
              title: `库存不足，仅剩${item.stock}件`,
              icon: 'none'
            })
            return
          }
          
          if (newQuantity > 99) {
            wx.showToast({
              title: '数量不能超过99',
              icon: 'none'
            })
            return
          }
          
          await this.updateQuantity(id, newQuantity)
        }
      }
    })
  },

  /**
   * 更新数量
   */
  async updateQuantity(id, quantity) {
    try {
      await api.cart.update(id, { quantity })
      
      // 更新本地数据
      const { validItems } = this.data
      const index = validItems.findIndex(item => item.item_id === id)
      
      if (index !== -1) {
        validItems[index].quantity = quantity
        this.setData({ validItems })
        this.calculateTotal()
      }
      
    } catch (error) {
      console.error('更新数量失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
      // 失败后重新加载
      this.loadCart()
    }
  },

  /**
   * 删除商品
   */
  onDeleteItem(e) {
    const id = e.currentTarget.dataset.id
    
    wx.showModal({
      title: '删除商品',
      content: '确定要删除这个商品吗？',
      confirmColor: '#ff6b6b',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.cart.remove(id)
            wx.showToast({
              title: '已删除',
              icon: 'success'
            })
            this.loadCart()
          } catch (error) {
            console.error('删除失败:', error)
            wx.showToast({
              title: error.message,
              icon: 'none'
            })
          }
        }
      }
    })
  },

  /**
   * 批量删除
   */
  onBatchDelete() {
    const { validItems, selectedCount } = this.data
    
    if (selectedCount === 0) {
      wx.showToast({
        title: '请先选择商品',
        icon: 'none'
      })
      return
    }
    
    wx.showModal({
      title: '批量删除',
      content: `确定要删除选中的${selectedCount}个商品吗？`,
      confirmColor: '#ff6b6b',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '删除中...', mask: true })
            
            const selectedItems = validItems.filter(item => item.selected)
            const deletePromises = selectedItems.map(item => 
              api.cart.remove(item.item_id)
            )
            
            await Promise.all(deletePromises)
            
            wx.hideLoading()
            wx.showToast({
              title: '删除成功',
              icon: 'success'
            })
            
            this.setData({ isManage: false })
            this.loadCart()
            
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

  /**
   * 清空失效商品
   */
  onClearInvalid() {
    const { invalidItems } = this.data
    
    if (invalidItems.length === 0) return
    
    wx.showModal({
      title: '清空失效商品',
      content: `确定要清空${invalidItems.length}个失效商品吗？`,
      confirmColor: '#ff6b6b',
      success: async (res) => {
        if (res.confirm) {
          try {
            wx.showLoading({ title: '清空中...', mask: true })
            
            const deletePromises = invalidItems.map(item => 
              api.cart.remove(item.item_id)
            )
            
            await Promise.all(deletePromises)
            
            wx.hideLoading()
            wx.showToast({
              title: '清空成功',
              icon: 'success'
            })
            
            this.loadCart()
            
          } catch (error) {
            wx.hideLoading()
            console.error('清空失效商品失败:', error)
            wx.showToast({
              title: error.message,
              icon: 'none'
            })
          }
        }
      }
    })
  },

  /**
   * 查看商品详情
   */
  onItemDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  /**
   * 查看推荐商品详情
   */
  onRecommendDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  /**
   * 添加推荐商品
   */
  async onAddRecommend(e) {
    const id = e.currentTarget.dataset.id
    
    try {
      await api.cart.add({
        dish_id: id,
        quantity: 1
      })
      
      wx.showToast({
        title: '已添加到购物车',
        icon: 'success'
      })
      
      this.loadCart()
      
    } catch (error) {
      console.error('添加失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  /**
   * 去结算
   */
  async onCheckout() {
    const { validItems, selectedCount } = this.data
    
    if (selectedCount === 0) {
      wx.showToast({
        title: '请先选择商品',
        icon: 'none'
      })
      return
    }
    
    const selectedItems = validItems.filter(item => item.selected)
    
    // 检查是否同一档口（优先从顶层获取canteen_id，其次从dish对象）
    const canteenIds = [...new Set(selectedItems.map(item => 
      item.canteen_id || item.dish?.canteen_id
    ).filter(Boolean))]
    
    console.log('选中的商品:', selectedItems)
    console.log('档口ID列表:', canteenIds)
    
    if (canteenIds.length === 0) {
      wx.showToast({
        title: '商品信息异常，缺少档口信息',
        icon: 'none',
        duration: 2000
      })
      return
    }
    
    if (canteenIds.length > 1) {
      wx.showModal({
        title: '提示',
        content: '购物车中有不同档口的商品，请分开结算',
        showCancel: false
      })
      return
    }
    
    // 将选中的商品ID保存到全局数据，供确认订单页使用
    try {
      const app = getApp()
      const canteenId = canteenIds[0]
      
      app.globalData.checkoutItems = selectedItems.map(item => ({
        item_id: item.item_id,
        dish_id: item.dish_id,
        dish_name: item.dish_name,
        cover_url: item.cover_url,
        price: item.dish_price,
        quantity: item.quantity,
        canteen_id: canteenId,
        tags: item.tags || []
      }))
      
      console.log('准备结算的数据:', app.globalData.checkoutItems)
      
      // 跳转到确认订单页
      wx.navigateTo({
        url: `/pages/order/confirm?from=cart&canteen_id=${canteenId}`
      })
    } catch (error) {
      console.error('准备结算数据失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
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
