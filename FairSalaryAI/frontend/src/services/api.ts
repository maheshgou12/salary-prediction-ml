import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) throw new Error('No refresh token')

        const response = await axios.post(`${API_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        })

        const { access_token, refresh_token } = response.data
        localStorage.setItem('access_token', access_token)
        localStorage.setItem('refresh_token', refresh_token)

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access_token}`
        }

        return api(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export const api = {
  // Auth
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },

  register: async (data: { email: string; password: string; full_name: string }) => {
    const response = await api.post('/auth/register', data)
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },

  refreshToken: async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },

  // Predictions
  predict: async (data: any) => {
    const response = await api.post('/predict', data)
    return response.data
  },

  getHistory: async (page = 1, pageSize = 20) => {
    const response = await api.get('/predict', { params: { page, page_size: pageSize } })
    return response.data
  },

  getPrediction: async (id: number) => {
    const response = await api.get(`/predict/${id}`)
    return response.data
  },

  // Fairness
  getFairnessDashboard: async () => {
    const response = await api.get('/fairness')
    return response.data
  },

  getAttributeFairness: async (attribute: string) => {
    const response = await api.get(`/fairness/attribute/${attribute}`)
    return response.data
  },

  getIntersectionalFairness: async () => {
    const response = await api.get('/fairness/intersectional')
    return response.data
  },

  getProxyAnalysis: async () => {
    const response = await api.get('/fairness/proxy')
    return response.data
  },

  // Model
  getModelMetrics: async () => {
    const response = await api.get('/model/metrics')
    return response.data
  },

  // Health
  healthCheck: async () => {
    const response = await api.get('/health')
    return response.data
  },
}