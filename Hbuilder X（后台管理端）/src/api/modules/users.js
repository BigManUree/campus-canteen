import request from '@/utils/request'

export const userApi = {
  getProfile() {
    return request({ url: '/api/user/info', method: 'get' })
  },
  getList(params) {
    return request({ url: '/api/user/list', method: 'get', params: {
      pageNum: params?.page,
      pageSize: params?.page_size,
      keyword: params?.keyword || undefined,
      role: params?.role || undefined,
      status: params?.status
    }, silentError: true })
  },
  getDetail(userId) {
    return request({ url: `/api/user/detail/${userId}`, method: 'get', silentError: true })
  },
  update(userId, data) {
    return request({ url: `/api/user/update/${userId}`, method: 'put', data, silentError: true })
  },
  updateStatus(userId, data) {
    return request({ url: `/api/user/status/${userId}`, method: 'put', data, silentError: true })
  },
  updateRole(userId, data) {
    return request({ url: `/api/user/role/${userId}`, method: 'put', data, silentError: true })
  },
  remove(userId) {
    return request({ url: `/api/user/${userId}`, method: 'delete', silentError: true })
  }
}
