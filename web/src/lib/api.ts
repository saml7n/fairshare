/** API client for the FairShare backend. */

import { getToken } from './auth'

const API_BASE = import.meta.env.VITE_API_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })

  if (res.status === 401) {
    const isAuthEndpoint = path.startsWith('/api/auth/')
    if (!isAuthEndpoint) {
      const { clearToken } = await import('./auth')
      clearToken()
      if (
        typeof window !== 'undefined' &&
        !window.location.pathname.startsWith('/login') &&
        !window.location.pathname.startsWith('/register')
      ) {
        window.location.href = '/login'
      }
    }
  }

  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status}: ${body}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

import type { CreateExpenseSplit, ExpenseItem, GroupDetail, GroupListItem, UserSearchResult } from './types'

export const api = {
  auth: {
    register: (email: string, password: string, name: string) =>
      request<{ ok: boolean; token: string; user: { id: string; email: string; name: string } | null }>('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string) =>
      request<{ ok: boolean; token: string; user: { id: string; email: string; name: string } | null }>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    me: () => request<{ id: string; email: string; name: string }>('/api/auth/me'),
  },
  groups: {
    list: () => request<GroupListItem[]>('/api/groups'),
    get: (id: string) => request<GroupDetail>(`/api/groups/${id}`),
    create: (name: string, memberEmails: string[] = []) =>
      request<GroupDetail>('/api/groups', {
        method: 'POST',
        body: JSON.stringify({ name, member_emails: memberEmails }),
      }),
    addMember: (groupId: string, email: string) =>
      request<GroupDetail>(`/api/groups/${groupId}/members`, {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    updateSplits: (groupId: string, splits: Record<string, number>) =>
      request<GroupDetail>(`/api/groups/${groupId}/splits`, {
        method: 'PUT',
        body: JSON.stringify({ splits }),
      }),
  },
  expenses: {
    list: (groupId: string) =>
      request<ExpenseItem[]>(`/api/groups/${groupId}/expenses`),
    create: (groupId: string, data: {
      description: string
      amount: number
      paid_by: string
      splits?: CreateExpenseSplit[]
    }) =>
      request<ExpenseItem>(`/api/groups/${groupId}/expenses`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
  users: {
    search: (q: string) => request<UserSearchResult[]>(`/api/users/search?q=${encodeURIComponent(q)}`),
  },
}
