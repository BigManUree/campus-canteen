import request, { requestFile } from '@/utils/request'

export const exportApi = {
  exportOrders(params) {
    return requestFile({
      url: '/api/statistics/export/orders',
      method: 'get',
      params,
      silentError: true
    })
  },
  exportSales(params) {
    return requestFile({
      url: '/api/statistics/export/sales',
      method: 'get',
      params,
      silentError: true
    })
  }
}

