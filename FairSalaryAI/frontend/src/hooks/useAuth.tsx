import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { UserResponse } from '../services/api'
import { api } from '../services/api'

interface AuthContextType {
  user: UserResponse | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string; full_name: string }) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (token) {
        const userData = await api.getCurrentUser()
        setUser(userData)
      }
    } catch (err: any) {
      // Only clear credentials if the server explicitly returned 401/403 unauthorized
      if (err?.response?.status === 401 || err?.response?.status === 403) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setUser(null)
      } else {
        // Backend waking up or network pause: retain stored tokens for continuous access
        console.warn('Backend waking up or network pause, maintaining authenticated session:', err?.message || err)
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const response = await api.login(email, password)
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    const userData = await api.getCurrentUser()
    setUser(userData)
  }

  const register = async (data: { email: string; password: string; full_name: string }) => {
    await api.register(data)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}