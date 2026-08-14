import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor — attach token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — automatic token refresh & global 401 handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const requestUrl = originalRequest?.url || ''
    const isAuthEndpoint =
      requestUrl.includes('/auth/login') ||
      requestUrl.includes('/auth/register') ||
      requestUrl.includes('/auth/refresh')

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken) {
        try {
          const refreshResponse = await axios.post(
            `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}/api/v1/auth/refresh`,
            {},
            {
              headers: {
                Authorization: `Bearer ${refreshToken}`,
              },
            }
          )

          const newAccessToken = refreshResponse.data.access_token
          if (newAccessToken) {
            localStorage.setItem('auth_token', newAccessToken)
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
            return api(originalRequest)
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      } else {
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export const apiClient = api
export default api