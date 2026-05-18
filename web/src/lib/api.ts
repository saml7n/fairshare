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
    // parbaked owns /auth/* — don't bounce the user on 401s from those
    // endpoints (e.g. wrong-password login) since they handle their own
    // error UX inline.
    const isAuthEndpoint = path.startsWith('/auth/')
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

import type { BalancesResponse, CreateExpenseSplit, DashboardData, ExpenseItem, GroupDetail, GroupListItem, PaymentItem, UpdateSplitsResponse, UserSearchResult } from './types'

export const api = {
  auth: {
    // parbaked's /auth/signup creates a pending user — the admin must
    // approve before login works. The legacy invite-code gate is gone;
    // the admin queue at /auth/admin is the new gate.
    register: (email: string, password: string, name: string, _inviteCode: string) =>
      request<{ user_id: string; status: string; email_sent: boolean }>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
      }),
    login: (email: string, password: string) =>
      request<{ token: string; user: { id: string; email: string; name: string; status: string } }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }),
    me: () => request<{ id: string; email: string; name: string }>('/auth/me'),
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
    updateSplits: (groupId: string, splits: Record<string, number>, retroactive = false) =>
      request<UpdateSplitsResponse>(`/api/groups/${groupId}/splits`, {
        method: 'PUT',
        body: JSON.stringify({ splits, retroactive }),
      }),
  },
  dashboard: {
    get: () => request<DashboardData>('/api/dashboard'),
  },
  balances: {
    get: (groupId: string) =>
      request<BalancesResponse>(`/api/groups/${groupId}/balances`),
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
  payments: {
    list: (groupId: string) =>
      request<PaymentItem[]>(`/api/groups/${groupId}/payments`),
    create: (groupId: string, data: {
      to_user_id: string
      amount: number
      note?: string
    }) =>
      request<PaymentItem>(`/api/groups/${groupId}/payments`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
  users: {
    search: (q: string) => request<UserSearchResult[]>(`/api/users/search?q=${encodeURIComponent(q)}`),
  },
}
