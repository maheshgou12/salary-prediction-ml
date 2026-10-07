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
      setSuccess(res.message)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary-50 via-white to-secondary-50 px-4 py-12">
      <div className="w-full max-w-md card p-8">
        <h1 className="text-2xl font-bold text-secondary-900 mb-2">Forgot password</h1>
        <p className="text-secondary-600 mb-6">Enter your account email and we'll send you a reset link.</p>
        {error && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-danger-50 border border-danger-200 rounded-lg text-danger-700">
            <AlertCircle className="w-5 h-5" /><span className="text-sm">{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-4 flex items-center space-x-2 p-4 bg-success-50 border border-success-200 rounded-lg text-success-700">
            <CheckCircle className="w-5 h-5" /><span className="text-sm">{success}</span>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="label">Email address</label>
            <div className="relative mt-1.5">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" />
              <input id="email" type="email" required className="input pl-10" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn btn-primary w-full">
            {loading ? 'Sending...' : 'Send reset link'}
          </button>
        </form>
        <Link to="/login" className="mt-6 inline-flex items-center text-sm text-primary-600 hover:text-primary-700">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to login
        </Link>
      </div>
    </div>
  )
}
