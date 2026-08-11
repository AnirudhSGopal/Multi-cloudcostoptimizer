import { create } from 'zustand'
import { apiClient } from '../services/api'

const useAuthStore = create((set) => ({
  user: null,
  token: localStorage.getItem('auth_token') || null,
  isAuthenticated: !!localStorage.getItem('auth_token'),
  isLoading: false,
  error: null,

  login: async (email, password) => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.post('/api/v1/auth/login', {
        email,
        password,
      })
      const { access_token, user } = response.data
      localStorage.setItem('auth_token', access_token)
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      })
      return { success: true }
    } catch (error) {
      const message =
        error.response?.data?.error || 'Login failed. Please try again.'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  signup: async (firstName, lastName, email, password, provider = 'viewer') => {
    set({ isLoading: true, error: null })
    try {
      // Step 1: Register the account
      await apiClient.post('/api/v1/auth/register', {
        email,
        password,
        username: `${firstName.toLowerCase()}.${lastName.toLowerCase()}`,
        role: provider.toLowerCase(),
      })

      // Step 2: Auto-login to get the access token (register doesn't return one)
      const loginResponse = await apiClient.post('/api/v1/auth/login', {
        email,
        password,
      })
      const { access_token, user } = loginResponse.data
      localStorage.setItem('auth_token', access_token)
      set({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
      })
      return { success: true }
    } catch (error) {
      const message =
        error.response?.data?.errors?.email?.[0] ||
        error.response?.data?.errors?.password?.[0] ||
        error.response?.data?.errors?.username?.[0] ||
        error.response?.data?.error ||
        'Sign up failed. Please try again.'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token')
    set({ user: null, token: null, isAuthenticated: false })
  },

  clearError: () => {
    set({ error: null })
  },

  fetchMe: async () => {
    const token = localStorage.getItem('auth_token')
    if (!token) return
    try {
      const response = await apiClient.get('/api/v1/auth/me')
      set({ user: response.data.user, isAuthenticated: true })
    } catch (error) {
      localStorage.removeItem('auth_token')
      set({ user: null, token: null, isAuthenticated: false })
    }
  },
}))

export default useAuthStore