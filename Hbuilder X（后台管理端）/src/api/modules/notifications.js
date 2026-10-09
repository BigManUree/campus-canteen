import request from '@/utils/request'

export const notificationApi = {
  getList(params) {
    return request({
      url: '/api/notification/list',
      method: 'get',
      params: {
        ...params,
        readStatus: params?.readStatus === 1 ? true : params?.readStatus === 0 ? false : undefined
      },
      silentError: true
    })
  },
  getStatistics() {
    return request({ url: '/api/notification/statistics', method: 'get', silentError: true })
  },
  markRead(data) {
    return request({ url: '/api/notification/mark-read', method: 'post', data, silentError: true })
  },
  remove(notificationId) {
    return request({ url: `/api/notification/${notificationId}`, method: 'delete', silentError: true })
  },
  getRecent(params) {
    return request({ url: '/api/notification/recent', method: 'get', params })
  },
  getUnreadCount() {
    return request({ url: '/api/notification/unread-count', method: 'get' })
  }
}
