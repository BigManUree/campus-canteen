// utils/api.js
const app = getApp()
const config = require('./config')

// 清理请求数据，移除 undefined/null
function cleanData(data = {}) {
  if (!data || typeof data !== 'object') return data
  const result = Array.isArray(data) ? [] : {}
  Object.keys(data).forEach((key) => {
    const value = data[key]
    if (value === undefined || value === null) {
      return
    }
    result[key] = value
  })
  return result
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms))
}

function classifyWxRequestFail(err) {
  const msg = (err && err.errMsg) ? String(err.errMsg) : ''
  if (msg.includes('timeout')) return '请求超时，请稍后重试'
  if (msg.includes('fail to fetch')) return '网络异常，请稍后重试'
  if (msg.includes('request:fail')) return '请求失败，请检查后端服务是否已启动'
  return '网络连接失败'
}

function extractErrorMessage(error, fallback = '请求失败') {
  if (!error) return fallback
  if (typeof error === 'string') return error

  if (typeof error.detail === 'string' && error.detail) {
    return error.detail
  }

  if (error.detail && typeof error.detail.message === 'string' && error.detail.message) {
    return error.detail.message
  }

  if (Array.isArray(error.detail) && error.detail.length > 0) {
    return error.detail.map((item) => {
      const field = item.loc && item.loc.length > 1 ? item.loc[item.loc.length - 1] : '字段'
      return `${field}: ${item.msg}`
    }).join('; ')
  }

  if (typeof error.message === 'string' && error.message) {
    return error.message
  }

  if (error.data) {
    return extractErrorMessage(error.data, fallback)
  }

  if (typeof error.errMsg === 'string' && error.errMsg) {
    if (error.errMsg.includes('request:fail')) {
      return '请求失败，请检查后端服务是否已启动'
    }
    return error.errMsg
  }

  return fallback
}

// 请求封装
function request(url, method = 'GET', data = {}, header = {}, options = {}) {
  const timeout = typeof options.timeout === 'number' ? options.timeout : (config.requestTimeout || 15000)
  const retryTimes = method === 'GET' ? (options.retryTimes ?? 1) : 0 // GET 默认重试 1 次
  const retryDelay = typeof options.retryDelay === 'number' ? options.retryDelay : 300

  const doRequestOnce = () =>
    new Promise((resolve, reject) => {
    // 允许调用方禁用 loading/toast
    const showLoading = options.showLoading !== false && method !== 'GET'
    const showToastOnError = options.showToastOnError !== false

    // 标记是否显示了 loading
    let hasLoading = false
    
    // 显示加载提示
    if (showLoading) {
      wx.showLoading({
        title: '加载中...',
        mask: true
      })
      hasLoading = true
    }

    const token = wx.getStorageSync('token') || app.globalData.token
    
    // 设置请求头
    const defaultHeader = {
      'Content-Type': 'application/json'
    }
    
    if (token) {
      defaultHeader['Authorization'] = `Bearer ${token}`
    }

    wx.request({
      url: (app.globalData.baseURL || config.baseURL) + url,
      method: method,
      data: cleanData(data),
      header: Object.assign(defaultHeader, header),
      timeout,
      success: (res) => {
        // 只有显示了 loading 才隐藏
        if (hasLoading) {
          wx.hideLoading()
        }
        
        if (res.statusCode >= 200 && res.statusCode < 300) {
          // 成功响应：直接返回数据（可能是对象或数组）
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // Token 过期或无效
          app.logout()
          if (showToastOnError) {
            wx.showToast({
              title: '登录已过期，请重新登录',
              icon: 'none',
              duration: 2000
            })
          }
          if (!app.globalData._authRedirecting) {
            app.globalData._authRedirecting = true
            setTimeout(() => {
              wx.reLaunch({
                url: '/pages/auth/login'
              })
              setTimeout(() => {
                app.globalData._authRedirecting = false
              }, 1500)
            }, 1200)
          }
          reject({ statusCode: 401, message: 'TOKEN_INVALID', data: res.data })
        } else if (res.statusCode === 403) {
          if (showToastOnError) {
            wx.showToast({
              title: '无权限访问',
              icon: 'none',
              duration: 2000
            })
          }
          reject({ statusCode: 403, message: 'FORBIDDEN', data: res.data })
        } else {
          const errorMsg = extractErrorMessage(res.data, `请求失败(${res.statusCode})`)
          if (showToastOnError) {
            wx.showToast({
              title: errorMsg,
              icon: 'none',
              duration: 2000
            })
          }
          reject({ statusCode: res.statusCode, message: errorMsg, data: res.data })
        }
      },
      fail: (err) => {
        // 只有显示了 loading 才隐藏
        if (hasLoading) {
          wx.hideLoading()
        }
        const errorMsg = extractErrorMessage(err, classifyWxRequestFail(err))
        if (showToastOnError) {
          wx.showToast({
            title: errorMsg,
            icon: 'none',
            duration: 2000
          })
        }
        reject({ statusCode: 0, message: errorMsg, data: err })
      }
    })
  })

  return (async () => {
    let lastErr
    for (let i = 0; i <= retryTimes; i++) {
      try {
        // eslint-disable-next-line no-await-in-loop
        return await doRequestOnce()
      } catch (e) {
        lastErr = e
        // 只有 GET 且明确允许重试才继续
        if (i < retryTimes) {
          // eslint-disable-next-line no-await-in-loop
          await sleep(retryDelay)
          continue
        }
      }
    }
    throw lastErr
  })()
}

