import request from '@/utils/request'

export const messageApi = {
  getList(params) {
    return request({ url: '/api/message/list', method: 'get', params: { user_id: params?.user_id }, silentError: true })
  },
  getUnreadCount(params) {
    return request({ url: '/api/message/unread-count', method: 'get', params: { user_id: params?.user_id }, silentError: true })
  },
  markRead(messageId) {
    return request({ url: `/api/message/${messageId}/read`, method: 'put', silentError: true })
  },
  markAllRead(userId) {
    return request({ url: '/api/message/read-all', method: 'put', params: { user_id: userId }, silentError: true })
  },
  send(data) {
    return request({ url: '/api/message/send', method: 'post', data, silentError: true })
  },
  remove(messageId) {
    return request({ url: `/api/message/${messageId}`, method: 'delete', silentError: true })
  }
}

