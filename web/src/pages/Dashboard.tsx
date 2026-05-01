/** Dashboard — cross-group financial summary. */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import type { DashboardData } from '@/lib/types'
import { TrendingUp, TrendingDown, ArrowRight, Users } from 'lucide-react'

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.dashboard.get()
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <p className="text-gray-500 text-center py-12">Loading…</p>
  }

  if (!data) {
    return <p className="text-red-400 text-center py-12">Failed to load dashboard</p>
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6 space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white mb-1">Dashboard</h1>
        <p className="text-gray-500 text-sm">Your financial summary across all groups.</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-lg border border-gray-800 bg-gray-900 text-center">
          <p className="text-xs text-gray-500 mb-1">Owed to you</p>
          <p className="text-lg font-bold text-green-400">£{data.total_owed_to_you.toFixed(2)}</p>
        </div>
        <div className="p-3 rounded-lg border border-gray-800 bg-gray-900 text-center">
          <p className="text-xs text-gray-500 mb-1">You owe</p>
          <p className="text-lg font-bold text-red-400">£{data.total_you_owe.toFixed(2)}</p>
        </div>
        <div className="p-3 rounded-lg border border-gray-800 bg-gray-900 text-center">
          <p className="text-xs text-gray-500 mb-1">Net</p>
          <p className={`text-lg font-bold ${data.net_position >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {data.net_position >= 0 ? '+' : ''}£{data.net_position.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Groups list */}
      <div>
        <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
          Your Groups ({data.groups.length})
        </h2>
        {data.groups.length === 0 ? (
          <p className="text-gray-600 text-sm">
            No groups yet. <button onClick={() => navigate('/groups/new')} className="text-indigo-400 underline">Create one</button>
          </p>
        ) : (
          <div className="space-y-2">
            {data.groups.map(g => (
              <button
                key={g.group_id}
                onClick={() => navigate(`/groups/${g.group_id}`)}
                className="w-full text-left p-3 rounded-lg border border-gray-800 bg-gray-900 hover:border-indigo-600 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-white font-medium">{g.group_name}</p>
                    <div className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
                      <Users className="w-3 h-3" />
                      <span>{g.member_count} members</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {Math.abs(g.balance) > 0.01 ? (
                      <>
                        {g.balance > 0 ? (
                          <TrendingUp className="w-4 h-4 text-green-400" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-400" />
                        )}
                        <span className={`font-medium ${g.balance > 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {g.balance > 0 ? '+' : ''}£{g.balance.toFixed(2)}
                        </span>
                      </>
                    ) : (
                      <span className="text-gray-500 text-sm">Settled</span>
                    )}
                    <ArrowRight className="w-4 h-4 text-gray-600" />
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
