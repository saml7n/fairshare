/** Register page — email + password + name.
 *
 * parbaked migration: signup creates a *pending* user. No JWT is issued
 * until an admin approves the account at /auth/admin (the parbaked
 * dashboard). The previous invite-code gate is gone — admin approval
 * is the new gate.
 */

import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'

export default function Register() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [pending, setPending] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password || !name.trim()) return

    try {
      setLoading(true)
      setError(null)
      // parbaked's signup: invite code arg is ignored after the migration —
      // pass empty string. Response is {user_id, status, email_sent}; no JWT.
      await api.auth.register(email.trim(), password, name.trim(), '')
      setPending(true)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      if (msg.includes('409')) {
        setError('Email already registered')
      } else if (msg.includes('422')) {
        setError('Check your email + password (8+ characters)')
      } else if (msg.includes('429')) {
        setError('Too many attempts — please try again later')
      } else {
        setError('Registration failed — please try again')
      }
    } finally {
      setLoading(false)
    }
  }

  if (pending) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center px-4">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8">
            <h1 className="text-white font-bold text-2xl mb-2">FairShare</h1>
            <p className="text-gray-300 text-base mb-2">Account created.</p>
            <p className="text-gray-500 text-sm">
              Your account is pending approval. You'll be able to sign in
              once an admin approves it.
            </p>
          </div>
          <p className="text-gray-500 text-sm text-center mt-6">
            <Link to="/login" className="text-indigo-400 hover:text-indigo-300 transition">
              Back to sign in
            </Link>
          </p>
        </div>
      </div>
    )
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

          {error && <p className="text-red-400 text-sm" data-testid="register-error">{error}</p>}

          <Button
            type="submit"
            disabled={loading || !email.trim() || !password || !name.trim()}
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
