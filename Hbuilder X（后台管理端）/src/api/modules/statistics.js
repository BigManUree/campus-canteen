import request from '@/utils/request'

export const statisticsApi = {
  getSalesTrend(params) {
    return request({ url: '/api/statistics/sales/trend-admin', method: 'get', params, silentError: true })
  },
  getDishRanking(params) {
    return request({ url: '/api/statistics/ranking/dishes', method: 'get', params, silentError: true })
  },
  getStallRanking(params) {
    return request({ url: '/api/statistics/ranking/stalls', method: 'get', params, silentError: true })
  },
  getUserGrowth(params) {
    return request({ url: '/api/statistics/users/growth', method: 'get', params, silentError: true })
  },
  getRefundSummary(params) {
    return request({ url: '/api/statistics/refund/summary', method: 'get', params, silentError: true })
  },
  getOverview(params) {
    return request({ url: '/api/statistics/dashboard', method: 'get', params, silentError: true })
  }
}