// GET 请求
function get(url, data = {}, options = {}) {
  // 过滤掉 undefined、null 和空字符串的参数
  const filteredData = {}
  for (const key in data) {
    const value = data[key]
    if (value !== undefined && value !== null && value !== '') {
      filteredData[key] = value
    }
  }
  return request(url, 'GET', filteredData, {}, options)
}

// POST 请求
function post(url, data = {}, options = {}) {
  return request(url, 'POST', data, {}, options)
}

// PUT 请求
function put(url, data = {}, options = {}) {
  return request(url, 'PUT', data, {}, options)
}

// DELETE 请求
function del(url, data = {}, options = {}) {
  return request(url, 'DELETE', data, {}, options)
}

function upload(url, filePath, formData = {}, name = 'file') {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('token') || app.globalData.token
    const fullUrl = (app.globalData.baseURL || config.baseURL) + url
    
    wx.showLoading({
      title: '上传中...',
      mask: true
    })

    wx.uploadFile({
      url: fullUrl,
      filePath: filePath,
      name: name,
      formData: formData,
      header: {
        'Authorization': `Bearer ${token}`
      },
      success: (res) => {
        wx.hideLoading()
        
        try {
          const data = JSON.parse(res.data)
          
          if (res.statusCode === 200) {
            resolve(data)
          } else {
            const errorMsg = extractErrorMessage(data, `上传失败(${res.statusCode})`)
            wx.showToast({
              title: errorMsg,
              icon: 'none'
            })
            reject({ statusCode: res.statusCode, message: errorMsg, data: data })
          }
        } catch (e) {
          const errorMsg = '上传失败，响应格式错误'
          wx.showToast({
            title: errorMsg,
            icon: 'none'
          })
          reject({ message: errorMsg, error: e, rawData: res.data })
        }
      },
      fail: (err) => {
        wx.hideLoading()
        const errorMsg = extractErrorMessage(err, classifyWxRequestFail(err))
        wx.showToast({
          title: errorMsg,
          icon: 'none'
        })
        reject({ statusCode: 0, message: errorMsg, data: err })
      }
    })
  })
}

