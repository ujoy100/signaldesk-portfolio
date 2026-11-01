const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status = 0, correlationId = null) { super(message); this.status = status; this.correlationId = correlationId }
}

export async function apiRequest(path, token, options = {}) {
  const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), 30000)
  try {
    const csrf = document.cookie.split('; ').find((item) => item.startsWith('signaldesk_csrf='))?.split('=')[1]
    const response = await fetch(`${API_BASE}${path}`, { ...options, credentials: 'include', signal: controller.signal, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(csrf && !['GET', 'HEAD'].includes(options.method || 'GET') ? { 'X-CSRF-Token': decodeURIComponent(csrf) } : {}), ...options.headers } })
    const correlationId = response.headers.get('X-Correlation-ID'); const body = await response.json().catch(() => ({}))
    if (!response.ok) throw new ApiError(body.detail || 'Request failed', response.status, correlationId)
    return body
  } catch (error) {
    if (error.name === 'AbortError') throw new ApiError('Request timed out')
    if (error instanceof ApiError) throw error
    throw new ApiError('Backend unavailable')
  } finally { clearTimeout(timer) }
}

export const operationsApi = {
  session: (token) => apiRequest('/api/v1/session', token),
  submitIssue: (token, payload) => apiRequest('/api/v1/support/issues', token, { method: 'POST', body: JSON.stringify(payload) }),
  approvals: (token) => apiRequest('/api/v1/approvals', token),
  decide: (token, id, payload) => apiRequest(`/api/v1/approvals/${id}/decisions`, token, { method: 'POST', body: JSON.stringify(payload) }),
  decideKnowledge: (token, id, payload) => apiRequest(`/api/v1/knowledge/promotion-approvals/${id}/decisions`, token, { method: 'POST', body: JSON.stringify(payload) }),
  requestPromotion: (token, versionId, threadId) => apiRequest(`/api/v1/knowledge/versions/${versionId}/promotion-requests`, token, { method: 'POST', body: JSON.stringify({ thread_id: threadId }) }),
  promote: (token, versionId, approvalId, executionRequestId) => apiRequest(`/api/v1/knowledge/versions/${versionId}/promote`, token, { method: 'POST', body: JSON.stringify({ approval_id: approvalId, execution_request_id: executionRequestId }) }),
  evaluations: (token) => apiRequest('/api/v1/evaluations', token),
  knowledge: (token) => apiRequest('/api/v1/knowledge/versions', token),
  submitFeedback: (token, payload) => apiRequest('/api/v1/feedback', token, { method: 'POST', body: JSON.stringify(payload) }),
  feedback: (token) => apiRequest('/api/v1/feedback', token),
  logout: () => apiRequest('/auth/logout', null, { method: 'POST' }),
}

export const microsoftLoginUrl = `${API_BASE}/auth/login`
