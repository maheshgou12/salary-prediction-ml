import { useState } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import { Lock, AlertCircle, CheckCircle } from 'lucide-react'

export function ResetPassword() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    setLoading(true)
    try {
      const res = await api.resetPassword(token, password)
      setSuccess(res.message || 'Password updated successfully!')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid or expired reset token')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary-50 via-white to-secondary-50 dark:from-secondary-950 dark:via-secondary-900 dark:to-secondary-950 px-4 py-12 transition-colors">
      <div className="w-full max-w-md card p-8 bg-white/95 dark:bg-secondary-900/90 dark:border-secondary-800 backdrop-blur-sm shadow-xl">
        <h1 className="text-2xl font-bold text-secondary-900 dark:text-white mb-2">Create new password</h1>
        <p className="text-secondary-600 dark:text-secondary-400 mb-6 text-sm">
          Enter your new password below to secure your account.
        </p>

        {error && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-danger-50 dark:bg-danger-900/30 border border-danger-200 dark:border-danger-800 rounded-lg text-danger-700 dark:text-danger-300">
            <AlertCircle className="w-5 h-5 flex-shrink-0" /><span className="text-sm">{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-success-50 dark:bg-success-900/30 border border-success-200 dark:border-success-800 rounded-lg text-success-800 dark:text-success-200">
            <CheckCircle className="w-5 h-5 flex-shrink-0 text-success-600 dark:text-success-400" />
            <span className="text-sm font-medium">{success} Redirecting to login...</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="password" className="label dark:text-secondary-300">New password</label>
            <div className="relative mt-1.5">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
              <input
                id="password"
                type="password"
                required
                minLength={6}
                className="input pl-10 dark:bg-secondary-800/80 dark:border-secondary-700 dark:text-white"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
              />
            </div>
          </div>

          <div>
            <label htmlFor="confirm" className="label dark:text-secondary-300">Confirm password</label>
            <input
              id="confirm"
              type="password"
              required
              minLength={6}
              className="input mt-1.5 dark:bg-secondary-800/80 dark:border-secondary-700 dark:text-white"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Re-enter your new password"
            />
          </div>

          <button type="submit" disabled={loading || !token} className="btn btn-primary w-full">
            {loading ? 'Updating...' : 'Update password'}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-secondary-100 dark:border-secondary-800 text-center">
          <Link to="/login" className="inline-block text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300">
            Back to login
          </Link>
        </div>
      </div>
    </div>
  )
}
