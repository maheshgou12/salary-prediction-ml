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
    if (password !== confirm) { setError('Passwords do not match'); return }
    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    setLoading(true)
    try {
      const res = await api.resetPassword(token, password)
      setSuccess(res.message)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid or expired token')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary-50 via-white to-secondary-50 px-4 py-12">
      <div className="w-full max-w-md card p-8">
        <h1 className="text-2xl font-bold text-secondary-900 mb-6">Reset password</h1>
        {error && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-danger-50 border border-danger-200 rounded-lg text-danger-700">
            <AlertCircle className="w-5 h-5" /><span className="text-sm">{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-success-50 border border-success-200 rounded-lg text-success-700">
            <CheckCircle className="w-5 h-5" /><span className="text-sm">{success} Redirecting to login...</span>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="password" className="label">New password</label>
            <div className="relative mt-1.5">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
              <input id="password" type="password" required minLength={8} className="input pl-10" value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
          </div>
          <div>
            <label htmlFor="confirm" className="label">Confirm password</label>
            <input id="confirm" type="password" required minLength={8} className="input mt-1.5" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
          </div>
          <button type="submit" disabled={loading || !token} className="btn btn-primary w-full">
            {loading ? 'Updating...' : 'Update password'}
          </button>
        </form>
        <Link to="/login" className="mt-6 inline-block text-sm text-primary-600 hover:text-primary-700">Back to login</Link>
      </div>
    </div>
  )
}
