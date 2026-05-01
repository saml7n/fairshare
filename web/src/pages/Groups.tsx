/** Groups list page. */

import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import type { GroupListItem } from '@/lib/types'
import { Users, Plus } from 'lucide-react'

export default function Groups() {
  const [groups, setGroups] = useState<GroupListItem[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.groups.list().then(setGroups).finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-white">Groups</h1>
        <Button size="sm" onClick={() => navigate('/groups/new')}>
          <Plus className="w-4 h-4" /> New Group
        </Button>
      </div>

      {loading ? (
        <p className="text-gray-500 text-center py-8">Loading…</p>
      ) : groups.length === 0 ? (
        <div className="text-center py-12">
          <Users className="w-12 h-12 text-gray-700 mx-auto mb-3" />
          <p className="text-gray-500">No groups yet</p>
          <p className="text-gray-600 text-sm mt-1">Create one to start splitting expenses</p>
        </div>
      ) : (
        <div className="space-y-2">
          {groups.map((g) => (
            <Link
              key={g.id}
              to={`/groups/${g.id}`}
              className="block rounded-lg border border-gray-800 bg-gray-900 p-4 hover:border-gray-700 transition"
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-white">{g.name}</span>
                <span className="text-xs text-gray-500">
                  {g.member_count} member{g.member_count !== 1 ? 's' : ''}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
