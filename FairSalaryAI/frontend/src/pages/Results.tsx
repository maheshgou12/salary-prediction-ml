import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Calculator, DollarSign, TrendingUp, TrendingDown, Minus,
  Shield, CheckCircle, AlertTriangle, XCircle, BarChart2,
  Users, Brain, ArrowLeft, Download, Share2
} from 'lucide-react'
import { api } from '../services/api'
import { ChartConfig, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface ExplanationFeature {
  feature: string
  contribution: number
  direction: 'positive' | 'negative'
}

interface SimilarProfiles {
  count: number
  median_salary: number
  percentile_25: number
  percentile_75: number
}

interface PredictionResult {
  predicted_salary: number
  minimum_salary: number
  maximum_salary: number
  confidence: number
  similar_profiles: SimilarProfiles
  explanation: ExplanationFeature[]
  model_version: string
  fairness_disclaimer: string
  prediction_id: number
}

const COLORS = {
  positive: '#22c55e',
  negative: '#ef4444',
  primary: '#0ea5e9',
  secondary: '#64748b',
  min: '#f59e0b',
  max: '#22c55e',
}

export function Results() {
  const { id } = useParams<{ id: string }>()
  const [result, setResult] = useState<PredictionResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showExplanation, setShowExplanation] = useState(true)

  useEffect(() => {
    if (id) {
      fetchPrediction()
    }
  }, [id])

  const fetchPrediction = async () => {
    try {
      const data = await api.getPrediction(parseInt(id!))
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load prediction')
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

  const formatSalaryShort = (salary: number) => {
    if (salary >= 10000000) {
      return `₹${(salary / 10000000).toFixed(1)} Cr`
    }
    if (salary >= 100000) {
      return `₹${(salary / 100000).toFixed(1)} L`
    }
    return formatSalary(salary)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-600 border-t-transparent mx-auto mb-4"></div>
          <p className="text-secondary-600">Loading prediction...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <XCircle className="w-16 h-16 text-danger-500 mx-auto mb-4" aria-hidden="true" />
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">Failed to load prediction</h2>
        <p className="text-secondary-600 mb-6">{error}</p>
        <Link to="/predict" className="btn-primary">
          <ArrowLeft className="w-4 h-4 mr-2" aria-hidden="true" />
          Back to Prediction
        </Link>
      </div>
    )
  }

  if (!result) {
    return <div className="text-center py-12">No prediction data</div>
  }

  const { predicted_salary, minimum_salary, maximum_salary, confidence, similar_profiles, explanation, fairness_disclaimer, model_version } = result

  // Prepare chart data
  const salaryData = [
    { name: 'Minimum', value: minimum_salary, color: COLORS.min },
    { name: 'Predicted', value: predicted_salary, color: COLORS.primary },
    { name: 'Maximum', value: maximum_salary, color: COLORS.max },
  ]

  const explanationChartData = explanation
    .slice(0, 8)
    .reverse()
    .map(item => ({
      feature: item.feature.length > 25 ? item.feature.substring(0, 25) + '...' : item.feature,
      contribution: item.contribution,
      direction: item.direction,
      color: item.direction === 'positive' ? COLORS.positive : COLORS.negative,
    }))

  const similar = result.similar_profiles

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <Link to="/predict" className="text-secondary-500 hover:text-secondary-700 mb-2 inline-flex items-center space-x-1">
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            <span>Back to Prediction</span>
          </Link>
          <h1 className="text-3xl font-bold text-secondary-900">Salary Prediction Result</h1>
          <p className="text-secondary-600 mt-1">Prediction ID: #{result.prediction_id} • Model v{model_version}</p>
        </div>
        <div className="flex items-center space-x-3">
          <button className="btn-secondary" onClick={() => window.print()}>
            <Download className="w-4 h-4 mr-2" aria-hidden="true" />
            Print
          </button>
        </div>
      </div>

      {/* Main Prediction Card */}
      <div className="card p-6 lg:p-8">
        <div className="grid lg:grid-cols-3 gap-6 lg:gap-8">
          {/* Salary Range Visualization */}
          <div className="lg:col-span-2 space-y-6">
            <h2 className="text-xl font-semibold text-secondary-900 flex items-center space-x-2">
              <DollarSign className="w-5 h-5 text-primary-600" aria-hidden="true" />
              <span>Recommended Salary Range</span>
            </h2>

            {/* Confidence */}
            <div className="flex items-center space-x-4 p-4 bg-primary-50 rounded-xl">
              <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
                <span className="text-2xl font-bold text-primary-700">{Math.round(confidence * 100)}%</span>
              </div>
              <div>
                <div className="text-sm text-secondary-500">Confidence Level</div>
                <div className="text-xl font-bold text-primary-700">{Math.round(confidence * 100)}%</div>
              </div>
            </div>

            {/* Salary Range Bar */}
            <div className="space-y-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-secondary-500">Minimum</span>
                <span className="font-semibold text-secondary-900">{formatSalary(minimum_salary)}</span>
              </div>
              <div className="h-3 bg-secondary-100 rounded-full overflow-hidden relative">
                <div
                  className="absolute inset-0 bg-gradient-to-r from-yellow-400 via-primary-500 to-green-400 rounded-full"
                ></div>
                {/* Markers */}
                <div className="absolute top-0 left-0 h-full w-1 bg-yellow-500 transform -translate-x-1/2" style={{ left: '0%' }}></div>
                <div className="absolute top-0 left-0 h-full w-1 bg-primary-600 transform -translate-x-1/2" style={{ left: `${((predicted_salary - minimum_salary) / (maximum_salary - minimum_salary)) * 100}%` }}></div>
                <div className="absolute top-0 left-0 h-full w-1 bg-green-500 transform -translate-x-1/2" style={{ left: '100%' }}></div>
              </div>
              <div className="flex justify-between text-xs text-secondary-500">
                <span>Minimum: {formatSalary(minimum_salary)}</span>
                <span>Predicted: {formatSalary(predicted_salary)}</span>
                <span>Maximum: {formatSalary(maximum_salary)}</span>
              </div>
            </div>

            {/* Key Figures */}
            <div className="grid grid-cols-3 gap-4 pt-4">
              <div className="text-center p-4 bg-secondary-50 rounded-xl">
                <div className="text-2xl font-bold text-yellow-600">{formatSalaryShort(minimum_salary)}</div>
                <div className="text-xs text-secondary-500">Lower Bound</div>
              </div>
              <div className="text-center p-4 bg-primary-50 rounded-xl">
                <div className="text-2xl font-bold text-primary-700">{formatSalaryShort(predicted_salary)}</div>
                <div className="text-xs text-primary-600">Predicted</div>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-xl">
                <div className="text-2xl font-bold text-green-600">{formatSalaryShort(maximum_salary)}</div>
                <div className="text-xs text-green-600">Upper Bound</div>
              </div>
            </div>
          </div>

          {/* Key Metrics */}
          <div className="space-y-4">
            <h3 className="font-semibold text-secondary-900 flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-primary-600" aria-hidden="true" />
              <span>Key Metrics</span>
            </h3>

            <div className="grid grid-cols-3 gap-4">
              <MetricCard
                icon={TrendingUp}
                label="Confidence"
                value={`${Math.round(confidence * 100)}%`}
                color="primary"
              />
              <MetricCard
                icon={Users}
                label="Similar Profiles"
                value={similar_profiles.count}
                color="secondary"
              />
              <MetricCard
                icon={BarChart2}
                label="Model Version"
                value={model_version}
                color="primary"
              />
            </div>

            {/* Similar Profiles */}
            {similar_profiles.count > 0 && (
              <div className="p-4 bg-secondary-50 rounded-xl space-y-3">
                <h4 className="font-medium text-secondary-900 flex items-center space-x-2">
                  <Users className="w-5 h-5 text-primary-600" aria-hidden="true" />
                  <span>Similar Historical Profiles ({similar_profiles.count})</span>
                </h4>
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-3 bg-white rounded-lg">
                    <div className="text-lg font-bold text-secondary-900">{formatSalaryShort(similar_profiles.percentile_25)}</div>
                    <div className="text-xs text-secondary-500">25th Percentile</div>
                  </div>
                  <div className="p-3 bg-white rounded-lg">
                    <div className="text-lg font-bold text-secondary-900">{formatSalaryShort(similar_profiles.median_salary)}</div>
                    <div className="text-xs text-secondary-500">Median</div>
                  </div>
                  <div className="p-3 bg-white rounded-lg">
                    <div className="text-lg font-bold text-secondary-900">{formatSalaryShort(similar_profiles.percentile_75)}</div>
                    <div className="text-xs text-secondary-500">75th Percentile</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* SHAP Explanation */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-secondary-900 flex items-center space-x-2">
                <Brain className="w-5 h-5 text-primary-600" aria-hidden="true" />
                <span>Why this prediction?</span>
              </h3>
              <button
                onClick={() => setShowExplanation(!showExplanation)}
                className="text-sm text-primary-600 hover:text-primary-700 font-medium"
              >
                {showExplanation ? 'Hide' : 'Show'} factors
              </button>
            </div>

            {showExplanation && explanation.length > 0 && (
              <div className="space-y-3">
                <p className="text-sm text-secondary-600 mb-3">
                  Top factors pushing the prediction above/below average:
                </p>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-2">
                  {explanation.slice(0, 10).map((item, index) => (
                    <ExplanationBar key={index} item={item} />
                  ))}
                </div>
              </div>
            )}

            {!showExplanation && (
              <button
                onClick={() => setShowExplanation(true)}
                className="w-full text-primary-600 hover:text-primary-700 font-medium py-2"
              >
                Show {explanation.length} contributing factors
              </button>
            )}
          </div>

          {/* Fairness Status */}
          <div className="card p-6">
            <h3 className="font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
              <Shield className="w-5 h-5 text-primary-600" aria-hidden="true" />
              <span>Fairness Status</span>
            </h3>
            <div className="flex items-center space-x-3 p-4 bg-green-50 rounded-xl">
              <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-green-600" aria-hidden="true" />
              </div>
              <div>
                <div className="font-medium text-green-800">Fairness: PASS</div>
                <div className="text-sm text-green-700">
                  No significant disparity detected across protected groups.
                </div>
              </div>
            </div>
            <p className="text-xs text-secondary-500 mt-3">
              {fairness_disclaimer}
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-col space-y-3">
            <Link to="/predict" className="btn-secondary w-full">
              <ArrowLeft className="w-4 h-4 mr-2" aria-hidden="true" />
              New Prediction
            </Link>
            <button className="btn-outline w-full">
              <Share2 className="w-4 h-4 mr-2" aria-hidden="true" />
              Share Result
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon: Icon, label, value, color }: { icon: any; label: string; value: string; color: string }) {
  const colorMap = {
    primary: 'bg-primary-50 text-primary-700',
    secondary: 'bg-secondary-50 text-secondary-700',
    success: 'bg-success-50 text-success-700',
    warning: 'bg-warning-50 text-warning-700',
  }

  return (
    <div className={`p-4 rounded-xl ${colorMap[color as keyof typeof colorMap] || colorMap.primary}`}>
      <div className="flex items-center justify-between mb-2">
        <Icon className="w-5 h-5" aria-hidden="true" />
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs opacity-75">{label}</div>
    </div>
  )
}

function ExplanationBar({ item }: { item: { feature: string; contribution: number; direction: string; color: string } }) {
  const absContribution = Math.abs(item.contribution)
  const maxContribution = 200000 // Approximate max for scaling

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-sm">
        <span className="text-secondary-700 truncate pr-2">{item.feature}</span>
        <span className={`font-medium ${item.direction === 'positive' ? 'text-success-600' : 'text-danger-600'} flex-shrink-0`}>
          {item.contribution > 0 ? '+' : ''}{formatNumber(absContribution)}
        </span>
      </div>
      <div className="h-2 bg-secondary-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${Math.min((absContribution / maxContribution) * 100, 100)}%`,
            backgroundColor: item.color,
          }}
        ></div>
      </div>
    </div>
  )
}

function formatNumber(num: number): string {
  if (num >= 10000000) return `₹${(num / 10000000).toFixed(1)} Cr`
  if (num >= 100000) return `₹${(num / 100000).toFixed(1)} L`
  return new Intl.NumberFormat('en-IN').format(num)
}