// pages/auth/register.js
const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    username: '',
    password: '',
    confirmPassword: '',
    phone: '',
    nickname: '',
    showPassword: false,
    showConfirmPassword: false
  },

  // 输入处理
  onUsernameInput(e) {
    this.setData({ username: e.detail.value })
  },

  onPasswordInput(e) {
    this.setData({ password: e.detail.value })
  },

  onConfirmPasswordInput(e) {
    this.setData({ confirmPassword: e.detail.value })
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value })
  },

  togglePassword() {
    this.setData({ showPassword: !this.data.showPassword })
  },

  toggleConfirmPassword() {
    this.setData({ showConfirmPassword: !this.data.showConfirmPassword })
  },

  // 注册
  async onRegister() {
    const { username, password, confirmPassword, phone, nickname } = this.data

    // 验证用户名
    if (!username || !username.trim()) {
      wx.showToast({ title: '请输入用户名', icon: 'none' })
      return
    }

    if (username.trim().length < 3) {
      wx.showToast({ title: '用户名至少3个字符', icon: 'none' })
      return
    }

    if (username.trim().length > 20) {
      wx.showToast({ title: '用户名不能超过20个字符', icon: 'none' })
      return
    }

    // 验证密码
    if (!password) {
      wx.showToast({ title: '请输入密码', icon: 'none' })
      return
    }

    if (password.length < 6) {
      wx.showToast({ title: '密码长度至少6位', icon: 'none' })
      return
    }

    if (password.length > 20) {
      wx.showToast({ title: '密码不能超过20位', icon: 'none' })
      return
    }

    // 验证确认密码
    if (!confirmPassword) {
      wx.showToast({ title: '请输入确认密码', icon: 'none' })
      return
    }

    if (password !== confirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    // 验证手机号（可选）
    if (phone && phone.trim() && !/^1[3-9]\d{9}$/.test(phone.trim())) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    try {
      wx.showLoading({ title: '注册中...', mask: true })

      const registerData = {
        username: username.trim(),
        password: password
      }

      if (phone && phone.trim()) {
        registerData.phone = phone.trim()
      }

      if (nickname && nickname.trim()) {
        registerData.nickname = nickname.trim()
      }

      const res = await api.auth.register(registerData)

      // 保存登录信息
      app.login(res.userInfo, res.token)

      wx.hideLoading()
      wx.showToast({ title: '注册成功', icon: 'success' })

      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } catch (e) {
      wx.hideLoading()
      console.error('注册失败:', e)
      wx.showToast({ title: e.message, icon: 'none' })
    }
  },

  // 跳转登录
  onLogin() {
    wx.navigateBack()
  }
})

