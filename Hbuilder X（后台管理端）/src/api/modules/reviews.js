import request from '@/utils/request'

export const reviewApi = {
  getList(params) {
    return request({ url: '/api/review/admin/list', method: 'get', params })
  },
  remove(reviewId) {
    return request({ url: `/api/review/admin/${reviewId}`, method: 'delete' })
  }
}
