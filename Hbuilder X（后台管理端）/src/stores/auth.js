import { defineStore } from 'pinia'
import { authApi } from '@/api/modules/auth'
import { ADMIN_ROLE_SET, STORAGE_KEYS } from '@/utils/constants'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(STORAGE_KEYS.token) || '',
    user: JSON.parse(localStorage.getItem(STORAGE_KEYS.user) || 'null')
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.token),
    userName: (state) => state.user?.nickname || state.user?.username || '管理员',
    roleLabel: (state) => {
      const roleMap = {
        admin: '管理员',
        sys_admin: '系统管理员',
        merchant: '商家管理员',
        canteen_admin: '档口管理员'
      }
      return roleMap[state.user?.role] || '管理人员'
    }
  },
  actions: {
    setAuth(payload) {
      this.token = payload.token || ''
      this.user = payload.userInfo || payload.user || null
      localStorage.setItem(STORAGE_KEYS.token, this.token)
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(this.user))
    },
    clearAuth() {
      this.token = ''
      this.user = null
      localStorage.removeItem(STORAGE_KEYS.token)
      localStorage.removeItem(STORAGE_KEYS.user)
    },
    async login(form) {
      const result = await authApi.login(form)
      const role = result?.userInfo?.role || result?.user?.role
      if (!ADMIN_ROLE_SET.includes(role)) {
        this.clearAuth()
        throw new Error('当前账号无管理端访问权限')
      }
      this.setAuth(result)
      return result
    },
    async fetchProfile() {
      const result = await authApi.getProfile()
      const role = result?.role
      if (!ADMIN_ROLE_SET.includes(role)) {
        this.clearAuth()
        throw new Error('当前账号无管理端访问权限')
      }
      this.user = result
      localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(result))
      return result
    }
  }
})
