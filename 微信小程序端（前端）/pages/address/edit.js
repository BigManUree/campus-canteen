// pages/address/edit.js
const api = require('../../utils/api.js')
const util = require('../../utils/util.js')
const app = getApp()

Page({
  data: {
    addressId: null,
    receiver: '',
    phone: '',
    building: '',
    room: '',
    latitude: null,
    longitude: null,
    isDefault: 0,
    isEdit: false,
    adminAlertOverlay: {
      show: false,
      alert: null,
      queueLength: 0
    }
  },

  onLoad(options) {
    app.bindAdminAlertToPage(this)
    if (options.id) {
      this.setData({ addressId: options.id, isEdit: true })
      this.loadAddress()
    }
  },

  // 加载地址
  async loadAddress() {
    try {
      const addresses = await api.address.list()
      // 确保ID类型一致（字符串或数字）
      const address = addresses.find(addr => String(addr.address_id) === String(this.data.addressId))
      if (address) {
        this.setData({
          receiver: address.receiver || '',
          phone: address.phone || '',
          building: address.building || '',
          room: address.room || '',
          latitude: address.latitude || null,
          longitude: address.longitude || null,
          isDefault: address.is_default || 0
        })
      } else {
        wx.showToast({ title: '地址不存在', icon: 'none' })
        setTimeout(() => wx.navigateBack(), 1500)
      }
    } catch (error) {
      console.error('加载地址失败:', error)
      wx.showToast({ title: error.message, icon: 'none' })
    }
  },

  // 输入处理
  onReceiverInput(e) {
    this.setData({ receiver: e.detail.value })
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
  },

  onBuildingInput(e) {
    this.setData({ building: e.detail.value })
  },

  onRoomInput(e) {
    this.setData({ room: e.detail.value })
  },

  onDefaultChange(e) {
    this.setData({ isDefault: e.detail.value ? 1 : 0 })
  },

  // 选择位置
  async onChooseLocation() {
    try {
      const location = await util.chooseLocation()
      this.setData({
        building: location.name || location.address || '',
        latitude: location.latitude,
        longitude: location.longitude
      })
    } catch (error) {
      console.error('选择位置失败:', error)
    }
  },

  // 保存地址
  async onSave() {
    return util.withLock('address_save', async () => {
      const { receiver, phone, building, room, latitude, longitude, isDefault, addressId, isEdit } = this.data

      // 验证收件人
      if (!receiver || !receiver.trim()) {
        wx.showToast({ title: '请输入收件人', icon: 'none' })
        return
      }

      // 验证手机号
      if (!phone || !phone.trim()) {
        wx.showToast({ title: '请输入手机号', icon: 'none' })
        return
      }

      if (!/^1[3-9]\d{9}$/.test(phone)) {
        wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
        return
      }

      // 验证楼栋
      if (!building || !building.trim()) {
        wx.showToast({ title: '请输入楼栋', icon: 'none' })
        return
      }

      // 验证房间号
      if (!room || !room.trim()) {
        wx.showToast({ title: '请输入房间号', icon: 'none' })
        return
      }

      try {
        wx.showLoading({ title: '保存中...', mask: true })

        const addressData = {
          receiver: receiver.trim(),
          phone: phone.trim(),
          building: building.trim(),
          room: room.trim(),
          latitude: latitude || undefined,
          longitude: longitude || undefined,
          is_default: isDefault
        }

        if (isEdit && addressId) {
          await api.address.update(addressId, addressData)
        } else {
          await api.address.create(addressData)
        }

        wx.hideLoading()
        wx.showToast({ title: '保存成功', icon: 'success' })

        setTimeout(() => {
          wx.navigateBack()
        }, 1500)
      } catch (error) {
        wx.hideLoading()
        console.error('保存地址失败:', error)
      }
    }, 1500)
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
