import request from '@/utils/request'

export const dishApi = {
  getList(params) {
    return request({ url: '/api/dish/admin/list', method: 'get', params, silentError: true })
  },
  getDetail(dishId) {
    return request({ url: `/api/dish/detail/${dishId}`, method: 'get' })
  },
  create(data) {
    return request({ url: '/api/dish/create', method: 'post', data, silentError: true })
  },
  update(dishId, data) {
    return request({ url: `/api/dish/update/${dishId}`, method: 'put', data, silentError: true })
  },
  updateStatus(dishId, data) {
    return request({ url: `/api/dish/status/${dishId}`, method: 'put', data, silentError: true })
  },
  uploadImages(files, dishId) {
    const formData = new FormData()
    files.forEach((file) => {
      formData.append('files', file)
    })
    if (dishId) {
      formData.append('dish_id', dishId)
    }
    return request({
      url: '/api/media/upload/images',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      silentError: true
    })
  },
  remove(dishId) {
    return request({ url: `/api/dish/delete/${dishId}`, method: 'delete', silentError: true })
  }
}
