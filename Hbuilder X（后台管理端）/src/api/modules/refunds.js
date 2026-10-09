import request from '@/utils/request'

export const refundApi = {
  getList(params) {
    return request({ url: '/api/refund/admin/list', method: 'get', params, silentError: true })
  },
  getDetail(refundId) {
    return request({ url: `/api/refund/admin/detail/${refundId}`, method: 'get', silentError: true })
  },
  audit(refundId, data) {
    return request({ url: `/api/refund/admin/audit/${refundId}`, method: 'post', data, silentError: true })
  }
}
