import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import CostAnalysis from './pages/CostAnalysis'
import SecurityAudit from './pages/SecurityAudit'
import Recommendations from './pages/Recommendations'
import Settings from './pages/Settings'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

function App() {
  // Read saved theme from localStorage, default to 'dark'
  const [theme, setTheme] = useState(
    () => localStorage.getItem('theme') || 'dark'
  )

  // Apply theme to <html> element whenever it changes
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () =>
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app-layout">
          <Sidebar />
          <div className="main-content">
            {/* Pass theme + toggle down to Navbar */}
            <Navbar theme={theme} toggleTheme={toggleTheme} />
            <div className="page-wrapper">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/cost-analysis" element={<CostAnalysis />} />
                <Route path="/security" element={<SecurityAudit />} />
                <Route path="/recommendations" element={<Recommendations />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </div>
        </div>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: theme === 'dark' ? '#111520' : '#ffffff',
              color:      theme === 'dark' ? '#eef0f6' : '#0f1320',
              border:     theme === 'dark' ? '1px solid #1e2640' : '1px solid #e2e5f0',
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