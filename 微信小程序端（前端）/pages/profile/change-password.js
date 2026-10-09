// pages/profile/change-password.js
const api = require('../../utils/api.js')

Page({
  data: {
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
    showOldPassword: false,
    showNewPassword: false,
    showConfirmPassword: false
  },

  // 输入旧密码
  onOldPasswordInput(e) {
    this.setData({ oldPassword: e.detail.value })
  },

  // 输入新密码
  onNewPasswordInput(e) {
    this.setData({ newPassword: e.detail.value })
  },

  // 输入确认密码
  onConfirmPasswordInput(e) {
    this.setData({ confirmPassword: e.detail.value })
  },

  // 切换旧密码显示
  toggleOldPassword() {
    this.setData({ showOldPassword: !this.data.showOldPassword })
  },

  // 切换新密码显示
  toggleNewPassword() {
    this.setData({ showNewPassword: !this.data.showNewPassword })
  },

  // 切换确认密码显示
  toggleConfirmPassword() {
    this.setData({ showConfirmPassword: !this.data.showConfirmPassword })
  },

  // 提交修改
  async onSubmit() {
    const { oldPassword, newPassword, confirmPassword } = this.data

    if (!oldPassword) {
      wx.showToast({ title: '请输入旧密码', icon: 'none' })
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

    if (newPassword !== confirmPassword) {
      wx.showToast({ title: '两次密码不一致', icon: 'none' })
      return
    }

    try {
      wx.showLoading({ title: '修改中...', mask: true })
      await api.user.changePassword(oldPassword, newPassword)
      wx.hideLoading()
      wx.showToast({ title: '修改成功', icon: 'success' })
      
      setTimeout(() => {
        wx.navigateBack()
      }, 1500)
    } catch (error) {
      wx.hideLoading()
      console.error('修改密码失败:', error)
    }
  }
})
