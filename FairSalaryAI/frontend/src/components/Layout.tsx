import { Outlet, Link, useLocation, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import {
  LayoutDashboard,
  Calculator,
  History,
  BarChart2,
  User,
  LogOut,
  Menu,
  X,
  Home,
  Info,
} from 'lucide-react'
import { useState } from 'react'

export function Layout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'))
  const toggleDark = () => {
    document.documentElement.classList.toggle('dark')
    const on = document.documentElement.classList.contains('dark')
    setDark(on)
    localStorage.setItem('theme', on ? 'dark' : 'light')
  }

  const navItems = [
    { path: '/predict', label: 'Predict', icon: Calculator },
    { path: '/history', label: 'History', icon: History },
    { path: '/fairness', label: 'Fairness', icon: BarChart2 },
    { path: '/profile', label: 'Profile', icon: User },
  ]

  return (
    <div className="min-h-screen bg-secondary-50">
      {/* Header */}
      <header className="bg-white border-b border-secondary-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2" aria-label="FairSalary AI Home">
              <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
                <Calculator className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-secondary-900">FairSalary AI</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-1" aria-label="Main navigation">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary-50 text-primary-700'
                        : 'text-secondary-600 hover:bg-secondary-50 hover:text-secondary-900'
                    }`
                  }
                >
                  <item.icon className="w-4 h-4" aria-hidden="true" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </nav>

            {/* User Menu */}
            <div className="hidden md:flex items-center space-x-4">
              <Link
                to="/fairness"
                className="text-sm font-medium text-secondary-600 hover:text-secondary-900 transition-colors"
              >
                Fairness
              </Link>
              <Link
                to="/history"
                className="text-sm font-medium text-secondary-600 hover:text-secondary-900 transition-colors"
              >
                History
              </Link>
              <div className="flex items-center space-x-3">
                <Link
                  to="/profile"
                  className="text-sm text-secondary-600 hover:text-secondary-900 transition-colors"
                >
                  {user?.full_name}
                </Link>
                <button onClick={toggleDark} aria-label="Toggle dark mode" className="p-2 rounded-lg hover:bg-secondary-100 text-secondary-600 text-lg">
                  {dark ? '☀️' : '🌙'}
                </button>
                <button
                  onClick={() => logout()}
                  className="text-sm font-medium text-secondary-600 hover:text-secondary-900 transition-colors"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-lg text-secondary-600 hover:bg-secondary-100"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-secondary-200 bg-white">
          <nav className="px-4 py-4 space-y-2" aria-label="Mobile navigation">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-base font-medium ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-secondary-600 hover:bg-secondary-50'
                  }`
                }
              >
                <item.icon className="w-5 h-5" aria-hidden="true" />
                <span>{item.label}</span>
              </NavLink>
            ))}
            <div className="pt-4 border-t border-secondary-200">
              <div className="px-3 py-2 text-sm text-secondary-600">
                Signed in as {user?.full_name}
              </div>
              <button
                onClick={() => { logout(); setMobileMenuOpen(false); }}
                className="w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-base font-medium text-secondary-600 hover:bg-secondary-50"
              >
                <LogOut className="w-5 h-5" aria-hidden="true" />
                <span>Logout</span>
              </button>
            </div>
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-secondary-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <p className="text-sm text-secondary-500">
              FairSalary AI - AI-Powered Fair Salary Recommendations
            </p>
            <div className="flex items-center space-x-6">
              <Link
                to="/about"
                className="text-sm text-secondary-500 hover:text-secondary-700"
              >
                About
              </Link>
              <a
                href="#"
                className="text-sm text-secondary-500 hover:text-secondary-700"
              >
                Privacy
              </a>
              <a
                href="#"
                className="text-sm text-secondary-500 hover:text-secondary-700"
              >
                Terms
              </a>
            </div>
          </div>
          <p className="mt-4 text-xs text-secondary-400 text-center">
            <strong>Disclaimer:</strong> This system provides AI-assisted salary recommendations based on
            synthetic demonstration data. It should not be used as the sole basis for employment decisions.
            Do not upload confidential employee information.
          </p>
        </div>
      </footer>
    </div>
  )
}
