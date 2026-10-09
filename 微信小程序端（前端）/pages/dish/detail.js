// pages/dish/detail.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    dishId: null,
    dish: null,
    canteen: null,
    images: [],
    currentImageIndex: 0,
    mediaUrl: '',
    mediaType: '',
    tags: [],
    reviews: [],
    reviewCount: 0,
    ratingDistribution: [],
    recommendDishes: [],
    isFavorite: false,
    quantity: 1,
    loading: true,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ dishId: options.id })
      this.loadData()
    } else {
      wx.showToast({ 
        title: '未获取到菜品信息', 
        icon: 'none' 
      })
      setTimeout(() => wx.navigateBack(), 1200)
    }
  },

  onShow() {
    app.bindAdminAlertToPage(this)
    if (!this.data.dishId) return
    // 每次显示页面时刷新菜品数据（包括最新销量）
    this.loadDish()
    this.checkFavorite()
  },

  onShareAppMessage() {
    const { dish } = this.data
    return {
      title: dish ? `${dish.name} - 美味推荐` : '菜品详情',
      path: `/pages/dish/detail?id=${this.data.dishId}`,
      imageUrl: this.data.images[0] || ''
    }
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

  // 加载数据
  async loadData() {
    if (!this.data.dishId) return
    
    try {
      this.setData({ loading: true })
      
      // 并发加载数据
      const [dishRes] = await Promise.all([
        this.loadDish(),
        this.loadReviews(),
        this.checkFavorite()
      ])

      // 加载食堂信息
      if (dishRes && dishRes.canteen_id) {
        this.loadCanteen(dishRes.canteen_id)
      }

      // 加载推荐菜品
      this.loadRecommendDishes()

      this.setData({ loading: false })
    } catch (error) {
      console.error('加载数据失败:', error)
      this.setData({ loading: false })
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 加载菜品详情
  async loadDish() {
    if (!this.data.dishId) return null
    
    try {
      const res = await api.dish.detail(this.data.dishId)
      
  // 处理图片
      let images = []
      const sourceImages = Array.isArray(res.image_urls) && res.image_urls.length
        ? res.image_urls
        : res.images

      if (sourceImages) {
        if (Array.isArray(sourceImages)) {
          images = sourceImages.map(img => util.formatImageUrl(img))
        } else if (typeof sourceImages === 'string') {
          try {
            const parsed = JSON.parse(sourceImages)
            images = parsed.map(img => util.formatImageUrl(img))
          } catch (e) {
            images = [util.formatImageUrl(sourceImages)]
          }
        }
      }
      
      // 如果没有图片，使用默认图片
      if (images.length === 0) {
        images = ['/static/default-dish.png']
      }

      // 处理标签
      let tags = []
      if (res.tags) {
        if (Array.isArray(res.tags)) {
          tags = res.tags
        } else if (typeof res.tags === 'string') {
          try {
            tags = JSON.parse(res.tags)
          } catch (e) {
            tags = res.tags.split(',').map(t => t.trim()).filter(t => t)
          }
        }
      }

      // 处理媒体
      const mediaUrl = res.media_path || ''
      const mediaType = res.media_type || ''

      // 判断是否为热销、新品、推荐（使用后端返回的数据）
      const is_hot = res.is_hot || false
      const is_new = res.is_new || false
      const is_recommend = res.is_recommend || false

      this.setData({
        dish: {
          ...res,
          is_hot,
          is_new,
          is_recommend,
          rating: res.rating || 0,
          sales: res.sales || 0,
          like_count: res.like_count || 0,
          window_name: res.window_name || '',
          window_label: res.window_name ? `窗口 ${res.window_name}` : (res.window_id ? `窗口 #${res.window_id}` : '窗口信息待完善')
        },
        images,
        tags,
        mediaUrl,
        mediaType
      })

      // 记录浏览历史
      if (app.globalData.isLogin) {
        try {
          await api.history.add(res.dish_id)
        } catch (e) {
          console.error('记录浏览历史失败:', e)
        }
      }

      return res
    } catch (error) {
      console.error('加载菜品失败:', error)
      throw error
    }
  },

  // 加载食堂信息
  async loadCanteen(canteenId) {
    try {
      const res = await api.canteen.detail(canteenId)
      this.setData({ canteen: res })
    } catch (error) {
      console.error('加载食堂信息失败:', error)
    }
  },

  // 加载评价
  async loadReviews() {
    if (!this.data.dishId) return
    
    try {
      const res = await api.review.list(this.data.dishId)
      const list = Array.isArray(res) ? res : (res && res.items) ? res.items : []
      
      // 处理评价数据
      const reviews = list.slice(0, 3).map(r => this.normalizeReview(r))

      // 计算评分分布
      const ratingDistribution = this.calculateRatingDistribution(list)

      this.setData({ 
        reviews,
        reviewCount: list.length,
        ratingDistribution
      })
    } catch (error) {
      console.error('加载评价失败:', error)
    }
  },

  normalizeReview(review = {}) {
    const isAnonymous = review.is_anonymous === true || review.is_anonymous === 1
    return {
      ...review,
      is_anonymous: isAnonymous,
      user_name: this.getReviewDisplayName(review, isAnonymous),
      user_avatar: this.getReviewAvatar(review, isAnonymous),
      create_time_text: util.formatDate(review.create_time, 'YYYY-MM-DD HH:mm'),
      rating: review.rating || 5,
      images: this.parseReviewImages(review.images),
      reply_content: this.getReviewReplyContent(review),
      reply_time_text: this.getReviewReplyTime(review)
    }
  },

  getReviewDisplayName(review = {}, isAnonymous = null) {
    const hidden = isAnonymous === null
      ? (review.is_anonymous === true || review.is_anonymous === 1)
      : isAnonymous
    if (hidden) {
      return '匿名用户'
    }
    return review.user?.nickname || '实名用户'
  },

  getReviewAvatar(review = {}, isAnonymous = null) {
    const hidden = isAnonymous === null
      ? (review.is_anonymous === true || review.is_anonymous === 1)
      : isAnonymous
    if (hidden) {
      return '/static/default-avatar.png'
    }
    return review.user?.avatar || '/static/default-avatar.png'
  },

  getReviewReplyContent(review = {}) {
    return review.reply_content || ''
  },

  getReviewReplyTime(review = {}) {
    return review.reply_time ? util.formatDate(review.reply_time, 'YYYY-MM-DD HH:mm') : ''
  },

  // 解析评价图片
  parseReviewImages(images) {
    if (!images) return []
    if (Array.isArray(images)) return images
    if (typeof images === 'string') {
      try {
        return JSON.parse(images)
      } catch (e) {
        return images.split(',').map(img => img.trim()).filter(img => img)
      }
    }
    return []
  },

  // 计算评分分布
  calculateRatingDistribution(reviews) {
    const distribution = [
      { star: 5, count: 0, percent: 0 },
      { star: 4, count: 0, percent: 0 },
      { star: 3, count: 0, percent: 0 },
      { star: 2, count: 0, percent: 0 },
      { star: 1, count: 0, percent: 0 }
    ]

    reviews.forEach(review => {
      const rating = review.rating || 5
      const index = 5 - rating
      if (index >= 0 && index < 5) {
        distribution[index].count++
      }
    })

    const total = reviews.length || 1
    distribution.forEach(item => {
      item.percent = Math.round((item.count / total) * 100)
    })

    return distribution
  },

  // 加载推荐菜品
  async loadRecommendDishes() {
    try {
      const res = await api.dish.list({ 
        canteen_id: this.data.dish?.canteen_id,
        limit: 10
      })
      
      const rawList = Array.isArray(res) ? res : (res && res.items) ? res.items : []
      
      // 过滤掉当前菜品，随机选择5个
      const filtered = rawList
        .filter(d => d.dish_id !== this.data.dishId)
        .slice(0, 5)
        .map(d => this.processRecommendDish(d))

      this.setData({ recommendDishes: filtered })
    } catch (error) {
      console.error('加载推荐菜品失败:', error)
    }
  },

  // 处理推荐菜品数据
  processRecommendDish(dish) {
    let cover_url = '/static/default-dish.png'
    const images = dish && dish.images
    
    if (images) {
      if (Array.isArray(images)) {
        const url = images[0] || cover_url
        cover_url = util.formatImageUrl(url)
      } else if (typeof images === 'string') {
        const s = images.trim()
        if (s) {
          if (s.startsWith('[')) {
            try {
              const arr = JSON.parse(s)
              if (Array.isArray(arr) && arr.length > 0) {
                const url = arr[0] || cover_url
                cover_url = util.formatImageUrl(url)
              }
            } catch (e) {
              cover_url = util.formatImageUrl(s)
            }
          } else {
            cover_url = util.formatImageUrl(s)
          }
        }
      }
    }

    return {
      ...dish,
      cover_url,
      sales: dish.sales || 0
    }
  },

  // 检查收藏状态
  async checkFavorite() {
    if (!app.globalData.isLogin || !this.data.dishId) return
    
    try {
      const res = await api.favorite.check(this.data.dishId)
      this.setData({
        isFavorite: res.is_favorite || false
      })
    } catch (error) {
      console.error('检查收藏状态失败:', error)
    }
  },

  // 切换收藏
  async onToggleFavorite() {
    if (!util.checkLogin()) return

    try {
      if (this.data.isFavorite) {
        await api.favorite.remove(this.data.dishId)
        this.setData({ isFavorite: false })
        wx.showToast({
          title: '已取消收藏',
          icon: 'success'
        })
      } else {
        await api.favorite.add(this.data.dishId)
        this.setData({ isFavorite: true })
        wx.showToast({
          title: '收藏成功',
          icon: 'success'
        })
      }
    } catch (error) {
      console.error('收藏操作失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 轮播图切换
  onSwiperChange(e) {
    this.setData({
      currentImageIndex: e.detail.current
    })
  },

  // 预览图片
  onPreviewImage(e) {
    const index = e.currentTarget.dataset.index
    wx.previewImage({
      urls: this.data.images,
      current: this.data.images[index]
    })
  },

  // 预览评价图片
  onPreviewReviewImage(e) {
    const images = e.currentTarget.dataset.images
    const index = e.currentTarget.dataset.index
    wx.previewImage({
      urls: images,
      current: images[index]
    })
  },

  // 播放媒体
  onPlayMedia() {
    if (this.data.mediaUrl) {
      wx.navigateTo({
        url: `/pages/media/media?url=${encodeURIComponent(this.data.mediaUrl)}&type=${this.data.mediaType}`
      })
    }
  },

  // 查看档口
  onViewCanteen() {
    if (this.data.canteen) {
      wx.navigateTo({
        url: `/pages/canteen/detail?id=${this.data.canteen.canteen_id}`
      })
    }
  },

  // 查看全部评价
  onViewAllReviews() {
    wx.navigateTo({
      url: `/pages/review/list?dish_id=${this.data.dishId}&dish_name=${encodeURIComponent(this.data.dish.name)}`
    })
  },

  // 推荐菜品点击
  onRecommendTap(e) {
    const id = e.currentTarget.dataset.id
    wx.redirectTo({
      url: `/pages/dish/detail?id=${id}`
    })
  },

  // 数量减少
  onQuantityMinus() {
    if (this.data.quantity > 1) {
      this.setData({
        quantity: this.data.quantity - 1
      })
    }
  },

  // 数量增加
  onQuantityPlus() {
    if (this.data.quantity < this.data.dish.stock) {
      this.setData({
        quantity: this.data.quantity + 1
      })
    } else {
      wx.showToast({
        title: '库存不足',
        icon: 'none'
      })
    }
  },

  // 数量输入
  onQuantityInput(e) {
    let value = parseInt(e.detail.value) || 1
    if (value < 1) value = 1
    if (value > this.data.dish.stock) {
      value = this.data.dish.stock
      wx.showToast({
        title: '库存不足',
        icon: 'none'
      })
    }
    this.setData({ quantity: value })
  },

  // 添加到购物车
  async onAddToCart() {
    if (!util.checkLogin()) return

    const { dish, quantity } = this.data
    
    // 检查菜品状态
    if (!dish) {
      wx.showToast({ 
        title: '菜品信息错误', 
        icon: 'none' 
      })
      return
    }

    if (dish.status !== 1) {
      wx.showToast({ 
        title: '菜品已下架', 
        icon: 'none' 
      })
      return
    }

    if (dish.stock < quantity) {
      wx.showToast({ 
        title: '库存不足', 
        icon: 'none' 
      })
      return
    }

    try {
      wx.showLoading({ 
        title: '添加中...', 
        mask: true 
      })

      // 调用 API 添加到购物车
      await api.cart.add({
        dish_id: dish.dish_id,
        quantity: quantity
      })

      wx.hideLoading()
      wx.showToast({ 
        title: '已加入购物车', 
        icon: 'success' 
      })

      // 重置数量
      this.setData({ quantity: 1 })
    } catch (error) {
      wx.hideLoading()
      console.error('添加到购物车失败:', error)
      wx.showToast({
        title: error.message,
        icon: 'none'
      })
    }
  },

  // 立即购买
  onBuyNow() {
    if (!util.checkLogin()) return

    const { dish, quantity } = this.data
    
    if (!dish || dish.status !== 1) {
      wx.showToast({ 
        title: '菜品已下架', 
        icon: 'none' 
      })
      return
    }

    if (dish.stock < quantity) {
      wx.showToast({ 
        title: '库存不足', 
        icon: 'none' 
      })
      return
    }

    wx.navigateTo({
      url: `/pages/order/confirm?dish_id=${dish.dish_id}&quantity=${quantity}&canteen_id=${dish.canteen_id}`
    })
  },

  // 分享
  onShare() {
    const { dish, images } = this.data
    
    wx.showActionSheet({
      itemList: ['分享给好友', '生成分享海报', '复制链接'],
      success: (res) => {
        if (res.tapIndex === 0) {
          // 分享给好友
          wx.showModal({
            title: '分享提示',
            content: '请点击右上角"..."按钮，选择"转发"分享给好友',
            showCancel: false,
            confirmText: '知道了'
          })
        } else if (res.tapIndex === 1) {
          // 生成分享海报
          wx.showToast({
            title: '海报生成功能开发中',
            icon: 'none'
          })
        } else if (res.tapIndex === 2) {
          // 复制链接
          wx.setClipboardData({
            data: `pages/dish/detail?id=${this.data.dishId}`,
            success: () => {
              wx.showToast({
                title: '链接已复制',
                icon: 'success'
              })
            }
          })
        }
      }
    })
  },

  // 返回
  onBack() {
    wx.navigateBack()
  }
})
