import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

import useAuthStore from './store/authStore'
import Login from './pages/Login'
import LandingPage from './pages/LandingPage'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import CostAnalysis from './pages/CostAnalysis'
import SecurityAudit from './pages/SecurityAudit'
import Recommendations from './pages/Recommendations'
import Settings from './pages/Settings'
import AdminPanel from './pages/AdminPanel'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

// Private Route Component
function PrivateRoute({ children }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

// Admin Route Component
function AdminRoute({ children }) {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />
  return children
}

function AppLayout({ theme, toggleTheme }) {
  return (
    <div className="app-layout">
      <Sidebar />
      <div className="main-content">
        <Navbar theme={theme} toggleTheme={toggleTheme} />
        <div className="page-wrapper">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route
              path="/cost-analysis"
              element={
                <PrivateRoute>
                  <CostAnalysis />
                </PrivateRoute>
              }
            />
            <Route
              path="/security"
              element={
                <PrivateRoute>
                  <SecurityAudit />
                </PrivateRoute>
              }
            />
            <Route
              path="/recommendations"
              element={
                <PrivateRoute>
                  <Recommendations />
                </PrivateRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <PrivateRoute>
                  <Settings />
                </PrivateRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminPanel />
                </AdminRoute>
              }
            />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </div>
    </div>
  )
}

function App() {
  const { isAuthenticated, fetchMe } = useAuthStore()
  const [theme, setTheme] = useState(
    () => localStorage.getItem('theme') || 'dark'
  )

  useEffect(() => {
    fetchMe()
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () =>
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        {isAuthenticated ? (
          <AppLayout theme={theme} toggleTheme={toggleTheme} />
        ) : (
          <Routes>
            <Route path="/" element={<LandingPage theme={theme} toggleTheme={toggleTheme} />} />
            <Route path="/login" element={<Login />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        )}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: theme === 'dark' ? '#111520' : '#ffffff',
              color: theme === 'dark' ? '#eef0f6' : '#0f1320',
              border: theme === 'dark' ? '1px solid #1e2640' : '1px solid #e2e5f0',
              fontFamily: "'Inter', sans-serif",
              fontSize: '13px',
            },
          }}
        />
      </Router>
    </QueryClientProvider>
  )
}

export default App