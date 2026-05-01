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
