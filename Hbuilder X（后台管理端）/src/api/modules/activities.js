import request from '@/utils/request'

export const activityApi = {
  getList() {
    return request({ url: '/api/activity/admin/list', method: 'get', silentError: true })
  },
  create(data) {
    return request({ url: '/api/activity/create', method: 'post', data, silentError: true })
  },
  update(activityId, data) {
    return request({ url: `/api/activity/update/${activityId}`, method: 'put', data, silentError: true })
  },
  updateStatus(activityId, status) {
    return request({ url: `/api/activity/status/${activityId}`, method: 'put', data: { status }, silentError: true })
  },
  uploadImage(file, activityId) {
    const formData = new FormData()
    formData.append('file', file)
    if (activityId) {
      formData.append('activity_id', activityId)
    }
    return request({
      url: '/api/activity/upload/image',
      method: 'post',
      data: formData,
      headers: { 'Content-Type': 'multipart/form-data' },
      silentError: true
    })
  },
  remove(activityId) {
    return request({ url: `/api/activity/delete/${activityId}`, method: 'delete', silentError: true })
  }
}

