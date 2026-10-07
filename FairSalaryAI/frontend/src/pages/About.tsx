import { Link } from 'react-router-dom'
import { Calculator, Shield, Brain, BarChart2, Users, CheckCircle, ArrowRight, Sparkles } from 'lucide-react'

const features = [
  {
    icon: Calculator,
    title: 'Accurate Predictions',
    description: 'XGBoost ensemble models with 91.6% R² score and $13.8K MAE on test data.',
  },
  {
    icon: Shield,
    title: 'Fairness Auditing',
    description: 'Automated demographic parity and error rate analysis across protected groups using Fairlearn.',
  },
  {
    icon: Brain,
    title: 'SHAP Explainability',
    description: 'Feature-level contribution breakdown showing exactly what drives each salary prediction.',
  },
  {
    icon: BarChart2,
    title: 'Salary Ranges',
    description: 'Conformal prediction intervals providing statistically valid confidence intervals.',
  },
  {
    icon: Users,
    title: 'Similar Profiles',
    description: 'Comparison with median salaries and percentile ranges from similar candidates.',
  },
  {
    icon: Sparkles,
    title: 'Responsible AI',
    description: 'Built with transparency, privacy, and ethical guidelines. No confidential data required.',
  },
]

const methodologySteps = [
  {
    step: 1,
    title: 'Data Generation',
    description: 'Synthetic dataset of 5,000+ realistic candidate profiles with experience, education, skills, location, and salary relationships.',
  },
  {
    step: 2,
    title: 'Preprocessing',
    description: 'ColumnTransformer pipeline with median imputation, StandardScaler for numerical features, and OneHotEncoder for categorical variables.',
  },
  {
    step: 3,
    title: 'Model Training',
    description: 'Comparison of Linear Regression, Random Forest, Gradient Boosting, and XGBoost with Optuna hyperparameter optimization.',
  },
  {
    step: 4,
    title: 'Ensemble Selection',
    description: 'Stacking ensemble of top 3 models (Linear, Ridge, XGBoost) with Ridge meta-learner for optimal performance.',
  },
  {
    step: 5,
    title: 'Fairness Analysis',
    description: 'Fairlearn demographic parity difference and equalized odds evaluation across gender and age groups with post-processing calibration.',
  },
  {
    step: 6,
    title: 'Conformal Prediction',
    description: 'Split conformal prediction for statistically valid 90% coverage intervals (q̂ = $22,333).',
  },
  {
    step: 7,
    title: 'SHAP Explainability',
    description: 'KernelExplainer for ensemble models providing global feature importance and local waterfall explanations.',
  },
]

const limitations = [
  'Synthetic data may not reflect real-world salary distributions and relationships',
  'Fairness metrics are proxies; cannot prove absence of all forms of discrimination',
  'SHAP explanations are model interpretations, not causal proofs',
  'Confidence intervals are statistical estimates, not guarantees',
  'Model requires retraining with real organizational data for production use',
  'Protected attributes limited to gender and age in current implementation',
  'Sample size for some intersectional groups may be too small for reliable metrics',
]

