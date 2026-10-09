// pages/auth/login.js
const api = require('../../utils/api.js')
const app = getApp()

Page({
  data: {
    username: '',
    password: '',
    showPassword: false,
    rememberPassword: false
  },

  onLoad(options) {
    // 如果已登录，跳转到首页
    if (app.globalData.isLogin) {
      wx.switchTab({
        url: '/pages/index/index'
      })
      return
    }

    // 读取保存的账号密码
    this.loadSavedCredentials()
  },

  // 加载保存的账号密码
  loadSavedCredentials() {
    try {
      const savedUsername = wx.getStorageSync('saved_username')
      const savedPassword = wx.getStorageSync('saved_password')
      const rememberPassword = wx.getStorageSync('remember_password')

      if (rememberPassword && savedUsername) {
        this.setData({
          username: savedUsername,
          password: savedPassword || '',
          rememberPassword: true
        })
      }
    } catch (error) {
      console.error('读取保存的账号密码失败:', error)
    }
  },

  // 切换记住密码
  toggleRemember() {
    this.setData({
      rememberPassword: !this.data.rememberPassword
    })
  },

  // 输入用户名
  onUsernameInput(e) {
    this.setData({
      username: e.detail.value
    })
  },

  // 输入密码
  onPasswordInput(e) {
    this.setData({
      password: e.detail.value
    })
  },

  // 切换密码显示
  togglePassword() {
    this.setData({
      showPassword: !this.data.showPassword
    })
  },

  // 登录
  async onLogin() {
    const { username, password } = this.data

    // 验证用户名
    if (!username || !username.trim()) {
      wx.showToast({
        title: '请输入用户名',
        icon: 'none'
      })
      return
    }

    // 验证密码
    if (!password) {
      wx.showToast({
        title: '请输入密码',
        icon: 'none'
      })
      return
    }

    if (password.length < 6) {
      wx.showToast({
        title: '密码长度至少6位',
        icon: 'none'
      })
      return
    }

    try {
      wx.showLoading({
        title: '登录中...',
        mask: true
      })

      const res = await api.auth.login({
        username: username.trim(),
        password: password
      })

      console.log('登录响应数据:', res)

      // 验证返回数据
      if (!res || !res.token || !res.userInfo) {
        console.error('登录返回数据异常:', res)
        throw new Error('登录返回数据异常')
      }

      console.log('准备保存 Token:', res.token)

      // 保存登录信息
      app.login(res.userInfo, res.token)
      
      // 验证 Token 是否保存成功
      const savedToken = wx.getStorageSync('token')
      console.log('Token 保存验证:', savedToken ? '成功' : '失败', savedToken)

      // 保存或清除账号密码
      if (this.data.rememberPassword) {
        wx.setStorageSync('saved_username', username.trim())
        wx.setStorageSync('saved_password', password)
        wx.setStorageSync('remember_password', true)
      } else {
        wx.removeStorageSync('saved_username')
        wx.removeStorageSync('saved_password')
        wx.removeStorageSync('remember_password')
      }

      wx.hideLoading()
      wx.showToast({
        title: '登录成功',
        icon: 'success'
      })

      // 跳转到首页
      setTimeout(() => {
        wx.switchTab({
          url: '/pages/index/index'
        })
      }, 1500)
    } catch (e) {
      wx.hideLoading()
      console.error('登录失败:', e)
      const invalidCredential = /账号或密码错误|用户名或密码错误|invalid credentials|bad credentials/i.test(e.message || '')
      wx.showToast({
        title: invalidCredential ? '账号或密码错误，请重新输入' : e.message,
        icon: 'none'
      })
    }
  },

  // 跳转注册
  onRegister() {
    wx.navigateTo({
      url: '/pages/auth/register'
    })
  },

  // 忘记密码
  onForgotPassword() {
    wx.navigateTo({
      url: '/pages/auth/forgot-password'
    })
  }
})
