/** Group detail page — members, splits, add member. */

import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import type { GroupDetail as GroupDetailType } from '@/lib/types'
import { getUserInfo } from '@/lib/auth'
import { UserPlus, ArrowLeft } from 'lucide-react'

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [group, setGroup] = useState<GroupDetailType | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAddMember, setShowAddMember] = useState(false)
  const [memberEmail, setMemberEmail] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [editingSplits, setEditingSplits] = useState(false)
  const [splitValues, setSplitValues] = useState<Record<string, string>>({})
  const [splitError, setSplitError] = useState<string | null>(null)

  const currentUser = getUserInfo()

  const applyGroup = (g: GroupDetailType) => {
    setGroup(g)
    const sv: Record<string, string> = {}
    for (const m of g.members) {
      sv[m.user_id] = String(m.default_split_percent)
    }
    setSplitValues(sv)
  }

  const loadGroup = useCallback(async () => {
    if (!id) return
    try {
      const g = await api.groups.get(id)
      applyGroup(g)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    loadGroup()
  }, [loadGroup])

  const handleAddMember = async () => {
    if (!id || !memberEmail.trim()) return
    try {
      setAddError(null)
      const g = await api.groups.addMember(id, memberEmail.trim())
      applyGroup(g)
      setMemberEmail('')
      setShowAddMember(false)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed'
      if (msg.includes('404')) setAddError('User not found — they must register first')
      else if (msg.includes('409')) setAddError('Already a member')
      else setAddError('Failed to add member')
    }
  }

  const handleSaveSplits = async () => {
    if (!id) return
    const splits: Record<string, number> = {}
    for (const [uid, val] of Object.entries(splitValues)) {
      splits[uid] = parseFloat(val) || 0
    }
    const total = Object.values(splits).reduce((a, b) => a + b, 0)
    if (Math.abs(total - 100) > 0.1) {
      setSplitError(`Splits must sum to 100% (currently ${total.toFixed(1)}%)`)
      return
    }
    try {
      setSplitError(null)
      const g = await api.groups.updateSplits(id, splits)
      applyGroup(g)
      setEditingSplits(false)
    } catch {
      setSplitError('Failed to update splits')
    }
  }

  if (loading) {
    return <p className="text-gray-500 text-center py-12">Loading…</p>
  }

  if (!group) {
    return <p className="text-red-400 text-center py-12">Group not found</p>
  }

  const splitTotal = Object.values(splitValues).reduce((a, b) => a + (parseFloat(b) || 0), 0)

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <button onClick={() => navigate('/groups')} className="flex items-center text-gray-400 hover:text-white text-sm mb-4 transition">
        <ArrowLeft className="w-4 h-4 mr-1" /> Groups
      </button>

      <h1 className="text-xl font-bold text-white mb-6">{group.name}</h1>

      {/* Members */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
            Members ({group.members.length})
          </h2>
          <Button size="sm" variant="ghost" onClick={() => setShowAddMember(!showAddMember)}>
            <UserPlus className="w-4 h-4" />
          </Button>
        </div>

        {showAddMember && (
          <div className="mb-4 p-3 rounded-lg border border-gray-800 bg-gray-900/50 space-y-2">
            <Label>Add member by email</Label>
            <div className="flex gap-2">
              <Input
                value={memberEmail}
                onChange={(e) => setMemberEmail(e.target.value)}
                placeholder="user@example.com"
                onKeyDown={(e) => e.key === 'Enter' && handleAddMember()}
              />
              <Button size="sm" onClick={handleAddMember} disabled={!memberEmail.trim()}>
                Add
              </Button>
            </div>
            {addError && <p className="text-red-400 text-xs">{addError}</p>}
          </div>
        )}

        <div className="space-y-1">
          {group.members.map((m) => (
            <div
              key={m.user_id}
              className="flex items-center justify-between p-3 rounded-lg border border-gray-800 bg-gray-900"
            >
              <div>
                <span className="text-white text-sm font-medium">
                  {m.name}
                  {m.user_id === currentUser?.id && (
                    <span className="text-indigo-400 ml-1 text-xs">(you)</span>
                  )}
                </span>
                <p className="text-gray-500 text-xs">{m.email}</p>
              </div>
              {editingSplits ? (
                <div className="flex items-center gap-1">
                  <Input
                    className="w-20 text-right text-sm"
                    value={splitValues[m.user_id] ?? ''}
                    onChange={(e) =>
                      setSplitValues((prev) => ({ ...prev, [m.user_id]: e.target.value }))
                    }
                  />
                  <span className="text-gray-500 text-sm">%</span>
                </div>
              ) : (
                <span className="text-gray-400 text-sm">{m.default_split_percent}%</span>
              )}
            </div>
          ))}
        </div>

        {editingSplits && (
          <div className="mt-2 space-y-2">
            <p className={`text-xs ${Math.abs(splitTotal - 100) > 0.1 ? 'text-red-400' : 'text-gray-500'}`}>
              Total: {splitTotal.toFixed(1)}%
            </p>
            {splitError && <p className="text-red-400 text-xs">{splitError}</p>}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveSplits}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => setEditingSplits(false)}>Cancel</Button>
            </div>
          </div>
        )}

        {!editingSplits && group.members.length > 1 && (
          <Button size="sm" variant="ghost" className="mt-2" onClick={() => setEditingSplits(true)}>
            Edit splits
          </Button>
        )}
      </div>
    </div>
  )
}
