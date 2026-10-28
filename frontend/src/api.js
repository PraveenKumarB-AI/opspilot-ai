// All calls to the FastAPI back end. Pages never call fetch() directly.
const BASE = '/api'
const DOWN = "OpsPilot's server isn't responding. Your text is still here: try again in a minute, or tell IT."

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(BASE + path, { headers: { 'Content-Type': 'application/json' }, ...options })
  } catch {
    throw new Error(DOWN) // network failure: the API or the proxy is unreachable
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    if (res.status >= 500 || !body) throw new Error(DOWN)
    if (Array.isArray(body.detail)) {
      // 422 from FastAPI: name the field, e.g. "body: String should have at most 5000 characters"
      throw new Error(body.detail.map((d) => `${d.loc?.at(-1) ?? 'input'}: ${d.msg}`).join('; '))
    }
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  // Tell the rest of the app (e.g. the sidebar counts) that data changed after any write.
  if (options.method && options.method !== 'GET') window.dispatchEvent(new Event('opspilot:changed'))
  return res.json()
}

export const api = {
  health: () => request('/health'),
  samples: () => request('/samples'),
  createRequest: (data) => request('/requests', { method: 'POST', body: JSON.stringify(data) }),
  listRequests: (params = {}) => request('/requests?' + new URLSearchParams(params)),
  getRequest: (id) => request(`/requests/${encodeURIComponent(id)}`),
  review: (id, data) => request(`/requests/${encodeURIComponent(id)}/review`, { method: 'POST', body: JSON.stringify(data) }),
  metrics: () => request('/metrics'),
  audit: () => request('/audit'),
  addTiming: (data) => request('/baseline', { method: 'POST', body: JSON.stringify(data) }),
}
