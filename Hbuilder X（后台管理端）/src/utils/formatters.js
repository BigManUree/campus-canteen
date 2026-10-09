export function normalizeListPayload(payload) {
  const source = payload?.data && !Array.isArray(payload.data) ? payload.data : payload

  if (Array.isArray(source)) {
    return {
      items: source,
      total: source.length,
      page: 1,
      pageSize: source.length,
      totalPages: 1
    }
  }

  const items = source?.records || source?.items || source?.list || source?.rows || (Array.isArray(source?.data) ? source.data : []) || []
  return {
    items,
    total: source?.total || source?.count || source?.total_count || items.length || 0,
    page: source?.pageNum || source?.page || source?.current_page || 1,
    pageSize: source?.pageSize || source?.page_size || source?.per_page || items.length || 10,
    totalPages: source?.totalPages || source?.total_pages || 0
  }
}

export function firstOf(source, keys, fallback = '-') {
  for (const key of keys) {
    const value = source?.[key]
    if (value !== undefined && value !== null && value !== '') {
      return value
    }
  }
  return fallback
}

export function toNumber(value, fallback = 0) {
  const amount = Number(value)
  return Number.isFinite(amount) ? amount : fallback
}

export function pickAmount(source, keys, fallback = 0) {
  return toNumber(firstOf(source, keys, fallback), fallback)
}

export function pickText(source, keys, fallback = '-') {
  return String(firstOf(source, keys, fallback))
}

export function normalizeStatus(value, map = {}, fallback = '未知') {
  return map[value] || fallback
}

export function currency(value) {
  const amount = toNumber(value)
  return amount.toFixed(2)
}

export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  const pad = (num) => String(num).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function normalizeBooleanStatus(value, trueValues = [1, true, 'enabled', 'active', 'online', 'on_sale']) {
  return trueValues.includes(value)
}
