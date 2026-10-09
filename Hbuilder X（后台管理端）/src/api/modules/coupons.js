import request from '@/utils/request'

export const couponApi = {
  getList(params) {
    return request({ url: '/api/coupon/list', method: 'get', params, silentError: true })
  },
  getMine(params) {
    return request({ url: '/api/coupon/my', method: 'get', params })
  },
  claim(couponId) {
    return request({ url: `/api/coupon/claim/${couponId}`, method: 'post' })
  },
  create(data) {
    return request({ url: '/api/coupon/create', method: 'post', data, silentError: true })
  },
  update(couponId, data) {
    return request({ url: `/api/coupon/update/${couponId}`, method: 'put', data, silentError: true })
  },
  updateStatus(couponId, status) {
    return request({ url: `/api/coupon/status/${couponId}`, method: 'put', data: { status }, silentError: true })
  },
  remove(couponId) {
    return request({ url: `/api/coupon/delete/${couponId}`, method: 'delete', silentError: true })
  }
}
