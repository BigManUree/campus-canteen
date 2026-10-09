// pages/profile/edit.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    userInfo: null,
    nickname: '',
    phone: '',
    email: '',
    student_no: '',
    avatar: ''
  },

  onLoad() {
    this.loadUserInfo()
  },

  // 加载用户信息
  async loadUserInfo() {
    try {
      const res = await api.user.getInfo()
      
      this.setData({
        userInfo: res,
        nickname: res.nickname || '',
        phone: res.phone || '',
        email: res.email || '',
        student_no: res.student_no || '',
        avatar: util.formatImageUrl(res.avatar)
      })
    } catch (error) {
      console.error('加载用户信息失败:', error)
    }
  },

  // 输入昵称
  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value })
  },

  // 输入手机号
  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  // 输入邮箱
  onEmailInput(e) {
    this.setData({ email: e.detail.value })
  },

  // 输入学号
  onStudentNoInput(e) {
    this.setData({ student_no: e.detail.value })
  },

  // 选择头像
  async onChooseAvatar() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: async (res) => {
        const tempFilePath = res.tempFilePaths[0]
        try {
          wx.showLoading({ title: '上传中...', mask: true })
          const uploadRes = await api.media.uploadAvatar(tempFilePath)
          wx.hideLoading()
          
          console.log('上传成功，完整返回数据:', JSON.stringify(uploadRes, null, 2))
          
          // 使用 url 字段（包含 /uploads/ 前缀）
          let avatarUrl = uploadRes.url
          
          console.log('提取的原始 URL:', avatarUrl)
          
          if (!avatarUrl) {
            throw new Error('后端未返回图片 URL，返回数据: ' + JSON.stringify(uploadRes))
          }
          
          // 拼接完整 URL（url 字段已包含 /uploads/ 前缀，以 / 开头）
          const fullUrl = `http://localhost:8000${avatarUrl}`
          
          console.log('处理后的完整 URL:', fullUrl)
          
          this.setData({ avatar: fullUrl })
          wx.showToast({ title: '上传成功', icon: 'success' })
        } catch (error) {
          wx.hideLoading()
          console.error('上传头像失败:', error)
          wx.showToast({ 
            title: error.message, 
            icon: 'none' 
          })
        }
      }
    })
  },

  // 保存
  async onSave() {
    const { nickname, phone, email, student_no, avatar } = this.data

    // 验证手机号（如果填写了）
    if (phone && phone.trim() && !/^1[3-9]\d{9}$/.test(phone.trim())) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    // 验证邮箱（如果填写了）
    if (email && email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      wx.showToast({ title: '请输入正确的邮箱', icon: 'none' })
      return
    }

    try {
      wx.showLoading({ title: '保存中...', mask: true })
      
      const updateData = {}
      if (nickname && nickname.trim()) updateData.nickname = nickname.trim()
      if (phone && phone.trim()) updateData.phone = phone.trim()
      if (email && email.trim()) updateData.email = email.trim()
      if (student_no && student_no.trim()) updateData.student_no = student_no.trim()
      if (avatar) updateData.avatar = avatar

      // 至少要有一个字段更新
      if (Object.keys(updateData).length === 0) {
        wx.hideLoading()
        wx.showToast({ title: '没有修改任何信息', icon: 'none' })
        return
      }

      await api.user.updateInfo(updateData)
      
      // 更新全局用户信息
      const userInfo = await api.user.getInfo()
      app.login(userInfo, app.globalData.token)
      
      wx.hideLoading()
      wx.showToast({ title: '保存成功', icon: 'success' })
      
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (e) {
      wx.hideLoading()
      console.error('保存失败:', e)
      wx.showToast({ 
        title: e.message, 
        icon: 'none' 
      })
    }
  }
})
