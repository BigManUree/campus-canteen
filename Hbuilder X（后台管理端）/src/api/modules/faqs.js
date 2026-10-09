import request from '@/utils/request'

export const faqApi = {
  getList(params) {
    return request({ url: '/api/faq/list', method: 'get', params, silentError: true })
  },
  create(data) {
    return request({ url: '/api/faq/create', method: 'post', data, silentError: true })
  },
  update(faqId, data) {
    return request({ url: `/api/faq/update/${faqId}`, method: 'put', data, silentError: true })
  },
  remove(faqId) {
    return request({ url: `/api/faq/delete/${faqId}`, method: 'delete', silentError: true })
  }
}
