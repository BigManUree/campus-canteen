import request from '@/utils/request'

export const canteenApi = {
  getList(params) {
    return request({ url: '/api/canteen/list', method: 'get', params, silentError: true })
  },
  create(data) {
    return request({ url: '/api/canteen/create', method: 'post', data, silentError: true })
  },
  getDetail(canteenId) {
    return request({ url: `/api/canteen/detail/${canteenId}`, method: 'get' })
  },
  update(canteenId, data) {
    return request({ url: `/api/canteen/update/${canteenId}`, method: 'put', data, silentError: true })
  },
  updateStatus(canteenId, status) {
    return request({ url: `/api/canteen/status/${canteenId}`, method: 'put', params: { status }, silentError: true })
  },
  remove(canteenId) {
    return request({ url: `/api/canteen/delete/${canteenId}`, method: 'delete', silentError: true })
  }
}
