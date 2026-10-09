import request from '@/utils/request'

export const authApi = {
  login(data) {
    return request({
      url: '/api/auth/login',
      method: 'post',
      data
    })
  },
  getProfile() {
    return request({
      url: '/api/user/info',
      method: 'get'
    })
  }
}
