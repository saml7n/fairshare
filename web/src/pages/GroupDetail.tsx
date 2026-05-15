/** Group detail page — members, splits, balances, expenses, payments. */

import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import type { GroupDetail as GroupDetailType, ExpenseItem, CreateExpenseSplit, BalancesResponse, PaymentItem } from '@/lib/types'
import { getUserInfo } from '@/lib/auth'
import { UserPlus, ArrowLeft, Plus, Receipt, TrendingUp, TrendingDown, ArrowRight, Banknote } from 'lucide-react'

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [group, setGroup] = useState<GroupDetailType | null>(null)
  const [expenses, setExpenses] = useState<ExpenseItem[]>([])
  const [balances, setBalances] = useState<BalancesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [showAddMember, setShowAddMember] = useState(false)
  const [memberEmail, setMemberEmail] = useState('')
  const [addError, setAddError] = useState<string | null>(null)
  const [editingSplits, setEditingSplits] = useState(false)
  const [splitValues, setSplitValues] = useState<Record<string, string>>({})
  const [splitError, setSplitError] = useState<string | null>(null)
  const [splitRetroactive, setSplitRetroactive] = useState(false)
  const [splitUpdateCount, setSplitUpdateCount] = useState<number | null>(null)
  const [showAddExpense, setShowAddExpense] = useState(false)
  const [expDesc, setExpDesc] = useState('')
  const [expAmount, setExpAmount] = useState('')
  const [expPaidBy, setExpPaidBy] = useState('')
  const [expSplitMode, setExpSplitMode] = useState<'default' | 'custom'>('default')
  const [expCustomSplits, setExpCustomSplits] = useState<Record<string, string>>({})
  const [expExcluded, setExpExcluded] = useState<Set<string>>(new Set())
  const [expSplitUnit, setExpSplitUnit] = useState<'amount' | 'percent'>('amount')
  const [expError, setExpError] = useState<string | null>(null)
  const [expLoading, setExpLoading] = useState(false)

  const [payments, setPayments] = useState<PaymentItem[]>([])
  const [showSettle, setShowSettle] = useState(false)
  const [settleTo, setSettleTo] = useState('')
  const [settleAmount, setSettleAmount] = useState('')
  const [settleNote, setSettleNote] = useState('')
  const [settleError, setSettleError] = useState<string | null>(null)
  const [settleLoading, setSettleLoading] = useState(false)

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
      setLoadError(null)
      const [g, exps, bals, pmts] = await Promise.all([
        api.groups.get(id),
        api.expenses.list(id),
        api.balances.get(id),
        api.payments.list(id),
      ])
      applyGroup(g)
      setExpenses(exps)
      setBalances(bals)
      setPayments(pmts)
      if (g.members.length > 0 && !expPaidBy) {
        setExpPaidBy(currentUser?.id ?? g.members[0]?.user_id ?? '')
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to load group'
      if (msg.includes('403')) {
        setLoadError('You are not a member of this group')
      } else if (msg.includes('404')) {
        setLoadError('Group not found')
      } else {
        setLoadError('Failed to load group')
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
      const result = await api.groups.updateSplits(id, splits, splitRetroactive)
      applyGroup(result)
      setEditingSplits(false)
      setSplitRetroactive(false)
      if (result.updated_expenses > 0) {
        setSplitUpdateCount(result.updated_expenses)
        setTimeout(() => setSplitUpdateCount(null), 4000)
        const [exps, bals] = await Promise.all([
          api.expenses.list(id),
          api.balances.get(id),
        ])
        setExpenses(exps)
        setBalances(bals)
      }
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
        if (expSplitUnit === 'percent') {
          if (Math.abs(customSplitTotal - 100) > 0.1) {
            setExpError('Percentages must sum to 100%')
            setExpLoading(false)
            return
          }
          data.splits = Object.entries(expCustomSplits)
            .map(([uid, v]) => ({
              user_id: uid,
              amount: Math.round(parseFloat(v) / 100 * amount * 100) / 100,
            }))
            .filter(s => s.amount > 0)
        } else {
          data.splits = Object.entries(expCustomSplits)
            .filter(([, v]) => parseFloat(v) > 0)
            .map(([uid, v]) => ({ user_id: uid, amount: parseFloat(v) }))
        }
      }
      await api.expenses.create(id, data)
      const [exps, bals, pmts] = await Promise.all([
        api.expenses.list(id),
        api.balances.get(id),
        api.payments.list(id),
      ])
      setExpenses(exps)
      setBalances(bals)
      setPayments(pmts)
      setShowAddExpense(false)
      setExpDesc('')
      setExpAmount('')
      setExpSplitMode('default')
      setExpCustomSplits({})
      setExpExcluded(new Set())
      setExpSplitUnit('amount')
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
    setExpExcluded(new Set())
    setExpSplitUnit('amount')
  }

  const toggleMemberExclusion = (userId: string) => {
    if (!group) return
    const newExcluded = new Set(expExcluded)
    if (newExcluded.has(userId)) {
      newExcluded.delete(userId)
    } else {
      newExcluded.add(userId)
    }
    const includedMembers = group.members.filter(m => !newExcluded.has(m.user_id))
    const totalPct = includedMembers.reduce((sum, m) => sum + m.default_split_percent, 0)
    const amount = parseFloat(expAmount) || 0
    const sv: Record<string, string> = {}
    for (const m of includedMembers) {
      const share = totalPct > 0 ? m.default_split_percent / totalPct : 1 / includedMembers.length
      if (expSplitUnit === 'percent') {
        sv[m.user_id] = String(Math.round(share * 1000) / 10)
      } else {
        sv[m.user_id] = String(Math.round(amount * share * 100) / 100)
      }
    }
    const ids = Object.keys(sv)
    if (ids.length > 1) {
      const lastId = ids[ids.length - 1]!
      const sumOthers = ids.slice(0, -1).reduce((s, k) => s + parseFloat(sv[k] ?? '0'), 0)
      if (expSplitUnit === 'percent') {
        sv[lastId] = String(Math.round((100 - sumOthers) * 10) / 10)
      } else if (amount > 0) {
        sv[lastId] = String(Math.round((amount - sumOthers) * 100) / 100)
      }
    }
    setExpCustomSplits(sv)
    setExpExcluded(newExcluded)
  }

  const switchSplitUnit = (newUnit: 'amount' | 'percent') => {
    if (newUnit === expSplitUnit || !group) return
    const amount = parseFloat(expAmount) || 0
    const sv: Record<string, string> = {}
    for (const m of group.members) {
      if (expExcluded.has(m.user_id)) continue
      const currentVal = parseFloat(expCustomSplits[m.user_id] ?? '0') || 0
      if (newUnit === 'percent') {
        sv[m.user_id] = amount > 0 ? String(Math.round(currentVal / amount * 1000) / 10) : '0'
      } else {
        sv[m.user_id] = String(Math.round(currentVal / 100 * amount * 100) / 100)
      }
    }
    const ids = Object.keys(sv)
    if (ids.length > 1) {
      const lastId = ids[ids.length - 1]!
      const sumOthers = ids.slice(0, -1).reduce((s, k) => s + parseFloat(sv[k] ?? '0'), 0)
      if (newUnit === 'percent') {
        sv[lastId] = String(Math.round((100 - sumOthers) * 10) / 10)
      } else if (amount > 0) {
        sv[lastId] = String(Math.round((amount - sumOthers) * 100) / 100)
      }
    }
    setExpCustomSplits(sv)
    setExpSplitUnit(newUnit)
  }

  const handleSettle = async (e: FormEvent) => {
    e.preventDefault()
    if (!id) return
    setSettleError(null)
    const amount = parseFloat(settleAmount)
    if (!settleTo) { setSettleError('Select a recipient'); return }
    if (!amount || amount <= 0) { setSettleError('Amount must be positive'); return }
    setSettleLoading(true)
    try {
      await api.payments.create(id, {
        to_user_id: settleTo,
        amount,
        note: settleNote || undefined,
      })
      const [bals, pmts] = await Promise.all([
        api.balances.get(id),
        api.payments.list(id),
      ])
      setBalances(bals)
      setPayments(pmts)
      setShowSettle(false)
      setSettleTo('')
      setSettleAmount('')
      setSettleNote('')
    } catch (err) {
      setSettleError(err instanceof Error ? err.message : 'Failed to record payment')
    } finally {
      setSettleLoading(false)
    }
  }

  if (loading) {
    return <p className="text-gray-500 text-center py-12">Loading…</p>
  }

  if (loadError) {
    return <p className="text-red-400 text-center py-12">{loadError}</p>
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
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={splitRetroactive}
                onChange={(e) => setSplitRetroactive(e.target.checked)}
                className="accent-indigo-500"
              />
              Also update past expenses that used the default split
            </label>
            {splitError && <p className="text-red-400 text-xs">{splitError}</p>}
            <div className="flex gap-2">
              <Button size="sm" onClick={handleSaveSplits}>Save</Button>
              <Button size="sm" variant="outline" onClick={() => { setEditingSplits(false); setSplitRetroactive(false) }}>Cancel</Button>
            </div>
          </div>
        )}

        {splitUpdateCount !== null && (
          <p className="text-green-400 text-xs mt-2">{splitUpdateCount} expense(s) updated.</p>
        )}

        {!editingSplits && group.members.length > 1 && (
          <Button size="sm" variant="ghost" className="mt-2" onClick={() => setEditingSplits(true)}>
            Edit splits
          </Button>
        )}
      </div>

      {/* Balances */}
      {balances && (balances.balances.some(b => Math.abs(b.balance) > 0.01)) && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
            Balances
          </h2>
          <div className="space-y-1 mb-3">
            {balances.balances
              .filter(b => Math.abs(b.balance) > 0.01)
              .sort((a, b) => b.balance - a.balance)
              .map((b) => (
              <div key={b.user_id} className="flex items-center justify-between p-2 rounded-lg border border-gray-800 bg-gray-900">
                <div className="flex items-center gap-2">
                  {b.balance > 0 ? (
                    <TrendingUp className="w-4 h-4 text-green-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-sm text-white">{b.name}</span>
                </div>
                <span className={`text-sm font-medium ${b.balance > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {b.balance > 0 ? `+£${b.balance.toFixed(2)}` : `-£${Math.abs(b.balance).toFixed(2)}`}
                </span>
              </div>
            ))}
          </div>
          {balances.simplified_debts.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-gray-500 mb-1">Simplified transfers:</p>
              {balances.simplified_debts.map((d, i) => (
                <div key={i} className="flex items-center gap-2 p-2 rounded-lg border border-gray-800 bg-gray-900/50 text-sm">
                  <span className="text-red-400">{d.from_name}</span>
                  <ArrowRight className="w-3 h-3 text-gray-500" />
                  <span className="text-green-400">{d.to_name}</span>
                  <span className="ml-auto text-white font-medium">£{d.amount.toFixed(2)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settle Up */}
      {balances && balances.simplified_debts.some(d => d.from_user_id === currentUser?.id) && (
        <div className="mb-6">
          {!showSettle ? (
            <Button onClick={() => {
              const myDebt = balances.simplified_debts.find(d => d.from_user_id === currentUser?.id)
              if (myDebt) {
                setSettleTo(myDebt.to_user_id)
                setSettleAmount(String(myDebt.amount))
              }
              setShowSettle(true)
            }}>
              <Banknote className="w-4 h-4 mr-2" />
              Settle Up
            </Button>
          ) : (
            <form onSubmit={handleSettle} className="space-y-3 p-4 rounded-lg border border-gray-800 bg-gray-900">
              <h3 className="text-sm font-medium text-gray-300">Record Payment</h3>
              <div>
                <Label htmlFor="settle-to">Pay to</Label>
                <select
                  id="settle-to"
                  className="w-full mt-1 bg-gray-800 border border-gray-700 rounded-md px-3 py-2 text-sm text-white"
                  value={settleTo}
                  onChange={(e) => setSettleTo(e.target.value)}
                >
                  <option value="">Select member</option>
                  {group.members
                    .filter(m => m.user_id !== currentUser?.id)
                    .map(m => (
                      <option key={m.user_id} value={m.user_id}>{m.name}</option>
                    ))}
                </select>
              </div>
              <div>
                <Label htmlFor="settle-amount">Amount (£)</Label>
                <Input
                  id="settle-amount"
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={settleAmount}
                  onChange={(e) => setSettleAmount(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="settle-note">Note (optional)</Label>
                <Input
                  id="settle-note"
                  value={settleNote}
                  onChange={(e) => setSettleNote(e.target.value)}
                  placeholder="e.g. Bank transfer"
                />
              </div>
              {settleError && <p className="text-red-400 text-sm">{settleError}</p>}
              <div className="flex gap-2">
                <Button type="submit" disabled={settleLoading}>
                  {settleLoading ? 'Recording…' : 'Record Payment'}
                </Button>
                <Button type="button" variant="ghost" onClick={() => { setShowSettle(false); setSettleError(null) }}>
                  Cancel
                </Button>
              </div>
            </form>
          )}
        </div>
      )}

      {/* Payments */}
      {payments.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-medium text-gray-400 uppercase tracking-wider mb-3">
            Payments ({payments.length})
          </h2>
          <div className="space-y-2">
            {payments.map(p => (
              <div key={p.id} className="p-3 rounded-lg border border-gray-800 bg-gray-900/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm">
                    <Banknote className="w-4 h-4 text-green-400" />
                    <span className="text-white">{p.from_name}</span>
                    <ArrowRight className="w-3 h-3 text-gray-500" />
                    <span className="text-white">{p.to_name}</span>
                  </div>
                  <span className="text-green-400 font-medium text-sm">£{p.amount.toFixed(2)}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {p.note && <span>{p.note} · </span>}
                  {new Date(p.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

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
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">£</span>
                <Input
                  className="pl-6"
                  type="number"
                  step="0.01"
                  min="0"
                  value={expAmount}
                  onChange={(e) => {
                    setExpAmount(e.target.value)
                    if (expSplitMode === 'custom' && expSplitUnit !== 'percent') {
                      const amt = parseFloat(e.target.value) || 0
                      const sv: Record<string, string> = {}
                      const includedMembers = group.members.filter(m => !expExcluded.has(m.user_id))
                      const totalPct = includedMembers.reduce((sum, m) => sum + m.default_split_percent, 0)
                      for (const m of includedMembers) {
                        const share = totalPct > 0 ? m.default_split_percent / totalPct : 1 / includedMembers.length
                        sv[m.user_id] = String(Math.round(amt * share * 100) / 100)
                      }
                      const ids = Object.keys(sv)
                      if (ids.length > 1 && amt > 0) {
                        const lastId = ids[ids.length - 1]!
                        const sumOthers = ids.slice(0, -1).reduce((s, k) => s + parseFloat(sv[k] ?? '0'), 0)
                        sv[lastId] = String(Math.round((amt - sumOthers) * 100) / 100)
                      }
                      setExpCustomSplits(sv)
                    }
                  }}
                  placeholder="0.00"
                />
              </div>
            </div>
            <div>
              <Label>Paid by</Label>
              <div className="w-full rounded-md border border-gray-700 bg-gray-800 text-white px-3 py-2 text-sm">
                {group.members.find(m => m.user_id === currentUser?.id)?.name ?? 'You'} (you)
              </div>
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
              <div className="space-y-2">
                <div className="flex gap-1">
                  <Button
                    type="button"
                    size="sm"
                    variant={expSplitUnit === 'amount' ? 'default' : 'outline'}
                    onClick={() => switchSplitUnit('amount')}
                  >£</Button>
                  <Button
                    type="button"
                    size="sm"
                    variant={expSplitUnit === 'percent' ? 'default' : 'outline'}
                    onClick={() => switchSplitUnit('percent')}
                  >%</Button>
                </div>
                {group.members.map((m) => {
                  const excluded = expExcluded.has(m.user_id)
                  return (
                    <div key={m.user_id} className={`flex items-center justify-between ${excluded ? 'opacity-40' : ''}`}>
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={!excluded}
                          onChange={() => toggleMemberExclusion(m.user_id)}
                          className="accent-indigo-500 cursor-pointer"
                        />
                        <span className="text-sm text-gray-300">{m.name}</span>
                      </div>
                      {!excluded && (
                        <div className="flex items-center gap-1">
                          <span className="text-gray-500 text-sm">{expSplitUnit === 'amount' ? '£' : '%'}</span>
                          <Input
                            className="w-24 text-right text-sm"
                            type="number"
                            step={expSplitUnit === 'amount' ? '0.01' : '0.1'}
                            min="0"
                            value={expCustomSplits[m.user_id] ?? ''}
                            onChange={(e) =>
                              setExpCustomSplits((prev) => ({ ...prev, [m.user_id]: e.target.value }))
                            }
                          />
                        </div>
                      )}
                    </div>
                  )
                })}
                {expSplitUnit === 'percent' ? (
                  <p className={`text-xs ${Math.abs(customSplitTotal - 100) > 0.1 ? 'text-red-400' : 'text-gray-500'}`}>
                    Total: {customSplitTotal.toFixed(1)}% / 100%
                  </p>
                ) : (
                  <p className={`text-xs ${Math.abs(customSplitTotal - (parseFloat(expAmount) || 0)) > 0.01 ? 'text-red-400' : 'text-gray-500'}`}>
                    Total: £{customSplitTotal.toFixed(2)} / £{(parseFloat(expAmount) || 0).toFixed(2)}
                  </p>
                )}
              </div>
            )}
            {expError && <p className="text-red-400 text-xs">{expError}</p>}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={
                expLoading || !expDesc.trim() || !expAmount ||
                (expSplitMode === 'custom' && expSplitUnit === 'percent' && Math.abs(customSplitTotal - 100) > 0.1)
              }>
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
