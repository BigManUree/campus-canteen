// pages/auth/forgot-password.js
const api = require('../../utils/api.js')

Page({
  data: {
    username: '',
    code: '',
    newPassword: '',
    confirmPassword: '',
    step: 1,
    codeSent: false,
    verificationCode: '',
    showNewPassword: false,
    showConfirmPassword: false,
    sendingCode: false,
    resetting: false,
    countdown: 0,
    timer: null
  },

  onUnload() {
    this.clearTimer()
  },

  onUsernameInput(e) {
    this.setData({ username: e.detail.value })
  },

  onCodeInput(e) {
    this.setData({ code: e.detail.value })
  },

  onNewPasswordInput(e) {
    this.setData({ newPassword: e.detail.value })
  },

  onConfirmPasswordInput(e) {
    this.setData({ confirmPassword: e.detail.value })
  },

  toggleNewPassword() {
    this.setData({ showNewPassword: !this.data.showNewPassword })
  },

  toggleConfirmPassword() {
    this.setData({ showConfirmPassword: !this.data.showConfirmPassword })
  },

  normalizeUsername(value) {
    return String(value || '').trim()
  },

  validateUsername(username) {
    if (!username) {
      return '请输入用户名或手机号'
    }

    const isPhone = /^1[3-9]\d{9}$/.test(username)
    if (isPhone) return ''

    if (username.length < 3) {
      return '用户名至少3位'
    }

    return ''
  },

  startCountdown(seconds = 60) {
    this.clearTimer()
    this.setData({ countdown: seconds })

    const timer = setInterval(() => {
      const next = this.data.countdown - 1
      if (next <= 0) {
        this.clearTimer()
        this.setData({ countdown: 0 })
        return
      }
      this.setData({ countdown: next })
    }, 1000)

    this.setData({ timer })
  },

  clearTimer() {
    if (this.data.timer) {
      clearInterval(this.data.timer)
      this.setData({ timer: null })
    }
  },

  async onSendCode() {
    const username = this.normalizeUsername(this.data.username)

    const usernameError = this.validateUsername(username)
    if (usernameError) {
      wx.showToast({ title: usernameError, icon: 'none' })
      return
    }

    if (this.data.sendingCode || this.data.countdown > 0) {
      return
    }

    this.setData({ sendingCode: true, username })

    try {
      const res = await api.auth.forgotPassword(username)
      const verificationCode = res && res.verification_code ? String(res.verification_code) : ''

      this.setData({
        codeSent: true,
        step: 2,
        verificationCode,
        code: '',
        newPassword: '',
        confirmPassword: ''
      })

      this.startCountdown(60)

      if (verificationCode) {
        wx.showModal({
          title: '验证码已发送',
          content: `开发环境验证码：${verificationCode}`,
          showCancel: false
        })
      } else {
        wx.showToast({ title: res.message || '验证码已发送', icon: 'success' })
      }
    } catch (error) {
      console.error('发送验证码失败:', error)
      const message = error && error.statusCode === 404
        ? '该手机号或用户名未注册'
        : ((error && error.message && error.message !== 'request:fail')
          ? error.message
          : '发送失败，请稍后重试')
      wx.showToast({ title: message, icon: 'none' })
    } finally {
      this.setData({ sendingCode: false })
    }
  },

  async onResetPassword() {
    const username = this.normalizeUsername(this.data.username)
    const code = String(this.data.code || '').trim()
    const newPassword = this.data.newPassword || ''
    const confirmPassword = this.data.confirmPassword || ''

    const usernameError = this.validateUsername(username)
    if (usernameError) {
      wx.showToast({ title: usernameError, icon: 'none' })
      return
    }

    if (!code) {
      wx.showToast({ title: '请输入验证码', icon: 'none' })
      return
    }

    if (!/^\d{4,6}$/.test(code)) {
      wx.showToast({ title: '验证码格式不正确', icon: 'none' })
      return
    }

    if (!newPassword) {
      wx.showToast({ title: '请输入新密码', icon: 'none' })
      return
    }

    if (newPassword.length < 6) {
      wx.showToast({ title: '密码长度至少6位', icon: 'none' })
      return
    }

    if (newPassword.length > 50) {
      wx.showToast({ title: '密码长度不能超过50位', icon: 'none' })
      return
    }

    if (!confirmPassword) {
      wx.showToast({ title: '请再次输入新密码', icon: 'none' })
      return
    }

    if (newPassword !== confirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    if (this.data.resetting) {
      return
    }

    this.setData({ resetting: true, username })

    try {
      const res = await api.auth.resetPassword(username, code, newPassword)
      wx.showToast({ title: res.message || '密码重置成功', icon: 'success' })

      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (error) {
      console.error('重置密码失败:', error)
    } finally {
      this.setData({ resetting: false })
    }
  }
})
