import request from '@/utils/request'

export const dashboardApi = {
  getOverview(params) {
    return request({ url: '/api/statistics/dashboard', method: 'get', params, silentError: true })
  }
}
