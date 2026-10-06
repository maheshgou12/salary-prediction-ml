import { Link } from 'react-router-dom'
import {
  Calculator,
  BarChart2,
  Shield,
  Brain,
  Users,
  ArrowRight,
  CheckCircle,
  Sparkles,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'

const features = [
  {
    icon: Calculator,
    title: 'Salary Prediction',
    description: 'Get accurate salary recommendations powered by XGBoost ensemble models trained on realistic candidate data.',
  },
  {
    icon: BarChart2,
    title: 'Salary Ranges',
    description: 'Receive statistically valid prediction intervals using conformal prediction, not fake confidence scores.',
  },
  {
    icon: Brain,
    title: 'SHAP Explainability',
    description: 'Understand exactly which factors drive your salary recommendation with feature-level SHAP explanations.',
  },
  {
    icon: Shield,
    title: 'Fairness Analysis',
    description: 'Automated bias detection across protected groups using Fairlearn demographic parity and error rate metrics.',
  },
  {
    icon: Users,
    title: 'Similar Profiles',
    description: 'Compare against historically similar candidates with median salaries and percentile ranges.',
  },
  {
    icon: Sparkles,
    title: 'Responsible AI',
    description: 'Built with transparency, privacy, and ethical guidelines at the core. No confidential data required.',
  },
]

const stats = [
  { value: '91.6%', label: 'Model R² Score' },
  { value: '$13.8K', label: 'Mean Absolute Error' },
  { value: '5,000+', label: 'Training Samples' },
  { value: '4', label: 'Protected Groups Audited' },
]

export function Home() {
  const { user } = useAuth()

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-primary-50 via-white to-secondary-50 py-20 lg:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-primary-50 text-primary-700 text-sm font-medium mb-6">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
                </span>
                <span>New: Fairness Dashboard & SHAP Explanations</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-secondary-900 tracking-tight text-balance mb-6">
                Fair Salary Recommendations
                <br />
                <span className="text-primary-600">Powered by Responsible AI</span>
              </h1>

              <p className="text-lg sm:text-xl text-secondary-600 mb-8 max-w-xl mx-auto lg:mx-0">
                Get accurate, explainable salary recommendations with built-in fairness auditing.
                Compare against similar candidates and understand what drives your compensation.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4 mb-10">
                {user ? (
                  <Link
                    to="/predict"
                    className="group w-full sm:w-auto btn-primary text-lg px-8 py-3"
                  >
                    Predict Salary
                    <ArrowRight className="w-5 h-5 ml-2 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                  </Link>
                ) : (
                  <Link
                    to="/register"
                    className="group w-full sm:w-auto btn-primary text-lg px-8 py-3"
                  >
                    Get Started Free
                    <ArrowRight className="w-5 h-5 ml-2 transition-transform group-hover:translate-x-1" aria-hidden="true" />
                  </Link>
                )}
                <Link to="/about" className="btn-secondary text-lg px-8 py-3 w-full sm:w-auto">
                  Learn More
                </Link>
              </div>

              {/* Trust indicators */}
              <div className="flex flex-wrap items-center justify-center lg:justify-start gap-6 text-sm text-secondary-500">
                <span className="flex items-center space-x-1">
                  <CheckCircle className="w-4 h-4 text-success-500" aria-hidden="true" />
                  <span>No confidential data required</span>
                </span>
                <span className="flex items-center space-x-1">
                  <CheckCircle className="w-4 h-4 text-success-500" aria-hidden="true" />
                  <span>Open source methodology</span>
                </span>
                <span className="flex items-center space-x-1">
                  <CheckCircle className="w-4 h-4 text-success-500" aria-hidden="true" />
                  <span>Fairness audited</span>
                </span>
              </div>
            </div>

            {/* Hero Visual */}
            <div className="relative">
              <div className="bg-white rounded-2xl shadow-xl border border-secondary-200 p-6 lg:p-8">
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-sm text-secondary-500">
                    <span>Prediction Result</span>
                    <span className="text-primary-600 font-medium">₹12.5 LPA</span>
                  </div>
                  <div className="h-2 bg-secondary-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary-500 to-primary-400 rounded-full"
                      style={{ width: '65%' }}
                    ></div>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="p-3 bg-secondary-50 rounded-xl">
                      <div className="text-2xl font-bold text-secondary-900">₹11.8L</div>
                      <div className="text-xs text-secondary-500">Lower Bound</div>
                    </div>
                    <div className="p-3 bg-primary-50 rounded-xl">
                      <div className="text-2xl font-bold text-primary-700">₹12.5L</div>
                      <div className="text-xs text-primary-600">Predicted</div>
                    </div>
                    <div className="p-3 bg-secondary-50 rounded-xl">
                      <div className="text-2xl font-bold text-secondary-900">₹13.5L</div>
                      <div className="text-xs text-secondary-500">Upper Bound</div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-secondary-500">
                    <Shield className="w-4 h-4 text-success-500" aria-hidden="true" />
                    <span>Fairness: PASS</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-secondary-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl sm:text-4xl font-bold">{stat.value}</div>
                <div className="text-secondary-300 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 lg:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-secondary-900 mb-4">
              Everything You Need for Fair Compensation
            </h2>
            <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
              Comprehensive tools for salary prediction, bias detection, and transparent decision-making.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <article
                key={feature.title}
                className="card p-6 group hover:border-primary-200"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center mb-4 group-hover:bg-primary-100 transition-colors">
                  <feature.icon className="w-6 h-6" aria-hidden="true" />
                </div>
                <h3 className="text-xl font-semibold text-secondary-900 mb-2">{feature.title}</h3>
                <p className="text-secondary-600 leading-relaxed">{feature.description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-600 text-white py-20">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Ready to Make Fair Salary Decisions?
          </h2>
          <p className="text-primary-100 text-lg mb-8 max-w-2xl mx-auto">
            Join organizations using FairSalary AI to bring transparency and fairness to their compensation decisions.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            {user ? (
              <Link to="/predict" className="bg-white text-primary-600 hover:bg-primary-50 px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
                Predict Now
              </Link>
            ) : (
              <Link to="/register" className="bg-white text-primary-600 hover:bg-primary-50 px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
                Start Free
              </Link>
            )}
            <Link to="/about" className="border-2 border-white text-white hover:bg-primary-700 px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
              Learn More
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}