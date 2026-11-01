
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

async function fetchStatus(path) {
  if (!API_BASE_URL) {
    throw new Error('VITE_API_BASE_URL is not configured')
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'GET',
    headers: {
      Accept: 'application/json',
    },
    signal: AbortSignal.timeout(5000),
  })

  if (!response.ok) {
    const error = new Error(
      `Request to ${path} failed: HTTP ${response.status}`,
    )
    error.status = response.status
    throw error
  }

  return response.json()
}

export function fetchHealth() {
  return fetchStatus('/health')
}

export function fetchReadiness() {
  return fetchStatus('/ready')
}
