/** Auth token management using localStorage with JWT support. */

const TOKEN_KEY = 'fairshare_token'

export interface UserInfo {
  id: string
  email: string
  name: string
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

function decodePayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = atob(parts[1]!.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(payload) as Record<string, unknown>
  } catch {
    return null
  }
}

export function isAuthenticated(): boolean {
  const token = getToken()
  if (!token) return false
  const payload = decodePayload(token)
  if (!payload || !payload.exp) return true
  const expiry = (payload.exp as number) * 1000
  if (Date.now() >= expiry) {
    clearToken()
    return false
  }
  return true
}

export function getUserInfo(): UserInfo | null {
  const token = getToken()
  if (!token) return null
  const payload = decodePayload(token)
  if (!payload || !payload.sub) return null
  return {
    id: payload.sub as string,
    email: (payload.email as string) || '',
    name: (payload.name as string) || '',
  }
}
