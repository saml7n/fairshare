/** Register page — email + password + name. */

import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import { setToken } from '@/lib/auth'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password || !name.trim() || !inviteCode.trim()) return

    try {
      setLoading(true)
      setError(null)
      const res = await api.auth.register(email.trim(), password, name.trim(), inviteCode.trim())
      setToken(res.token)
      navigate('/')
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      if (msg.includes('409')) {
        setError('Email already registered')
      } else if (msg.includes('400')) {
        setError('Password must be at least 8 characters')
      } else if (msg.includes('403')) {
        setError('Invalid invite code')
      } else if (msg.includes('429')) {
        setError('Too many attempts — please try again later')
      } else {
        setError('Registration failed — please try again')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <h1 className="text-white font-bold text-2xl mb-2">FairShare</h1>
          <p className="text-gray-500 text-sm">Create your account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4" data-testid="register-form">
          <div>
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              autoFocus
              autoComplete="name"
              data-testid="register-name"
            />
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              data-testid="register-email"
            />
          </div>
          <div>
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 characters"
              autoComplete="new-password"
              data-testid="register-password"
            />
          </div>
          <div>
            <Label htmlFor="invite-code">Invite Code</Label>
            <Input
              id="invite-code"
              type="password"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              placeholder="Enter the invite code"
              autoComplete="off"
              data-testid="register-invite-code"
            />
          </div>

          {error && <p className="text-red-400 text-sm" data-testid="register-error">{error}</p>}

          <Button
            type="submit"
            disabled={loading || !email.trim() || !password || !name.trim() || !inviteCode.trim()}
            className="w-full"
            data-testid="register-submit"
          >
            {loading ? 'Creating account…' : 'Create Account'}
          </Button>
        </form>

        <p className="text-gray-500 text-sm text-center mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300 transition">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
