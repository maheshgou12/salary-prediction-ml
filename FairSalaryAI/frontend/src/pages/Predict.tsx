import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Calculator, ArrowRight, Shield, Info, AlertCircle, Loader2 } from 'lucide-react'
import { api } from '../services/api'

const EDUCATION_OPTIONS = [
  'High School', 'Associate Degree', "Bachelor's Degree", "Master's Degree", 'PhD'
]

const JOB_ROLES = [
  'Software Engineer', 'Data Scientist', 'ML Engineer', 'DevOps Engineer',
  'Frontend Developer', 'Backend Developer', 'Full Stack Developer',
  'Data Analyst', 'Product Manager', 'Engineering Manager',
  'QA Engineer', 'Systems Architect', 'Security Engineer', 'Cloud Engineer'
]

const LOCATIONS = [
  'Bangalore', 'Mumbai', 'Delhi NCR', 'Hyderabad', 'Pune', 'Chennai',
  'Kolkata', 'Ahmedabad', 'Remote', 'Other'
]

const INDUSTRIES = [
  'Technology', 'Finance', 'Healthcare', 'E-commerce', 'Manufacturing',
  'Consulting', 'Education', 'Media', 'Telecommunications', 'Automotive'
]

const COMPANY_SIZES = [
  'Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1000+)'
]

const EMPLOYMENT_TYPES = [
  'Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance'
]

export function Predict() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    experience_years: 3,
    education: "Bachelor's Degree",
    job_role: 'Software Engineer',
    location: 'Bangalore',
    skills: ['Python', 'SQL'],
    industry: 'Technology',
    company_size: 'Medium (201-1000)',
    employment_type: 'Full-time',
  })
  const [skillsInput, setSkillsInput] = useState('Python, SQL')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<any>(null)

  // Parse skills input
  useEffect(() => {
    setFormData(prev => ({
      ...prev,
      skills: skillsInput.split(',').map(s => s.trim()).filter(Boolean)
    }))
  }, [skillsInput])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSkillsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSkillsInput(e.target.value)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    setResult(null)

    try {
      const response = await api.predict(formData)
      setResult(response)
      navigate(`/results/${response.prediction_id}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Prediction failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-secondary-900 flex items-center space-x-3">
          <Calculator className="w-8 h-8 text-primary-600" aria-hidden="true" />
          <span>Predict Fair Salary</span>
        </h1>
        <p className="text-secondary-600 mt-2">
          Enter candidate details to get a fair, data-driven salary recommendation with fairness analysis.
        </p>
      </div>

      {/* Fairness Notice */}
      <div className="mb-6 p-4 bg-primary-50 border border-primary-200 rounded-xl flex items-start space-x-3">
        <Shield className="w-5 h-5 text-primary-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
        <div>
          <h3 className="font-medium text-primary-800">Fairness Notice</h3>
          <p className="text-primary-700 text-sm mt-1">
            This prediction is made without using protected attributes (gender, age). The model is audited
            for demographic parity across protected groups. Results include fairness analysis.
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {error && (
          <div className="p-4 bg-danger-50 border border-danger-200 rounded-xl flex items-start space-x-3 text-danger-700" role="alert">
            <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" aria-hidden="true" />
            <span>{error}</span>
          </div>
        )}

        {/* Basic Info */}
        <fieldset className="card p-6">
          <legend className="text-lg font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
            <Calculator className="w-5 h-5 text-primary-600" aria-hidden="true" />
            <span>Candidate Profile</span>
          </legend>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="experience_years" className="label">Years of Experience</label>
              <input
                id="experience_years"
                name="experience_years"
                type="number"
                min="0"
                max="50"
                step="0.5"
                required
                value={formData.experience_years}
                onChange={handleChange}
                className="input mt-1.5"
              />
            </div>
            <div>
              <label htmlFor="education" className="label">Education Level</label>
              <select
                id="education"
                name="education"
                required
                value={formData.education}
                onChange={handleChange}
                className="input mt-1.5"
              >
                {EDUCATION_OPTIONS.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="job_role" className="label">Job Role</label>
              <select
                id="job_role"
                name="job_role"
                required
                value={formData.job_role}
                onChange={handleChange}
                className="input mt-1.5"
              >
                {JOB_ROLES.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="location" className="label">Location</label>
              <select
                id="location"
                name="location"
                required
                value={formData.location}
                onChange={handleChange}
                className="input mt-1.5"
              >
                {LOCATIONS.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          </div>
        </fieldset>

        {/* Skills */}
        <fieldset className="card p-6">
          <legend className="text-lg font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
            <Info className="w-5 h-5 text-primary-600" aria-hidden="true" />
            <span>Technical Skills</legend>
          <div>
            <label htmlFor="skills" className="label">Skills (comma-separated)</label>
            <input
              id="skills"
              type="text"
              value={skillsInput}
              onChange={handleSkillsChange}
              className="input mt-1.5"
              placeholder="Python, SQL, Machine Learning, AWS, Docker"
            />
            <p className="text-sm text-secondary-500 mt-1.5">
              Enter skills separated by commas. At least one skill required.
            </p>
          </div>
        </fieldset>

        {/* Company & Industry */}
        <fieldset className="card p-6">
          <legend className="text-lg font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
            <Info className="w-5 h-5 text-primary-600" aria-hidden="true" />
            <span>Company & Industry</legend>
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <label htmlFor="industry" className="label">Industry</label>
              <select
                id="industry"
                name="industry"
                required
                value={formData.industry}
                onChange={handleChange}
                className="input mt-1.5"
              >
                {INDUSTRIES.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="company_size" className="label">Company Size</label>
              <select
                id="company_size"
                name="company_size"
                required
                value={formData.company_size}
                onChange={handleChange}
                className="input mt-1.5"
              >
                {COMPANY_SIZES.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="employment_type" className="label">Employment Type</label>
              <select
                id="employment_type"
                name="employment_type"
                required
                value={formData.employment_type}
                onChange={handleChange}
                className="input mt-1.5"
              >
                {EMPLOYMENT_TYPES.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            </div>
          </div>
        </fieldset>

        {/* Submit */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-secondary-200">
          <div className="flex items-center space-x-2 text-secondary-600 text-sm">
            <Info className="w-4 h-4" aria-hidden="true" />
            <span>Protected attributes (gender, age) are NOT used for prediction</span>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary px-8 py-3 text-lg group"
          >
            {loading ? (
              <span className="flex items-center space-x-2">
                <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                <span>Predicting...</span>
              </span>
            ) : (
              <span className="flex items-center space-x-2">
                Predict Fair Salary
                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" aria-hidden="true" />
              </span>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}