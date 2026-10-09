// utils/util.js

/**
 * 格式化时间
 */
function formatTime(date) {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('-')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

function formatNumber(n) {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

/**
 * 格式化日期
 */
function formatDate(date, format = 'YYYY-MM-DD') {
  if (!date) return ''
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return ''
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')

  // 使用正则表达式替换，避免重复替换
  return format
    .replace(/YYYY/g, year)
    .replace(/MM/g, month)
    .replace(/DD/g, day)
    .replace(/HH/g, hour)
    .replace(/mm/g, minute)
    .replace(/ss/g, second)
}

/**
 * 格式化价格
 */
function formatPrice(price) {
  const value = Number(price)
  if (Number.isNaN(value)) return '0.00'
  return value.toFixed(2)
}

/**
 * 格式化金额文案（可带前缀/后缀）
 */
function formatMoneyText(price, prefix = '¥', suffix = '') {
  return `${prefix}${formatPrice(price)}${suffix}`
}

/**
 * 格式化距离
 */
function formatDistance(distance) {
  if (!distance) return ''
  if (distance < 1000) {
    return `${Math.round(distance)}m`
  }
  return `${(distance / 1000).toFixed(1)}km`
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
  let timeout
  return function(...args) {
    const context = this
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      func.apply(context, args)
    }, wait)
  }
}

/**
 * 防重复提交锁（同一个 key 在 lockMs 内只允许执行一次）
 */
function withLock(key, fn, lockMs = 1200) {
  const app = getApp()
  if (!app.globalData.__locks) app.globalData.__locks = {}
  const locks = app.globalData.__locks

  if (locks[key]) return Promise.resolve(false)
  locks[key] = true

  const release = () => {
    setTimeout(() => {
      locks[key] = false
    }, lockMs)
  }

  try {
    const ret = fn()
    return Promise.resolve(ret).finally(release)
  } catch (e) {
    release()
    return Promise.reject(e)
  }
}

/**
 * 节流函数
 */
function throttle(func, wait) {
  let previous = 0
  return function(...args) {
    const now = Date.now()
    if (now - previous > wait) {
      func.apply(this, args)
      previous = now
    }
  }
}

/**
 * 获取订单状态文本
 */
function getOrderStatusText(status) {
  const statusMap = {
    0: '待确认',
    1: '制作中',
    2: '待取餐',
    3: '配送中',
    4: '已完成',
    5: '已取消'
  }
  return statusMap[status] || '未知'
}

/**
 * 获取订单状态颜色
 */
function getOrderStatusColor(status) {
  const colorMap = {
    0: '#ff9500',
    1: '#007aff',
    2: '#34c759',
    3: '#5856d6',
    4: '#8e8e93',
    5: '#ff3b30'
  }
  return colorMap[status] || '#8e8e93'
}

/**
 * 计算总价
 */
function calculateTotal(items) {
  if (!items || items.length === 0) return 0
  return items.reduce((total, item) => {
    return total + (item.price || 0) * (item.quantity || 0)
  }, 0)
}

/**
 * 检查登录状态
 */
function checkLogin() {
  const app = getApp()
  if (!app.globalData.isLogin) {
    wx.showModal({
      title: '提示',
      content: '请先登录',
      showCancel: true,
      cancelText: '取消',
      confirmText: '去登录',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({
            url: '/pages/auth/login'
          })
        }
      }
    })
    return false
  }
  return true
}

/**
 * 检查 Token 是否过期
 */
function isTokenExpired() {
  const token = wx.getStorageSync('token')
  if (!token) return true
  
  try {
    // 解析 JWT payload
    const parts = token.split('.')
    if (parts.length !== 3) return true
    
    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp * 1000 // 转换为毫秒
    
    // 提前5分钟判断为过期，避免请求时才过期
    return Date.now() >= (exp - 5 * 60 * 1000)
  } catch (error) {
    console.error('Token 解析失败:', error)
    return true
  }
}

/**
 * 获取 Token 剩余有效时间（秒）
 */
function getTokenRemainingTime() {
  const token = wx.getStorageSync('token')
  if (!token) return 0
  
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return 0
    
    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp * 1000
    const remaining = Math.max(0, exp - Date.now())
    
    return Math.floor(remaining / 1000)
  } catch (error) {
    return 0
  }
}

/**
 * 获取位置信息
 */
function getLocation() {
  return new Promise((resolve, reject) => {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        resolve({
          latitude: res.latitude,
          longitude: res.longitude
        })
      },
      fail: (err) => {
        if (err.errMsg.includes('auth deny')) {
          wx.showModal({
            title: '提示',
            content: '需要获取您的位置信息，请在设置中开启位置权限',
            showCancel: false,
            confirmText: '确定'
          })
        }
        reject(err)
      }
    })
  })
}

/**
 * 选择位置
 */
function chooseLocation() {
  return new Promise((resolve, reject) => {
    wx.chooseLocation({
      success: (res) => {
        resolve({
          name: res.name,
          address: res.address,
          latitude: res.latitude,
          longitude: res.longitude
        })
      },
      fail: reject
    })
  })
}

/**
 * 打开地图导航
 */
function openLocation(latitude, longitude, name = '') {
  wx.openLocation({
    latitude: latitude,
    longitude: longitude,
    name: name,
    scale: 18
  })
}

/**
 * 预览图片
 */
function previewImage(urls, current = 0) {
  wx.previewImage({
    urls: urls,
    current: typeof current === 'number' ? urls[current] : current
  })
}

/**
 * 选择图片
 */
function chooseImage(count = 9) {
  return new Promise((resolve, reject) => {
    wx.chooseImage({
      count: count,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        resolve(res.tempFilePaths)
      },
      fail: reject
    })
  })
}

/**
 * 处理图片 URL（将相对路径转换为完整 URL）
 */
function formatImageUrl(url) {
  if (!url) return ''

  // 将 Windows 路径的反斜杠转换为正斜杠
  url = String(url).trim().replace(/\\/g, '/')
  if (!url) return ''

  // 小程序本地静态资源直接返回
  if (url.startsWith('/static/')) {
    return url
  }

  const app = getApp()
  const host = app.globalData.host || (app.globalData.baseURL || 'http://127.0.0.1:8000/api').replace(/\/api$/, '')
  const serverURL = String(host).replace(/\/+$/, '')

  // 绝对 URL 统一替换为当前服务主机，避免返回 localhost 等不可访问地址
  if (url.startsWith('http://') || url.startsWith('https://')) {
    try {
      const parsed = new URL(url)
      return `${serverURL}${parsed.pathname}${parsed.search || ''}`
    } catch (e) {
      return url
    }
  }

  // 兼容历史返回的绝对磁盘路径，截取资源根路径之后的部分
  const resourcePrefixes = ['/uploads/', '/media/', '/static/']
  for (const prefix of resourcePrefixes) {
    const index = url.indexOf(prefix)
    if (index >= 0) {
      return `${serverURL}${url.slice(index)}`
    }
  }

  // 其余相对路径按原样拼接到主机根路径，不再强制补 /uploads/
  const normalizedPath = url.startsWith('/') ? url : `/${url}`
  return `${serverURL}${normalizedPath}`
}

module.exports = {
  formatTime,
  formatDate,
  formatPrice,
  formatMoneyText,
  formatDistance,
  debounce,
  withLock,
  throttle,
  getOrderStatusText,
  getOrderStatusColor,
  calculateTotal,
  checkLogin,
  isTokenExpired,
  getTokenRemainingTime,
  getLocation,
  chooseLocation,
  openLocation,
  previewImage,
  chooseImage,
  formatImageUrl
}