export function About() {
  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Hero */}
      <section className="text-center">
        <div className="inline-flex items-center space-x-2 px-4 py-2 rounded-full bg-primary-50 text-primary-700 text-sm font-medium mb-6">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500"></span>
          </span>
          <span>Responsible AI for Fair Compensation</span>
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-secondary-900 tracking-tight mb-6">
          About FairSalary AI
        </h1>
        <p className="text-xl text-secondary-600 max-w-2xl mx-auto">
          A responsible AI platform for fair, transparent, and explainable salary recommendations.
          Built with fairness auditing, SHAP explainability, and conformal prediction intervals.
        </p>
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/predict" className="btn-primary text-lg px-8 py-3 group">
            Try Prediction
            <ArrowRight className="w-5 h-5 ml-2 transition-transform group-hover:translate-x-1" aria-hidden="true" />
          </Link>
          <Link to="/fairness" className="btn-secondary text-lg px-8 py-3">
            View Fairness Dashboard
          </Link>
        </div>
      </section>

      {/* What We Do */}
      <section>
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-secondary-900 mb-4">What Does FairSalary AI Do?</h2>
          <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
            FairSalary AI helps organizations make fair, data-driven salary decisions by combining
            machine learning predictions with fairness auditing and explainability.
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
      </section>

      {/* How It Works */}
      <section>
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-secondary-900 mb-4">How It Works</h2>
          <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
            Our ML pipeline follows responsible AI practices from data to deployment.
          </p>
        </div>

        <div className="space-y-8">
          {methodologySteps.map((step) => (
            <div key={step.title} className="flex gap-6 p-6 card">
              <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center text-2xl font-bold">
                {step.step}
              </div>
              <div>
                <h3 className="text-xl font-semibold text-secondary-900 mb-2">{step.title}</h3>
                <p className="text-secondary-600">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Fairness Commitment */}
      <section className="bg-primary-50 rounded-2xl p-8 lg:p-12">
        <div className="max-w-3xl mx-auto text-center">
          <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-6">
            <Shield className="w-8 h-8 text-primary-600" aria-hidden="true" />
          </div>
          <h2 className="text-3xl font-bold text-secondary-900 mb-4">Our Commitment to Fairness</h2>
          <p className="text-lg text-secondary-600 mb-8 max-w-2xl mx-auto">
            FairSalary AI is built on the principle that compensation decisions should be transparent,
            auditable, and equitable. We don't just predict salaries—we audit for bias.
          </p>
          <div className="grid md:grid-cols-3 gap-6 mt-8">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" aria-hidden="true" />
              <span className="text-secondary-700">Protected attributes excluded from features</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" aria-hidden="true" />
              <span className="text-secondary-700">Demographic parity audited</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" aria-hidden="true" />
              <span className="text-secondary-700">Error rate parity checked</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" aria-hidden="true" />
              <span className="text-secondary-700">Post-processing calibration</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" aria-hidden="true" />
              <span className="text-secondary-700">SHAP transparency</span>
            </div>
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-6 h-6 text-success-500 flex-shrink-0" aria-hidden="true" />
              <span className="text-secondary-700">Conformal intervals</span>
            </div>
          </div>
        </div>
      </section>

      {/* Limitations */}
      <section>
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-secondary-900 mb-4">Limitations & Responsible Use</h2>
          <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
            Understanding the boundaries of AI-assisted salary recommendations is crucial for responsible deployment.
          </p>
        </div>

        <div className="card p-6 bg-warning-50 border border-warning-200">
          <h3 className="font-semibold text-warning-800 mb-4 flex items-center space-x-2">
            <Sparkles className="w-5 h-5" aria-hidden="true" />
            <span>Important Limitations</span>
          </h3>
          <ul className="list-disc list-inside space-y-2 text-warning-700">
            {limitations.map((limitation, i) => (
              <li key={i}>{limitation}</li>
            ))}
          </ul>
        </div>

        <div className="card p-6 bg-danger-50 border border-danger-200 mt-6">
          <h3 className="font-semibold text-danger-800 mb-3 flex items-center space-x-2">
            <Shield className="w-5 h-5" aria-hidden="true" />
            <span>Responsible Use Disclaimer</span>
          </h3>
          <p className="text-danger-700">
            <strong>This system provides AI-assisted salary recommendations based on synthetic demonstration data.</strong>
            It should not be used as the sole basis for employment, compensation, promotion, or other high-impact decisions.
            Predictions may contain errors or reflect biases present in the underlying data.
          </p>
          <p className="text-danger-600 mt-3">
            <strong>Privacy Notice:</strong> Do not upload confidential employee information. This application uses
            synthetic data for demonstration. In production, ensure compliance with GDPR, CCPA, and local privacy laws.
          </p>
        </div>
      </section>

      {/* Tech Stack */}
      <section>
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-secondary-900 mb-4">Technology Stack</h2>
          <p className="text-lg text-secondary-600 max-w-2xl mx-auto">
            Built with modern, production-ready technologies.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="card p-6">
            <h3 className="font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
              <Brain className="w-5 h-5 text-primary-600" aria-hidden="true" />
              <span>Machine Learning</span>
            </h3>
            <ul className="space-y-2 text-secondary-600 text-sm">
              <li>&bull; XGBoost, Random Forest, Gradient Boosting</li>
              <li>&bull; Scikit-learn pipelines & ColumnTransformer</li>
              <li>&bull; Optuna hyperparameter optimization</li>
              <li>&bull; Fairlearn for fairness metrics</li>
              <li>&bull; SHAP for explainability</li>
              <li>&bull; Conformal prediction intervals</li>
            </ul>
          </div>
          <div className="card p-6">
            <h3 className="font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
              <BarChart2 className="w-5 h-5 text-primary-600" aria-hidden="true" />
              <span>Backend</span>
            </h3>
            <ul className="space-y-2 text-secondary-600 text-sm">
              <li>&bull; FastAPI with Pydantic v2</li>
              <li>&bull; SQLAlchemy 2.0 + PostgreSQL</li>
              <li>&bull; JWT authentication with bcrypt</li>
              <li>&bull; Alembic migrations</li>
              <li>&bull; Uvicorn ASGI server</li>
            </ul>
          </div>
          <div className="card p-6">
            <h3 className="font-semibold text-secondary-900 mb-4 flex items-center space-x-2">
              <Users className="w-5 h-5 text-primary-600" aria-hidden="true" />
              <span>Frontend</span>
            </h3>
            <ul className="space-y-2 text-secondary-600 text-sm">
              <li>&bull; React 18 + TypeScript</li>
              <li>&bull; Vite for fast development</li>
              <li>&bull; Tailwind CSS for styling</li>
              <li>&bull; Recharts for visualizations</li>
              <li>&bull; React Router v6</li>
              <li>&bull; Axios for API communication</li>
            </ul>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-secondary-900 text-white rounded-2xl p-8 lg:p-12 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold mb-6">
          Ready to Build Fairer Compensation?
        </h2>
        <p className="text-secondary-300 text-lg mb-8 max-w-2xl mx-auto">
          Deploy FairSalary AI in your organization or use it as a reference for building
          responsible AI systems for HR and compensation.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/predict" className="bg-white text-secondary-900 hover:bg-secondary-100 px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
            Try Live Demo
          </Link>
          <Link to="https://github.com" target="_blank" rel="noopener noreferrer" className="border-2 border-white text-white hover:bg-secondary-800 px-8 py-3 rounded-lg font-semibold text-lg transition-colors">
            View on GitHub
          </Link>
        </div>
      </section>
    </div>
  )
}
