/** Create a new group. */

import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'

export default function CreateGroup() {
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return

    try {
      setLoading(true)
      setError(null)
      const group = await api.groups.create(name.trim())
      navigate(`/groups/${group.id}`)
    } catch {
      setError('Failed to create group')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-white mb-6">Create Group</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="name">Group Name</Label>
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Trip to Paris"
            autoFocus
          />
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <div className="flex gap-2">
          <Button type="submit" disabled={loading || !name.trim()}>
            {loading ? 'Creating…' : 'Create Group'}
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate('/groups')}>
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
