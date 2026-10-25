import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { Mail, AlertCircle, CheckCircle, ArrowLeft } from 'lucide-react'

export function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    try {
      const res = await api.forgotPassword(email)
      setSuccess(res.message || 'If that email is registered, a password reset link has been sent to your email inbox.')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong. Please check your email address.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary-50 via-white to-secondary-50 dark:from-secondary-950 dark:via-secondary-900 dark:to-secondary-950 px-4 py-12 transition-colors">
      <div className="w-full max-w-md card p-8 bg-white/95 dark:bg-secondary-900/90 dark:border-secondary-800 backdrop-blur-sm shadow-xl">
        <h1 className="text-2xl font-bold text-secondary-900 dark:text-white mb-2">Forgot password</h1>
        <p className="text-secondary-600 dark:text-secondary-400 mb-6 text-sm">
          Enter your registered email address and we'll send you a password reset link.
        </p>

        {error && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-danger-50 dark:bg-danger-900/30 border border-danger-200 dark:border-danger-800 rounded-lg text-danger-700 dark:text-danger-300">
            <AlertCircle className="w-5 h-5 flex-shrink-0" /><span className="text-sm">{error}</span>
          </div>
        )}

        {success && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-success-50 dark:bg-success-900/30 border border-success-200 dark:border-success-800 rounded-lg text-success-800 dark:text-success-200">
            <CheckCircle className="w-5 h-5 flex-shrink-0 text-success-600 dark:text-success-400" />
            <span className="text-sm font-medium">{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="label dark:text-secondary-300">Email address</label>
            <div className="relative mt-1.5">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
              <input
                id="email"
                type="email"
                required
                className="input pl-10 dark:bg-secondary-800/80 dark:border-secondary-700 dark:text-white dark:placeholder-secondary-500"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
              />
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary w-full">
            {loading ? 'Sending...' : 'Send reset link'}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-secondary-100 dark:border-secondary-800 text-center">
          <Link to="/login" className="inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300">
            <ArrowLeft className="w-4 h-4 mr-1" /> Back to login
          </Link>
        </div>
      </div>
    </div>
  )
}
