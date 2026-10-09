// pages/review/review.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    orderId: null,
    dishId: null,
    dish: null,
    // 默认不选中任何星，全部显示为空心（灰色），用户点击后再点亮
    rating: 0,
    content: '',
    images: [],
    isAnonymous: true,
    orderItems: [], // 订单中的所有菜品
    currentIndex: 0, // 当前评价的菜品索引
    showBatch: false, // 是否显示批量评价模式
    successOverlay: {
      show: false,
      title: '',
      desc: ''
    },
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    app.bindAdminAlertToPage(this)
    if (options.order_id) {
      this.setData({ orderId: parseInt(options.order_id) })
      
      // 如果指定了菜品ID，单个评价模式
      if (options.dish_id) {
        this.setData({ 
          dishId: parseInt(options.dish_id),
          showBatch: false
        })
        this.loadDish()
      } else {
        // 批量评价模式，加载订单所有菜品
        this.setData({ showBatch: true })
        this.loadOrderItems()
      }
    } else {
      wx.showToast({ title: '参数错误', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1200)
    }
  },

  // 加载订单菜品列表
  async loadOrderItems() {
    if (!this.data.orderId) return
    
    try {
      wx.showLoading({ title: '加载中...', mask: true })
      const res = await api.review.orderStatus(this.data.orderId)
      
      console.log('后端返回的数据:', res)
      
      // 后端返回的 items 中每个菜品包含 image 字段（完整URL）
      const rawItems = Array.isArray(res.items) ? res.items : []
      const items = rawItems.filter(item => !item.is_reviewed && !item.reviewed)
      
      if (rawItems.length > 0) {
        console.log('第一个菜品的数据:', rawItems[0])
      }
      
      if (items.length === 0) {
        wx.hideLoading()
        wx.showToast({ title: '没有可评价的菜品', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 1200)
        return
      }
      
      this.setData({ 
        orderItems: items,
        dishId: items[0].dish_id,
        dish: items[0] // 直接使用返回的菜品信息（包含 image 字段）
      })
      
      console.log('设置后的 dish 数据:', this.data.dish)
      
      wx.hideLoading()
      
      // 更新标题
      if (this.data.showBatch && items.length > 1) {
        wx.setNavigationBarTitle({
          title: `评价 (1/${items.length})`
        })
      }
    } catch (error) {
      wx.hideLoading()
      console.error('加载订单菜品失败:', error)
      wx.showToast({ title: error.message, icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1200)
    }
  },

  // 加载菜品信息
  async loadDish() {
    if (!this.data.dishId) return
    
    // 如果是批量评价模式，直接从 orderItems 中获取
    if (this.data.showBatch) {
      const { currentIndex, orderItems } = this.data
      const currentDish = orderItems[currentIndex]
      
      this.setData({ dish: currentDish })
      
      // 更新标题
      wx.setNavigationBarTitle({
        title: `评价 (${currentIndex + 1}/${orderItems.length})`
      })
      return
    }
    
    // 单个评价模式，需要加载菜品详情
    try {
      const res = await api.dish.detail(this.data.dishId)
      this.setData({ dish: res })
    } catch (error) {
      console.error('加载菜品失败:', error)
    }
  },

  // 获取评分对应文案
  getRatingCopy(rating) {
    const map = {
      1: '1 星 · 差评，和预期差距较大',
      2: '2 星 · 略有不足，还有提升空间',
      3: '3 星 · 一般，整体中规中矩',
      4: '4 星 · 满意，愿意再次下单',
      5: '5 星 · 超满意，值得推荐给朋友'
    }
    return map[rating] || '请点击星星完成评分'
  },

  // 显示提交成功反馈
  showSuccessFeedback(title, desc, callback) {
    this.setData({
      successOverlay: {
        show: true,
        title,
        desc
      }
    })

    setTimeout(() => {
      this.setData({
        successOverlay: {
          show: false,
          title: '',
          desc: ''
        }
      })
      if (typeof callback === 'function') {
        callback()
      }
    }, 1400)
  },

  // 选择评分
  onRatingTap(e) {
    const rating = e.currentTarget.dataset.rating
    this.setData({ rating })
  },

  // 选择评价身份
  onAnonymousChange(e) {
    const anonymous = String(e.currentTarget.dataset.anonymous) === 'true'
    this.setData({ isAnonymous: anonymous })
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

  // 输入评价内容
  onContentInput(e) {
    this.setData({ content: e.detail.value })
  },

  // 选择图片
  async onChooseImage() {
    try {
      const res = await new Promise((resolve, reject) => {
        wx.chooseImage({
          count: 3 - this.data.images.length,
          sizeType: ['compressed'],
          sourceType: ['album', 'camera'],
          success: resolve,
          fail: reject
        })
      })
      
      // 检查图片大小（5MB限制）
      const validImages = []
      const maxSize = 5 * 1024 * 1024 // 5MB
      
      for (let i = 0; i < res.tempFilePaths.length; i++) {
        const filePath = res.tempFilePaths[i]
        
        try {
          const fileInfo = await new Promise((resolve, reject) => {
            wx.getFileInfo({
              filePath: filePath,
              success: resolve,
              fail: reject
            })
          })
          
          if (fileInfo.size > maxSize) {
            wx.showToast({
              title: `图片${i + 1}超过5MB，已跳过`,
              icon: 'none',
              duration: 2000
            })
          } else {
            validImages.push(filePath)
          }
        } catch (error) {
          console.error('获取文件信息失败:', error)
          validImages.push(filePath) // 如果获取失败，仍然添加
        }
      }
      
      if (validImages.length > 0) {
        const newImages = [...this.data.images, ...validImages].slice(0, 3)
        this.setData({ images: newImages })
      }
    } catch (error) {
      console.error('选择图片失败:', error)
    }
  },

  // 删除图片
  onDeleteImage(e) {
    const index = e.currentTarget.dataset.index
    const images = [...this.data.images]
    images.splice(index, 1)
    this.setData({ images })
  },

  // 上传图片到服务器
  async uploadImages() {
    const { images } = this.data
    if (images.length === 0) return []

    const uploadedUrls = []
    
    for (let i = 0; i < images.length; i++) {
      try {
        wx.showLoading({ 
          title: `上传图片 ${i + 1}/${images.length}...`, 
          mask: true 
        })
        
        // 使用评价专用的上传接口
        const result = await api.media.uploadReview(images[i])
        
        console.log(`第 ${i + 1} 张图片上传结果:`, result)
        
        // 根据后端返回的数据结构获取图片URL
        // 后端返回格式: { urls: [...], paths: [...], count: 1, message: "..." }
        if (result.urls && result.urls.length > 0) {
          uploadedUrls.push(result.urls[0])
        } else if (result.url) {
          uploadedUrls.push(result.url)
        } else if (result.file_url) {
          uploadedUrls.push(result.file_url)
        } else if (result.path) {
          uploadedUrls.push(result.path)
        }
      } catch (error) {
        console.error(`上传第 ${i + 1} 张图片失败:`, error)
        
        wx.showToast({ 
          title: error.message, 
          icon: 'none',
          duration: 2000
        })
      }
    }
    
    return uploadedUrls
  },

  // 提交评价
  async onSubmit() {
    return util.withLock('review_submit', async () => {
      const { orderId, dishId, rating, content } = this.data

      if (!dishId) {
        wx.showToast({ title: '菜品信息错误', icon: 'none' })
        return
      }

      if (!orderId) {
        wx.showToast({ title: '订单信息错误', icon: 'none' })
        return
      }

      if (!rating || rating < 1 || rating > 5) {
        wx.showToast({ title: '请选择评分', icon: 'none' })
        return
      }

      try {
        // 先上传图片
        let uploadedImageUrls = []
        if (this.data.images.length > 0) {
          uploadedImageUrls = await this.uploadImages()
          if (uploadedImageUrls.length === 0 && this.data.images.length > 0) {
            wx.showModal({
              title: '提示',
              content: '图片上传失败，是否继续提交评价？',
              success: (res) => {
                if (res.confirm) {
                  this.submitReview(uploadedImageUrls)
                }
              }
            })
            return
          }
        }
        
        await this.submitReview(uploadedImageUrls)
      } catch (error) {
        wx.hideLoading()
        console.error('提交评价失败:', error)

        if (error && error.message === '该菜品已评价') {
          wx.showToast({ title: '该菜品已评价', icon: 'none' })
          setTimeout(() => {
            wx.navigateBack()
          }, 1200)
        }
      }
    }, 1500)
  },

  // 提交评价数据
  async submitReview(imageUrls = []) {
    const { orderId, dishId, rating, content, isAnonymous } = this.data
    
    wx.showLoading({ title: '提交中...', mask: true })

    // 构建请求数据
    const reviewData = {
      order_id: orderId,
      dish_id: dishId,
      rating: rating,
      is_anonymous: isAnonymous
    }
    
    // 只有内容不为空时才添加
    if (content && content.trim()) {
      reviewData.content = content.trim()
    }
    
    // 添加上传后的图片URL（转换为JSON字符串）
    if (imageUrls.length > 0) {
      reviewData.images = JSON.stringify(imageUrls)
    }
    
    console.log('提交的评价数据:', reviewData)
    console.log('图片URL数组:', imageUrls)

    await api.review.create(reviewData)

    wx.hideLoading()
    
    // 如果是批量评价模式，继续下一个
    if (this.data.showBatch) {
      const { currentIndex, orderItems } = this.data
      
      if (currentIndex < orderItems.length - 1) {
        // 还有未评价的菜品
        this.showSuccessFeedback(
          '这道菜已评价完成',
          '已保存你的真实感受，接下来继续评价下一道菜。',
          () => {
            const nextIndex = currentIndex + 1
            this.setData({
              currentIndex: nextIndex,
              dishId: orderItems[nextIndex].dish_id,
              dish: orderItems[nextIndex],
              rating: 0,
              content: '',
              images: [],
              isAnonymous: true
            })
            this.loadDish()
          }
        )
      } else {
        // 所有菜品已评价完成
        this.showSuccessFeedback(
          '全部评价完成',
          '感谢你的认真反馈，这些评价会帮助其他同学更快做选择。',
          () => {
            wx.navigateBack()
          }
        )
      }
    } else {
      // 单个评价模式
      this.showSuccessFeedback(
        '评价提交成功',
        '你的用餐反馈已经送达，感谢帮助大家避坑和种草。',
        () => {
          wx.navigateBack()
        }
      )
    }
  },

  // 跳过当前菜品
  onSkip() {
    if (!this.data.showBatch) return
    
    const { currentIndex, orderItems } = this.data
    
    if (currentIndex < orderItems.length - 1) {
      const nextIndex = currentIndex + 1
      this.setData({
        currentIndex: nextIndex,
        dishId: orderItems[nextIndex].dish_id,
        dish: orderItems[nextIndex],
        rating: 0,
        content: '',
        images: [],
        isAnonymous: true
      })
      this.loadDish()
    } else {
      wx.showToast({ title: '已是最后一个', icon: 'none' })
    }
  }
})
