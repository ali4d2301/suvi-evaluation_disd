const API_ROOT = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function readErrorMessage(response) {
  const payload = await response.json().catch(() => null)
  return payload?.detail ?? 'Une erreur est survenue.'
}

async function request(path, options = {}) {
  const headers = new Headers(options.headers ?? {})

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })

  if (!response.ok) {
    throw new ApiError(await readErrorMessage(response), response.status)
  }

  if (response.status === 204) {
    return null
  }

  return response.json()
}

export async function login(username, password) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  })
}

export async function fetchCurrentUser() {
  return request('/api/auth/me')
}

export async function logout() {
  return request('/api/auth/logout', {
    method: 'POST',
  })
}

export async function fetchDashboard() {
  return request('/api/dashboard')
}

export async function fetchUsers() {
  return request('/api/users')
}

export async function createUser(payload) {
  return request('/api/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateUser(userId, payload) {
  return request(`/api/users/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}

export async function updateUserPassword(userId, password) {
  return request(`/api/users/${userId}/password`, {
    method: 'POST',
    body: JSON.stringify({ password }),
  })
}
