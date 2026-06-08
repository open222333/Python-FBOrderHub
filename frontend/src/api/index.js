import { useAuthStore } from '@/stores/auth'

/**
 * 帶 JWT 的 fetch，401 時自動嘗試用 Refresh Token 換發後重試一次。
 */
async function apiFetch(path, options = {}, _retry = true) {
  const auth = useAuthStore()
  const res  = await fetch(path, {
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${auth.token}` },
    ...options,
  })

  if (res.status === 401 && _retry) {
    const ok = await auth.tryRefresh()
    if (ok) return apiFetch(path, options, false)
    auth.clearAuth()
    return null
  }
  return res
}

// ── 使用者 & 模板 API ────────────────────────────────────────────
export const userApi = {
  list:           ()         => apiFetch('/user/'),
  create:         (data)     => apiFetch('/user/',                 { method: 'POST',   body: JSON.stringify(data) }),
  update:         (id, data) => apiFetch(`/user/${id}`,           { method: 'PUT',    body: JSON.stringify(data) }),
  remove:         (id)       => apiFetch(`/user/${id}`,           { method: 'DELETE' }),

  listTemplates:  ()         => apiFetch('/user/templates/'),
  createTemplate: (data)     => apiFetch('/user/templates/',       { method: 'POST',   body: JSON.stringify(data) }),
  updateTemplate: (id, data) => apiFetch(`/user/templates/${id}`, { method: 'PUT',    body: JSON.stringify(data) }),
  removeTemplate: (id)       => apiFetch(`/user/templates/${id}`, { method: 'DELETE' }),
}

// ── 操作紀錄 API ─────────────────────────────────────────────────
export const logApi = {
  list: () => apiFetch('/log/'),
}

// ── 產品 API ─────────────────────────────────────────────────────
export const productApi = {
  list:      (status)        => apiFetch(`/product/${status ? `?status=${status}` : ''}`),
  get:       (id)            => apiFetch(`/product/${id}`),
  create:    (data)          => apiFetch('/product/',          { method: 'POST',  body: JSON.stringify(data) }),
  update:    (id, data)      => apiFetch(`/product/${id}`,     { method: 'PUT',   body: JSON.stringify(data) }),
  remove:    (id)            => apiFetch(`/product/${id}`,     { method: 'DELETE' }),
  setStatus: (id, status)    => apiFetch(`/product/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
}

// ── FB API ───────────────────────────────────────────────────────
export const fbApi = {
  listTemplates:  ()         => apiFetch('/fb/templates/'),
  createTemplate: (data)     => apiFetch('/fb/templates/',       { method: 'POST',   body: JSON.stringify(data) }),
  updateTemplate: (id, data) => apiFetch(`/fb/templates/${id}`,  { method: 'PUT',    body: JSON.stringify(data) }),
  deleteTemplate: (id)       => apiFetch(`/fb/templates/${id}`,  { method: 'DELETE' }),
  post:           (message, group_id) => apiFetch('/fb/post', {
    method: 'POST',
    body: JSON.stringify({ message, ...(group_id ? { group_id } : {}) }),
  }),
}

// ── 訂單 API ─────────────────────────────────────────────────────
export const orderApi = {
  list:         (status)       => apiFetch(`/order/${status ? `?status=${status}` : ''}`),
  get:          (id)           => apiFetch(`/order/${id}`),
  updateStatus: (id, status)   => apiFetch(`/order/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
}
