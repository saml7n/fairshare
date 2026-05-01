/** Shared types matching the backend API responses. */

export interface GroupMember {
  id: string
  user_id: string
  email: string
  name: string
  default_split_percent: number
}

export interface GroupDetail {
  id: string
  name: string
  created_by: string
  members: GroupMember[]
  created_at: string
}

export interface GroupListItem {
  id: string
  name: string
  member_count: number
  created_at: string
}

export interface UserSearchResult {
  id: string
  email: string
  name: string
}

export interface ExpenseSplit {
  user_id: string
  user_name: string
  user_email: string
  amount: number
}

export interface ExpenseItem {
  id: string
  description: string
  amount: number
  paid_by: string
  paid_by_name: string
  splits: ExpenseSplit[]
  created_at: string
}

export interface CreateExpenseSplit {
  user_id: string
  amount: number
}

export interface MemberBalance {
  user_id: string
  name: string
  email: string
  balance: number
}

export interface SimplifiedDebt {
  from_user_id: string
  from_name: string
  to_user_id: string
  to_name: string
  amount: number
}

export interface BalancesResponse {
  balances: MemberBalance[]
  simplified_debts: SimplifiedDebt[]
}
