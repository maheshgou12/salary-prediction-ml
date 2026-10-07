import { useState, useEffect } from 'react'
import { Shield, CheckCircle, AlertTriangle, XCircle, BarChart2, Users, TrendingUp, Download, RefreshCw } from 'lucide-react'
import { api } from '../services/api'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts'

interface FairnessDashboard {
  overall_status: string
  protected_attributes: Array<{
    attribute: string
    status: string
    demographic_parity_difference: number
    mean_prediction_difference: number
    mae_by_group: Record<string, number>
    rmse_by_group: Record<string, number>
    groups: Array<{
      group: string
      count: number
      mean_predicted: number
      mean_actual: number | null
      mae: number | null
      rmse: number | null
      bias: number
    }>
    recommendations: string[]
  }>
  recommendations: string[]
}

const STATUS_COLORS = {
  PASS: { bg: 'bg-success-100', text: 'text-success-700', icon: CheckCircle, color: '#22c55e' },
  REVIEW: { bg: 'bg-warning-100', text: 'text-warning-700', icon: AlertTriangle, color: '#f59e0b' },
  WARNING: { bg: 'bg-danger-100', text: 'text-danger-700', icon: XCircle, color: '#ef4444' },
  UNKNOWN: { bg: 'bg-secondary-100', text: 'text-secondary-700', icon: Shield, color: '#64748b' },
}

const STATUS_LABELS = {
  PASS: 'Pass',
  REVIEW: 'Review Recommended',
  WARNING: 'Action Required',
  UNKNOWN: 'Unknown',
}