// API 接口
const api = {
  // 认证相关
  auth: {
    register: (data) => post('/auth/register', data),
    login: (data) => post('/auth/login', data),
    forgotPassword: (username) => post('/auth/forgot-password', { username }),
    resetPassword: (username, code, newPassword) => post('/auth/reset-password', {
      username,
      verification_code: code,
      new_password: newPassword
    })
  },
  
  // 用户相关
  user: {
    getInfo: () => get('/user/info'),
    updateInfo: (data) => put('/user/info', data),
    changePassword: (oldPassword, newPassword) => post(`/user/change-password?old_password=${oldPassword}&new_password=${newPassword}`, {})
  },
  
  // 地址相关
  address: {
    list: () => get('/address/list'),
    create: (data) => post('/address/create', data),
    update: (id, data) => put(`/address/update/${id}`, data),
    delete: (id) => del(`/address/delete/${id}`)
  },
  
  // 分类相关
  category: {
    list: (params) => get('/category/list', params),  // 支持传入参数，如 canteen_id
    all: () => get('/category/all'),
    detail: (id) => get(`/category/detail/${id}`)
  },

  // 档口相关
  canteen: {
    list: () => get('/canteen/list'),
    detail: (id) => get(`/canteen/detail/${id}`),
    queue: (id) => get(`/canteen/queue/${id}`)
  },
  
  // 菜品相关
  dish: {
    list: (params) => get('/dish/list', params),
    detail: (id) => get(`/dish/detail/${id}`)
  },
  
  // 购物车相关
  cart: {
    list: () => get('/cart/list'),
    add: (data) => post('/cart/add', data),
    update: (id, data) => put(`/cart/update/${id}`, data),
    remove: (id) => del(`/cart/remove/${id}`)
  },
  
  // 订单相关
  order: {
    create: (data) => post('/order/create', data),
    list: (params = {}) => get('/order/list', params),
    statusSummary: () => get('/order/status-summary', {}, { showLoading: false, showToastOnError: false }),
    markStatusViewed: (scope) => post('/order/status-viewed', { scope }, { showLoading: false, showToastOnError: false }),
    detail: (id) => get(`/order/detail/${id}`),
    timeline: (id) => get(`/order/timeline/${id}`),
    cancel: (id, data) => post(`/order/cancel/${id}`, data),
    pay: (id) => post(`/order/pay/${id}`, { order_status: 1, pay_status: 1 }),
    confirm: (id) => post(`/order/confirm/${id}`),
    remind: (id) => post(`/order/remind/${id}`),
    reorder: (id) => post(`/order/reorder/${id}`),
    delete: (id) => del(`/order/delete/${id}`)
  },

  // 优惠券相关
  coupon: {
    list: () => get('/coupon/list'),
    claim: (id) => post(`/coupon/claim/${id}`),
    my: (status) => get('/coupon/my', status ? { status } : {})
  },

  // 通知相关
  notification: {
    list: (params = {}) => get('/notification/list', params),  // 获取通知列表
    unreadCount: () => get('/notification/unread-count', {}, { showLoading: false, showToastOnError: false }),  // 获取未读数量
    markRead: (notificationIds = null) => post('/notification/mark-read', { notification_ids: notificationIds }, { showLoading: false, showToastOnError: false }),  // 标记已读
    delete: (id) => del(`/notification/${id}`, {}, { showLoading: false, showToastOnError: false }),  // 删除通知
    recent: () => get('/notification/recent'),  // 最近通知（兼容旧版）
    read: (id) => post('/notification/mark-read', { notification_ids: [id] }, { showLoading: false, showToastOnError: false }),  // 标记单个已读
    readAll: () => post('/notification/mark-read', { notification_ids: null }, { showLoading: false, showToastOnError: false }),  // 全部已读
    batchDelete: (ids = []) => post('/notification/batch-delete', { notification_ids: ids }, { showLoading: false, showToastOnError: false }),  // 批量删除
    clear: () => del('/notification/clear', {}, { showLoading: false, showToastOnError: false }),
    order: (orderId) => get(`/notification/order/${orderId}`)  // 订单通知
  },

  // 退款相关
  refund: {
    create: (data) => post('/refund/create', data),  // 创建退款申请
    list: (params = {}) => get('/refund/list', params),  // 获取退款列表
    detail: (id) => get(`/refund/${id}`),  // 获取退款详情
    approve: (id, data = {}) => post(`/refund/${id}/approve`, data),  // 批准退款（管理员）
    reject: (id, data = {}) => post(`/refund/${id}/reject`, data),  // 拒绝退款（管理员）
    statistics: (days = 30) => get('/refund/statistics', { days })  // 退款统计（管理员）
  },
  
  // 收藏相关
  favorite: {
    list: (page = 1, pageSize = 20) => get('/favorite/list', { page, page_size: pageSize }),
    check: (dishId) => get(`/favorite/check/${dishId}`, {}, { showLoading: false, showToastOnError: false }),
    add: (dishId) => post('/favorite/add', { dish_id: dishId }),
    remove: (dishId) => del('/favorite/remove', { dish_id: dishId })
  },
  
  // 评价相关
  review: {
    create: (data) => post('/review/create', data),
    list: (dishId, params = {}) => get(`/review/list/${dishId}`, params),
    orderStatus: (orderId) => get(`/review/order/${orderId}`),
    canteenCreate: (data) => post('/review/canteen/create', data),
    canteenList: (canteenId) => get(`/review/canteen/list/${canteenId}`)
  },
  
  // 浏览历史
  history: {
    list: (page = 1, pageSize = 20) => get('/browse/history', { page, page_size: pageSize }),
    add: (dishId) => post(`/browse/add/${dishId}`),
    clear: () => del('/browse/clear'),
    remove: (dishId) => del(`/browse/remove/${dishId}`)
  },
  
  // 消息相关
  message: {
    list: () => get('/message/list'),
    send: (data) => post('/message/send', data)
  },
  
  // 定位相关
  location: {
    canteen: (id, lat, lon) => get(`/location/canteen/${id}`, lat && lon ? { user_lat: lat, user_lon: lon } : {}),
    pickup: () => get('/location/pickup'),
    distance: (lat1, lon1, lat2, lon2) => get('/location/distance', { lat1, lon1, lat2, lon2 })
  },
  
  // 媒体相关
  media: {
    upload: (filePath, dishId) => upload('/media/upload', filePath, { dish_id: dishId }),
    uploadAvatar: (filePath) => upload('/media/upload/avatar', filePath, {}),
    uploadReview: (filePath) => upload('/media/upload/review', filePath, {}, 'files'),
    dish: (dishId) => get(`/media/dish/${dishId}`)
  },

  // 活动相关
  activity: {
    list: () => get('/activity/list')
  },

  // 搜索相关
  search: {
    all: (keyword, params = {}) => get('/search/all', { keyword, ...params }),
    suggest: (keyword, limit = 10) => get('/search/suggest', { keyword, limit }),
    hot: (limit = 10) => get('/search/hot', { limit }),
    history: (limit = 20) => get('/search/history', { limit }),
    addHistory: (keyword, searchType = 'all') => post('/search/history', { 
      keyword, 
      search_type: searchType 
    }, { 
      showLoading: false, 
      showToastOnError: false 
    }).then(() => {}).catch(() => {}), // 静默添加，不影响用户体验
    clearHistory: () => del('/search/history')
  },

  // FAQ相关
  faq: {
    list: (params = {}) => get('/faq/list', params),
    detail: (id) => get(`/faq/detail/${id}`)
  }
}

module.exports = api

