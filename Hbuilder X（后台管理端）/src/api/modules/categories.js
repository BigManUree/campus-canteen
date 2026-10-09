import request from '@/utils/request'

export const categoryApi = {
  getList(params) {
    return request({ url: '/api/category/all', method: 'get', params })
  },
  getDetail(categoryId) {
    return request({ url: `/api/category/detail/${categoryId}`, method: 'get' })
  },
  create(data) {
    return request({ url: '/api/category/create', method: 'post', data })
  },
  update(categoryId, data) {
    return request({ url: `/api/category/update/${categoryId}`, method: 'put', data })
  },
  remove(categoryId) {
    return request({ url: `/api/category/delete/${categoryId}`, method: 'delete' })
  }
}
