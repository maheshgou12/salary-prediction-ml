import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Calculator, Mail, Lock, User, AlertCircle, Eye, EyeOff, CheckCircle, AlertTriangle } from 'lucide-react'

const passwordRequirements = [
  { label: 'At least 8 characters', test: (p: string) => p.length >= 8 },
  { label: 'One uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
  { label: 'One lowercase letter', test: (p: string) => /[a-z]/.test(p) },
  { label: 'One number', test: (p: string) => /\d/.test(p) },
]

export function Register() {
  const { register } = useAuth()
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validation
    if (formData.password !== formData.confirm_password) {
      setError('Passwords do not match')
      return
    }

    const failedRequirements = passwordRequirements.filter(req => !req.test(formData.password))
    if (failedRequirements.length > 0) {
      setError(`Password must meet all requirements`)
      return
    }

    setLoading(true)

    try {
      await register({
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name,
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const getPasswordStrength = (password: string) => {
    let score = 0
    if (password.length >= 8) score++
    if (password.length >= 12) score++
    if (/[A-Z]/.test(password)) score++
    if (/[a-z]/.test(password)) score++
    if (/\d/.test(password)) score++
    if (/[^A-Za-z0-9]/.test(password)) score++

    if (score <= 2) return { label: 'Weak', color: 'text-danger-600', bg: 'bg-danger-100' }
    if (score <= 4) return { label: 'Fair', color: 'text-warning-600', bg: 'bg-warning-100' }
    if (score <= 5) return { label: 'Good', color: 'text-primary-600', bg: 'bg-primary-100' }
    return { label: 'Strong', color: 'text-success-600', bg: 'bg-success-100' }
  }

  const passwordStrength = getPasswordStrength(formData.password)

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-primary-50 via-white to-secondary-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center space-x-2 mb-6">
            <div className="w-12 h-12 rounded-xl bg-primary-600 flex items-center justify-center">
              <Calculator className="w-7 h-7 text-white" />
            </div>
            <span className="text-2xl font-bold text-secondary-900">FairSalary AI</span>
          </Link>
          <h1 className="text-3xl font-bold text-secondary-900">Create your account</h1>
          <p className="text-secondary-600 mt-2">Start making fair salary decisions today</p>
        </div>

        {/* Register Form */}
        <div className="card p-8">
          {error && (
            <div className="mb-6 flex items-center space-x-2 p-4 bg-danger-50 border border-danger-200 rounded-lg text-danger-700" role="alert">
              <AlertCircle className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            <div>
              <label htmlFor="full_name" className="label">
                Full name
              </label>
              <div className="relative mt-1.5">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" aria-hidden="true" />
                <input
                  id="full_name"
                  name="full_name"
                  type="text"
                  autoComplete="name"
                  required
                  value={formData.full_name}
                  onChange={handleChange}
                  className="input pl-10"
                  placeholder="John Doe"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="label">
                Email address
              </label>
              <div className="relative mt-1.5">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" aria-hidden="true" />
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="input pl-10"
                  placeholder="you@example.com"
                  disabled={loading}
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="relative mt-1.5">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" aria-hidden="true" />
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="input pl-10 pr-12"
                  placeholder="Create a strong password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-secondary-400 hover:text-secondary-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>

              {/* Password Strength */}
              <div className="mt-2">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-secondary-600">Password strength</span>
                  <span className={`font-medium px-2 py-0.5 rounded ${passwordStrength.bg} ${passwordStrength.color}`}>
                    {passwordStrength.label}
                  </span>
                </div>
                <div className="h-1.5 bg-secondary-200 rounded-full overflow-hidden mt-1">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      passwordStrength.color.replace('text-', 'bg-')
                    }`}
                    style={{ width: `${(passwordRequirements.filter(r => r.test(formData.password)).length / passwordRequirements.length) * 100}%` }}
                  ></div>
                </div>
                <ul className="mt-2 space-y-1 text-xs">
                  {passwordRequirements.map((req, i) => (
                    <li key={i} className="flex items-center space-x-2">
                      {passwordRequirements[i].test(formData.password) ? (
                        <CheckCircle className="w-4 h-4 text-success-500 flex-shrink-0" aria-hidden="true" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-secondary-300 flex-shrink-0" aria-hidden="true" />
                      )}
                      <span className={req.test(formData.password) ? 'text-secondary-500' : 'text-secondary-400'}>
                        {req.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div>
              <label htmlFor="confirm_password" className="label">
                Confirm password
              </label>
              <div className="relative mt-1.5">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400" aria-hidden="true" />
                <input
                  id="confirm_password"
                  name="confirm_password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.confirm_password}
                  onChange={handleChange}
                  className={`input pl-10 ${formData.confirm_password && formData.confirm_password !== formData.password ? 'input-error' : ''}`}
                  placeholder="Confirm your password"
                  disabled={loading}
                />
              </div>
              {formData.confirm_password && formData.confirm_password !== formData.password && (
                <p className="mt-1.5 text-sm text-danger-600 flex items-center space-x-1">
                  <AlertCircle className="w-4 h-4" aria-hidden="true" />
                  <span>Passwords do not match</span>
                </p>
              )}
            </div>

            <div className="flex items-start space-x-3">
              <input
                type="checkbox"
                id="terms"
                required
                className="w-4 h-4 mt-0.5 rounded border-secondary-300 text-primary-600 focus:ring-primary-500"
              />
              <label htmlFor="terms" className="text-sm text-secondary-600">
                I agree to the{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">Terms of Service</a>{' '}
                and{' '}
                <a href="#" className="text-primary-600 hover:text-primary-700">Privacy Policy</a>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-primary py-3 text-lg"
            >
              {loading ? (
                <span className="flex items-center justify-center space-x-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  <span>Creating account...</span>
                </span>
              ) : (
                'Create account'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-secondary-600">
              Already have an account?{' '}
              <Link to="/login" className="font-medium text-primary-600 hover:text-primary-700">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        {/* Demo notice */}
        <div className="mt-8 p-4 bg-secondary-50 rounded-xl">
          <p className="text-sm text-secondary-600 text-center">
            <strong>Demo:</strong> This is a demonstration system. Any email/password combination will work.
          </p>
        </div>
      </div>
    </div>
  )
}
