export const STORAGE_KEYS = {
  token: 'canteen_admin_token',
  user: 'canteen_admin_user'
}

export const APP_TITLE = '校园食堂管理后台'
export const BASE_URL = import.meta.env.VITE_API_BASE_URL || ''
export const ASSET_BASE_URL = import.meta.env.VITE_ASSET_BASE_URL || 'http://localhost:8000'
export const ADMIN_ROLE_SET = ['admin', 'sys_admin', 'merchant', 'canteen_admin']