export function Fairness() {
  const [dashboard, setDashboard] = useState<FairnessDashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'overview' | 'gender' | 'age' | 'intersectional'>('overview')

  useEffect(() => {
    fetchDashboard()
  }, [])

  const fetchDashboard = async () => {
    setLoading(true)
    try {
      const data = await api.getFairnessDashboard()
      setDashboard(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load fairness dashboard')
    } finally {
      setLoading(false)
    }
  }

  const refreshData = async () => {
    await fetchDashboard()
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-secondary-600">Loading fairness analysis...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-16 h-16 text-danger-500 mx-auto mb-4" aria-hidden="true" />
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">Failed to load fairness dashboard</h2>
        <p className="text-secondary-600 mb-6">{error}</p>
        <button onClick={refreshData} className="btn-primary flex items-center space-x-2 mx-auto">
          <RefreshCw className="w-4 h-4" aria-hidden="true" />
          <span>Retry</span>
        </button>
      </div>
    )
  }

  if (!dashboard) {
    return <div className="text-center py-12">No fairness data available</div>
  }

  const getStatusConfig = (status: string) => STATUS_COLORS[status as keyof typeof STATUS_COLORS] || STATUS_COLORS.UNKNOWN

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900 flex items-center space-x-3">
            <Shield className="w-8 h-8 text-primary-600" aria-hidden="true" />
            <span>Fairness Dashboard</span>
          </h1>
          <p className="text-secondary-600 mt-1">
            Bias analysis and fairness metrics across protected groups
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button onClick={refreshData} className="btn-secondary" disabled={loading}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
            Refresh
          </button>
          <button className="btn-primary">
            <Download className="w-4 h-4 mr-2" aria-hidden="true" />
            Export Report
          </button>
        </div>
      </div>

      {/* Overall Status */}
      <div className="card p-6">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-semibold text-secondary-900">Overall Fairness Status</h2>
            <p className="text-secondary-600 mt-1">Model v1.0.0 • Last updated: {new Date().toLocaleDateString()}</p>
          </div>
          <div className="flex items-center space-x-4">
            <div className={`px-4 py-2 rounded-xl ${getStatusConfig(dashboard.overall_status).bg}`}>
              <span className={`font-semibold ${getStatusConfig(dashboard.overall_status).text}`}>
                {STATUS_LABELS[dashboard.overall_status as keyof typeof STATUS_LABELS]}
              </span>
            </div>
          </div>
        </div>

        {dashboard.recommendations.length > 0 && (
          <div className="mt-4 p-4 bg-warning-50 border border-warning-200 rounded-xl">
            <h3 className="font-medium text-warning-800 mb-2 flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
              <span>Recommendations</span>
            </h3>
            <ul className="list-disc list-inside space-y-1 text-warning-700">
              {dashboard.recommendations.map((rec, i) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Protected Attributes Tabs */}
      <div className="card">
        <div className="border-b border-secondary-200">
          <nav className="flex space-x-8 px-6" aria-label="Protected attribute tabs">
            <button
              onClick={() => setActiveTab('overview')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'overview'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-secondary-500 hover:text-secondary-700'
              }`}
            >
              Overview
            </button>
            {dashboard.protected_attributes.map((attr) => (
              <button
                key={attr.attribute}
                onClick={() => setActiveTab(attr.attribute as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === attr.attribute
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-secondary-500 hover:text-secondary-700'
                }`}
              >
                {attr.attribute.charAt(0).toUpperCase() + attr.attribute.slice(1)}
              </button>
            ))}
            <button
              onClick={() => setActiveTab('intersectional')}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === 'intersectional'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-secondary-500 hover:text-secondary-700'
              }`}
            >
              Intersectional
            </button>
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && <OverviewTab dashboard={dashboard} />}
          {activeTab === 'gender' && <AttributeTab attribute={dashboard.protected_attributes.find(a => a.attribute === 'gender')} />}
          {activeTab === 'age' && <AttributeTab attribute={dashboard.protected_attributes.find(a => a.attribute === 'age')} />}
          {activeTab === 'intersectional' && <IntersectionalTab dashboard={dashboard} />}
        </div>
      </div>
    </div>
  )
}

function OverviewTab({ dashboard }: { dashboard: FairnessDashboard }) {
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {dashboard.protected_attributes.map((attr) => {
          const config = getStatusConfig(attr.status)
          const Icon = config.icon
          return (
            <div key={attr.attribute} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-secondary-900 capitalize">{attr.attribute}</h3>
                <Icon className={`w-5 h-5 ${config.color}`} aria-hidden="true" />
              </div>
              <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
                {STATUS_LABELS[attr.status as keyof typeof STATUS_LABELS]}
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-secondary-500">DP Difference</div>
                  <div className="font-mono font-medium">{attr.demographic_parity_difference.toFixed(3)}</div>
                </div>
                <div>
                  <div className="text-secondary-500">Mean Diff</div>
                  <div className="font-mono font-medium">₹{attr.mean_prediction_difference.toLocaleString()}</div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Group Comparison Chart */}
      <div className="card p-6">
        <h3 className="font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
          <BarChart2 className="w-5 h-5 text-primary-600" aria-hidden="true" />
          <span>Predicted Salary by Group</span>
        </h3>
        <div className="grid md:grid-cols-2 gap-6">
          {dashboard.protected_attributes.map((attr) => (
            <div key={attr.attribute}>
              <h4 className="font-medium text-secondary-900 mb-3 capitalize">{attr.attribute}</h4>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={attr.groups} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis type="number" tick={{ fill: '#64748b' }} />
                  <YAxis type="category" dataKey="group" tick={{ fill: '#64748b' }} width={100} />
                  <Tooltip formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, 'Predicted Salary']} />
                  <Bar dataKey="mean_predicted" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      {dashboard.recommendations.length > 0 && (
        <div className="card p-6 bg-warning-50 border border-warning-200">
          <h3 className="font-semibold text-warning-800 mb-3 flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5" aria-hidden="true" />
            <span>Key Recommendations</span>
          </h3>
          <ul className="list-disc list-inside space-y-2 text-warning-700">
            {dashboard.recommendations.map((rec, i) => (
              <li key={i}>{rec}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function AttributeTab({ attribute }: { attribute: any }) {
  if (!attribute) return <div className="p-6 text-center text-secondary-500">No data available</div>

  const config = getStatusConfig(attribute.status)
  const Icon = config.icon

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 bg-secondary-50 rounded-xl">
        <div className="flex items-center space-x-3">
          <Icon className={`w-8 h-8 ${config.color}`} aria-hidden="true" />
          <div>
            <h3 className="text-xl font-semibold text-secondary-900 capitalize">{attribute.attribute}</h3>
            <div className={`inline-flex px-3 py-1 rounded-full text-sm font-medium mt-1 ${config.bg} ${config.text}`}>
              {STATUS_LABELS[attribute.status as keyof typeof STATUS_LABELS]}
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-6 text-sm">
          <div className="text-secondary-500">DP Difference</div>
          <div className="font-mono font-medium">{attribute.demographic_parity_difference.toFixed(3)}</div>
          <div className="text-secondary-500">Mean Diff</div>
          <div className="font-mono font-medium">₹{attribute.mean_prediction_difference.toLocaleString()}</div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <MetricCard label="Demographic Parity" value={attribute.demographic_parity_difference.toFixed(3)} color="primary" />
        <MetricCard label="Mean Prediction Diff" value={`₹${attribute.mean_prediction_difference.toLocaleString()}`} color="secondary" />
        <MetricCard label="MAE Range" value={`${Object.values(attribute.mae_by_group).length} groups`} color="success" />
        <MetricCard label="RMSE Range" value={`${Object.values(attribute.rmse_by_group).length} groups`} color="warning" />
      </div>

      {/* Group Metrics Table */}
      <div className="card overflow-hidden">
        <h3 className="px-6 py-4 border-b border-secondary-200 font-semibold text-secondary-900">Group Metrics</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-secondary-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-secondary-500 uppercase tracking-wider">Group</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">Count</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">Mean Predicted</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">Mean Actual</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">Bias</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">MAE</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">RMSE</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-secondary-100">
              {attribute.groups.map((group: any) => (
                <tr key={group.group} className="hover:bg-secondary-50">
                  <td className="px-6 py-4 font-medium text-secondary-900">{group.group}</td>
                  <td className="px-6 py-4 text-right text-secondary-600">{group.count.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right text-secondary-700">₹{group.mean_predicted.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right text-secondary-600">{group.mean_actual ? '₹' + group.mean_actual.toLocaleString() : 'N/A'}</td>
                  <td className="px-6 py-4 text-right">
                    <span className={`font-medium ${group.bias > 0 ? 'text-danger-600' : group.bias < 0 ? 'text-success-600' : 'text-secondary-600'}`}>
                      {group.bias > 0 ? '+' : ''}₹{Math.abs(group.bias).toLocaleString()}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-secondary-600">{group.mae ? '₹' + group.mae.toLocaleString() : 'N/A'}</td>
                  <td className="px-6 py-4 text-right text-secondary-600">{group.rmse ? '₹' + group.rmse.toLocaleString() : 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Group Comparison Chart */}
        <div className="card p-6">
          <h3 className="font-semibold text-secondary-900 mb-4">Predicted Salary by Group</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={attribute.groups} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis type="number" tick={{ fill: '#64748b' }} />
              <YAxis type="category" dataKey="group" tick={{ fill: '#64748b' }} width={120} />
              <Tooltip formatter={(value: number) => [`₹${value.toLocaleString('en-IN')}`, 'Predicted Salary']} />
              <Bar dataKey="mean_predicted" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recommendations */}
        {attribute.recommendations.length > 0 && (
          <div className="card p-6 bg-warning-50 border border-warning-200">
            <h3 className="font-semibold text-warning-800 mb-3 flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5" aria-hidden="true" />
              <span>Recommendations</span>
            </h3>
            <ul className="list-disc list-inside space-y-2 text-warning-700">
              {attribute.recommendations.map((rec: any, i: number) => (
                <li key={i}>{rec}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

function IntersectionalTab({ dashboard }: { dashboard: FairnessDashboard }) {
  const intersectional = dashboard.protected_attributes.flatMap(attr =>
    attr.groups.map(g => ({ ...g, attribute: attr.attribute }))
  )

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h3 className="font-semibold text-secondary-900 mb-4">Intersectional Analysis</h3>
        <p className="text-secondary-600 mb-6">
          Analysis of fairness across combined protected attributes (gender × age groups).
          <strong className="text-secondary-900"> Intersectional analysis coming soon.</strong>
        </p>

        <div className="card p-4 bg-secondary-50">
          <h4 className="font-medium text-secondary-900 mb-3">Sample Intersectional Groups</h4>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-secondary-100">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">Gender</th>
                  <th className="px-4 py-2 text-left font-medium">Age Group</th>
                  <th className="px-4 py-2 text-right font-medium">Count</th>
                  <th className="px-4 py-2 text-right font-medium">Mean Predicted</th>
                  <th className="px-4 py-2 text-right font-medium">Bias</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-t border-secondary-200">
                  <td className="px-4 py-2">Female</td>
                  <td className="px-4 py-2">20-30</td>
                  <td className="px-4 py-2 text-right">1,234</td>
                  <td className="px-4 py-2 text-right">₹12.4 L</td>
                  <td className="px-4 py-2 text-right text-danger-600">+₹45K</td>
                </tr>
                <tr className="border-t border-secondary-200">
                  <td className="px-4 py-2">Male</td>
                  <td className="px-4 py-2">20-30</td>
                  <td className="px-4 py-2 text-right">1,567</td>
                  <td className="px-4 py-2 text-right">₹12.8 L</td>
                  <td className="px-4 py-2 text-right text-success-600">-₹23K</td>
                </tr>
                <tr className="border-t border-secondary-200">
                  <td className="px-4 py-2">Female</td>
                  <td className="px-4 py-2">30-40</td>
                  <td className="px-4 py-2 text-right">987</td>
                  <td className="px-4 py-2 text-right">₹14.2 L</td>
                  <td className="px-4 py-2 text-right text-danger-600">+₹67K</td>
                </tr>
                <tr className="border-t border-secondary-200">
                  <td className="px-4 py-2">Male</td>
                  <td className="px-4 py-2">30-40</td>
                  <td className="px-4 py-2 text-right">1,123</td>
                  <td className="px-4 py-2 text-right">₹15.1 L</td>
                  <td className="px-4 py-2 text-right text-success-600">-₹34K</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  const colorMap = {
    primary: 'bg-primary-50 text-primary-700',
    secondary: 'bg-secondary-50 text-secondary-700',
    success: 'bg-success-50 text-success-700',
    warning: 'bg-warning-50 text-warning-700',
  }

  return (
    <div className={`p-4 rounded-xl ${colorMap[color as keyof typeof colorMap] || colorMap.primary}`}>
      <div className="text-sm text-secondary-500 mb-1">{label}</div>
      <div className="text-xl font-bold">{value}</div>
    </div>
  )
}

function getStatusConfig(status: string) {
  return STATUS_COLORS[status as keyof typeof STATUS_COLORS] || STATUS_COLORS.UNKNOWN
}

