import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Calculator, DollarSign, Clock, ArrowRight, Download, Filter, ChevronLeft, ChevronRight, MoreHorizontal } from 'lucide-react'
import { api } from '../services/api'

interface Prediction {
  id: number
  input_data: any
  predicted_salary: number
  minimum_salary: number
  maximum_salary: number
  confidence: number
  model_version: string
  created_at: string
}

export function History() {
  const [predictions, setPredictions] = useState<Prediction[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [filters, setFilters] = useState({
    date_from: '',
    date_to: '',
    min_salary: '',
    max_salary: '',
  })

  useEffect(() => {
    fetchHistory()
  }, [page, pageSize, filters])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      const response = await api.getHistory(page, pageSize)
      // API returns array directly
      setPredictions(response || [])
      setTotal(response.length)
      setTotalPages(Math.ceil(response.length / pageSize))
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const formatSalary = (salary: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(salary)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getRole = (inputData: any) => inputData?.job_role || 'N/A'
  const getLocation = (inputData: any) => inputData?.location || 'N/A'
  const getExperience = (inputData: any) => `${inputData?.experience_years || 0} yrs`

  if (loading && predictions.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-secondary-600">Loading history...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900 flex items-center space-x-3">
            <Calculator className="w-8 h-8 text-primary-600" aria-hidden="true" />
            <span>Prediction History</span>
          </h1>
          <p className="text-secondary-600 mt-1">
            View and manage your salary prediction history
          </p>
        </div>
        <Link to="/predict" className="btn-primary">
          <Calculator className="w-4 h-4 mr-2" aria-hidden="true" />
          New Prediction
        </Link>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" aria-hidden="true" />
              <input
                type="date"
                value={filters.date_from}
                onChange={(e) => setFilters(p => ({ ...p, date_from: e.target.value }))}
                className="input pl-10 w-40"
                placeholder="From"
              />
            </div>
            <div className="relative">
              <input
                type="date"
                value={filters.date_to}
                onChange={(e) => setFilters(p => ({ ...p, date_to: e.target.value }))}
                className="input w-40"
                placeholder="To"
              />
            </div>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-secondary-400" aria-hidden="true" />
              <input
                type="number"
                placeholder="Min Salary"
                value={filters.min_salary}
                onChange={(e) => setFilters(p => ({ ...p, min_salary: e.target.value }))}
                className="input pl-10 w-36"
              />
            </div>
            <div className="relative">
              <input
                type="number"
                placeholder="Max Salary"
                value={filters.max_salary}
                onChange={(e) => setFilters(p => ({ ...p, max_salary: e.target.value }))}
                className="input w-36"
              />
            </div>
            <button className="btn-secondary" onClick={() => setFilters({ date_from: '', date_to: '', min_salary: '', max_salary: '' })}>
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      {error && (
        <div className="p-4 bg-danger-50 border border-danger-200 rounded-xl text-danger-700" role="alert">
          {error}
        </div>
      )}

      <div className="card overflow-hidden">
        {predictions.length === 0 ? (
          <div className="p-12 text-center">
            <Calculator className="w-16 h-16 text-secondary-300 mx-auto mb-4" aria-hidden="true" />
            <h3 className="text-lg font-medium text-secondary-900 mb-2">No predictions yet</h3>
            <p className="text-secondary-600 mb-6">Your prediction history will appear here</p>
            <Link to="/predict" className="btn-primary inline-flex items-center space-x-2">
              <Calculator className="w-4 h-4" aria-hidden="true" />
              <span>Make your first prediction</span>
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full" role="table">
                <thead className="bg-secondary-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-secondary-500 uppercase tracking-wider">Date</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-secondary-500 uppercase tracking-wider">Role</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-secondary-500 uppercase tracking-wider">Location</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-secondary-500 uppercase tracking-wider">Experience</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">Predicted</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-secondary-500 uppercase tracking-wider">Range</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-secondary-500 uppercase tracking-wider">Confidence</th>
                    <th className="px-4 py-3 text-center text-xs font-semibold text-secondary-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-secondary-100">
                  {predictions.map((prediction) => (
                    <tr key={prediction.id} className="hover:bg-secondary-50 transition-colors">
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-secondary-900">
                        {formatDate(prediction.created_at)}
                      </td>
                      <td className="px-4 py-4 text-sm text-secondary-700 max-w-xs truncate">
                        {prediction.input_data?.job_role || 'N/A'}
                      </td>
                      <td className="px-4 py-4 text-sm text-secondary-600">
                        {prediction.input_data?.location || 'N/A'}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-secondary-600">
                        {prediction.input_data?.experience_years || 0} yrs
                      </td>
                      <td className="px-4 py-4 text-right text-sm font-semibold text-secondary-900">
                        ₹{prediction.predicted_salary.toLocaleString('en-IN')}
                      </td>
                      <td className="px-4 py-4 text-right text-sm text-secondary-600">
                        ₹{prediction.minimum_salary.toLocaleString('en-IN')} – ₹{prediction.maximum_salary.toLocaleString('en-IN')}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          prediction.confidence >= 0.9 ? 'bg-success-100 text-success-700' :
                          prediction.confidence >= 0.8 ? 'bg-primary-100 text-primary-700' :
                          'bg-warning-100 text-warning-700'
                        }`}>
                          {Math.round(prediction.confidence * 100)}%
                        </span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <Link
                            to={`/results/${prediction.id}`}
                            className="p-2 text-secondary-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                            aria-label={`View details for prediction ${prediction.id}`}
                          >
                            <Calculator className="w-4 h-4" aria-hidden="true" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-4 border-t border-secondary-200 flex items-center justify-between">
                <div className="text-sm text-secondary-600">
                  Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, total)} of {total} results
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-2 rounded-lg text-secondary-600 hover:bg-secondary-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Previous page"
                  >
                    <ChevronLeft className="w-5 h-5" aria-hidden="true" />
                  </button>
                  <span className="text-sm text-secondary-600 px-3">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-2 rounded-lg text-secondary-600 hover:bg-secondary-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Next page"
                  >
                    <ChevronRight className="w-5 h-5" aria-hidden="true" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}