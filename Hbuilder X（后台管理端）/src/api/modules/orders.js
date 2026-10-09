import request from '@/utils/request'

export const orderApi = {
  getList(params) {
    return request({ url: '/api/order/admin/list', method: 'get', params, silentError: true })
  },
  getDetail(orderId) {
    return request({ url: `/api/order/detail/${orderId}`, method: 'get', silentError: true })
  },
  cancel(orderId, data) {
    return request({ url: `/api/order/cancel/${orderId}`, method: 'post', data, silentError: true })
  },
  updateStatus(orderId, data) {
    return request({ url: `/api/order/status/${orderId}`, method: 'put', data, silentError: true })
  },
  verifyPickup(orderId, data) {
    return request({ url: `/api/order/verify/${orderId}`, method: 'post', data, silentError: true })
  },
  getStatistics(params) {
    return request({ url: '/api/statistics/dashboard', method: 'get', params, silentError: true })
  }
}
