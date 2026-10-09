import request from '@/utils/request'

export const queueApi = {
  getInfo(canteenId) {
    return request({ url: `/api/canteen/queue/${canteenId}`, method: 'get', silentError: true })
  },
  update(canteenId, data) {
    return request({ url: `/api/canteen/queue/update/${canteenId}`, method: 'put', data, silentError: true })
  }
}

