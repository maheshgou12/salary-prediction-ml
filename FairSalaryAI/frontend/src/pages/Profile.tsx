import { useAuth } from '../hooks/useAuth'
import { User, Mail, Shield, Calendar } from 'lucide-react'

export function Profile() {
  const { user } = useAuth()

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-secondary-900 mb-8">My Profile</h1>
      <div className="card p-8 space-y-6">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
            <User className="w-8 h-8 text-primary-700" />
          </div>
          <div>
            <p className="text-xl font-semibold text-secondary-900">{user?.full_name}</p>
            <p className="text-secondary-500 text-sm">Account ID #{user?.id}</p>
          </div>
        </div>
        <div className="divide-y divide-secondary-100">
          <div className="flex items-center space-x-3 py-3">
            <Mail className="w-5 h-5 text-secondary-400" />
            <span className="text-secondary-600 w-32">Email</span>
            <span className="text-secondary-900">{user?.email}</span>
          </div>
          <div className="flex items-center space-x-3 py-3">
            <Shield className="w-5 h-5 text-secondary-400" />
            <span className="text-secondary-600 w-32">Status</span>
            <span className="text-success-600 font-medium">{user?.is_active ? 'Active' : 'Inactive'}</span>
          </div>
          <div className="flex items-center space-x-3 py-3">
            <Calendar className="w-5 h-5 text-secondary-400" />
            <span className="text-secondary-600 w-32">Member since</span>
            <span className="text-secondary-900">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</span>
          </div>
        </div>
      </div>
    </div>
  )
}
