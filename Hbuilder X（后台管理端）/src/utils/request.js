import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { BASE_URL, STORAGE_KEYS } from '@/utils/constants'

const request = axios.create({
  baseURL: BASE_URL,
  timeout: 20000,
  withCredentials: false
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem(STORAGE_KEYS.token)
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

const getErrorMessage = (error) => {
  const detail = error.response?.data?.detail
  return Array.isArray(detail)
    ? detail.map((item) => `${item.loc?.[item.loc.length - 1] || '字段'}: ${item.msg}`).join('；')
    : detail || error.response?.data?.message || error.message || '请求失败'
}

request.interceptors.response.use(
  (response) => (response.config?.returnFullResponse ? response : response.data),
  (error) => {
    const status = error.response?.status
    const message = getErrorMessage(error)
    error.userMessage = message

    if (status === 401) {
      localStorage.removeItem(STORAGE_KEYS.token)
      localStorage.removeItem(STORAGE_KEYS.user)
      if (router.currentRoute.value.path !== '/login') {
        router.replace('/login')
      }
    }

    if (!error.config?.silentError) {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export const requestFile = (config) => request({
  ...config,
  returnFullResponse: true,
  responseType: 'blob'
})

export default request
