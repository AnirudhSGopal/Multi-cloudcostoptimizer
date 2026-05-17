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

  signup: async (firstName, lastName, email, password, provider = 'AWS') => {
    set({ isLoading: true, error: null })
    try {
      const response = await apiClient.post('/api/v1/auth/register', {
        email,
        password,
        username: `${firstName.toLowerCase()}.${lastName.toLowerCase()}`,
        first_name: firstName,
        last_name: lastName,
        primary_provider: provider,
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
        error.response?.data?.error || 'Sign up failed. Please try again.'
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
}))

export default useAuthStore