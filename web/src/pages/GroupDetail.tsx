/** Group detail page — members, splits, expenses, add expense. */

import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import type { GroupDetail as GroupDetailType, ExpenseItem, CreateExpenseSplit } from '@/lib/types'
import { getUserInfo } from '@/lib/auth'
import { UserPlus, ArrowLeft, Plus, Receipt } from 'lucide-react'

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [group, setGroup] = useState<GroupDetailType | null>(null)
  const [expenses, setExpenses] = useState<ExpenseItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showAddMember, setShowAddMember] = useState(false)
  const [memberEmail, setMemberEmail] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [editingSplits, setEditingSplits] = useState(false)
  const [splitValues, setSplitValues] = useState<Record<string, string>>({})
  const [splitError, setSplitError] = useState<string | null>(null)

  const [showAddExpense, setShowAddExpense] = useState(false)
  const [expDesc, setExpDesc] = useState('')
  const [expAmount, setExpAmount] = useState('')
  const [expPaidBy, setExpPaidBy] = useState('')
  const [expSplitMode, setExpSplitMode] = useState<'default' | 'custom'>('default')
  const [expCustomSplits, setExpCustomSplits] = useState<Record<string, string>>({})
  const [expError, setExpError] = useState<string | null>(null)
  const [expLoading, setExpLoading] = useState(false)

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
      const [g, exps] = await Promise.all([
        api.groups.get(id),
        api.expenses.list(id),
      ])
      applyGroup(g)
      setExpenses(exps)
      if (g.members.length > 0 && !expPaidBy) {
        setExpPaidBy(currentUser?.id ?? g.members[0]?.user_id ?? '')
      }
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

  const handleAddExpense = async (e: FormEvent) => {
    e.preventDefault()
    if (!id || !expDesc.trim() || !expAmount) return
    const amount = parseFloat(expAmount)
    if (!amount || amount <= 0) {
      setExpError('Amount must be positive')
      return
    }
    try {
      setExpLoading(true)
      setExpError(null)
      const data: {
        description: string
        amount: number
        paid_by: string
        splits?: CreateExpenseSplit[]
      } = {
        description: expDesc.trim(),
        amount,
        paid_by: expPaidBy,
      }
      if (expSplitMode === 'custom') {
        data.splits = Object.entries(expCustomSplits)
          .filter(([, v]) => parseFloat(v) > 0)
          .map(([uid, v]) => ({ user_id: uid, amount: parseFloat(v) }))
      }
      await api.expenses.create(id, data)
      const exps = await api.expenses.list(id)
      setExpenses(exps)
      setShowAddExpense(false)
      setExpDesc('')
      setExpAmount('')
      setExpSplitMode('default')
      setExpCustomSplits({})
    } catch (err) {
      setExpError(err instanceof Error ? err.message : 'Failed to create expense')
    } finally {
      setExpLoading(false)
    }
  }

  const initCustomSplits = () => {
    if (!group) return
    const amount = parseFloat(expAmount) || 0
    const sv: Record<string, string> = {}
    for (const m of group.members) {
      sv[m.user_id] = String(Math.round(amount * m.default_split_percent / 100 * 100) / 100)
    }
    setExpCustomSplits(sv)
  }

  if (loading) {
    return <p className="text-gray-500 text-center py-12">Loading…</p>
  }

  if (!group) {
    return <p className="text-red-400 text-center py-12">Group not found</p>
  }

  const splitTotal = Object.values(splitValues).reduce((a, b) => a + (parseFloat(b) || 0), 0)
  const customSplitTotal = Object.values(expCustomSplits).reduce((a, b) => a + (parseFloat(b) || 0), 0)

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

      {/* Expenses */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
            Expenses ({expenses.length})
          </h2>
          <Button size="sm" onClick={() => {
            setShowAddExpense(!showAddExpense)
            if (!showAddExpense) initCustomSplits()
          }}>
            <Plus className="w-4 h-4" /> Add
          </Button>
        </div>

        {showAddExpense && (
          <form onSubmit={handleAddExpense} className="mb-4 p-3 rounded-lg border border-gray-800 bg-gray-900/50 space-y-3">
            <div>
              <Label>Description</Label>
              <Input value={expDesc} onChange={(e) => setExpDesc(e.target.value)} placeholder="e.g. Hotel" />
            </div>
            <div>
              <Label>Amount</Label>
              <Input
                type="number"
                step="0.01"
                min="0"
                value={expAmount}
                onChange={(e) => {
                  setExpAmount(e.target.value)
                  if (expSplitMode === 'custom') {
                    const amt = parseFloat(e.target.value) || 0
                    const sv: Record<string, string> = {}
                    for (const m of group.members) {
                      sv[m.user_id] = String(Math.round(amt * m.default_split_percent / 100 * 100) / 100)
                    }
                    setExpCustomSplits(sv)
                  }
                }}
                placeholder="0.00"
              />
            </div>
            <div>
              <Label>Paid by</Label>
              <select
                className="w-full rounded-md border border-gray-700 bg-gray-800 text-white px-3 py-2 text-sm"
                value={expPaidBy}
                onChange={(e) => setExpPaidBy(e.target.value)}
              >
                {group.members.map((m) => (
                  <option key={m.user_id} value={m.user_id}>
                    {m.name}{m.user_id === currentUser?.id ? ' (you)' : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label>Split method</Label>
              <div className="flex gap-2 mt-1">
                <Button
                  type="button"
                  size="sm"
                  variant={expSplitMode === 'default' ? 'default' : 'outline'}
                  onClick={() => setExpSplitMode('default')}
                >
                  Default
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={expSplitMode === 'custom' ? 'default' : 'outline'}
                  onClick={() => { setExpSplitMode('custom'); initCustomSplits() }}
                >
                  Custom
                </Button>
              </div>
            </div>
            {expSplitMode === 'custom' && (
              <div className="space-y-1">
                {group.members.map((m) => (
                  <div key={m.user_id} className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">{m.name}</span>
                    <div className="flex items-center gap-1">
                      <span className="text-gray-500 text-sm">£</span>
                      <Input
                        className="w-24 text-right text-sm"
                        type="number"
                        step="0.01"
                        value={expCustomSplits[m.user_id] ?? ''}
                        onChange={(e) =>
                          setExpCustomSplits((prev) => ({ ...prev, [m.user_id]: e.target.value }))
                        }
                      />
                    </div>
                  </div>
                ))}
                <p className={`text-xs ${Math.abs(customSplitTotal - (parseFloat(expAmount) || 0)) > 0.01 ? 'text-red-400' : 'text-gray-500'}`}>
                  Total: £{customSplitTotal.toFixed(2)} / £{(parseFloat(expAmount) || 0).toFixed(2)}
                </p>
              </div>
            )}
            {expError && <p className="text-red-400 text-xs">{expError}</p>}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={expLoading || !expDesc.trim() || !expAmount}>
                {expLoading ? 'Saving…' : 'Add Expense'}
              </Button>
              <Button type="button" size="sm" variant="outline" onClick={() => setShowAddExpense(false)}>
                Cancel
              </Button>
            </div>
          </form>
        )}

        {expenses.length === 0 ? (
          <div className="text-center py-8">
            <Receipt className="w-10 h-10 text-gray-700 mx-auto mb-2" />
            <p className="text-gray-500 text-sm">No expenses yet</p>
          </div>
        ) : (
          <div className="space-y-2">
            {expenses.map((exp) => (
              <div key={exp.id} className="p-3 rounded-lg border border-gray-800 bg-gray-900">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-white text-sm font-medium">{exp.description}</span>
                  <span className="text-white text-sm font-semibold">£{exp.amount.toFixed(2)}</span>
                </div>
                <p className="text-gray-500 text-xs mb-2">
                  Paid by {exp.paid_by_name} · {new Date(exp.created_at).toLocaleDateString()}
                </p>
                <div className="flex flex-wrap gap-2">
                  {exp.splits.map((s) => (
                    <span key={s.user_id} className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded">
                      {s.user_name}: £{s.amount.toFixed(2)}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
