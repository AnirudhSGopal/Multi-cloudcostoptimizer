import { useLocation } from 'react-router-dom'
import { Bell, RefreshCw, Sun, Moon } from 'lucide-react'
import useCloudStore from '../store/cloudStore'

const pageMeta = {
  '/dashboard':       { title: 'Dashboard',       sub: 'Real-time overview across all cloud providers' },
  '/cost-analysis':   { title: 'Cost Analysis',   sub: 'Detailed spending breakdown by service and provider' },
  '/security':        { title: 'Security Audit',  sub: 'Threats, compliance checks and active alerts' },
  '/recommendations': { title: 'Recommendations', sub: 'AI-powered cost and security optimizations' },
  '/settings':        { title: 'Settings',        sub: 'Cloud credentials and system preferences' },
}

export default function Navbar({ theme, toggleTheme }) {
  const { pathname } = useLocation()
  const { alerts, dismissedAlerts } = useCloudStore()
  const page = pageMeta[pathname] ?? { title: 'CloudOpt', sub: '' }
  const activeAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id))
  const criticalCount = activeAlerts.filter(a => a.type === 'critical').length

  return (
    <header className="navbar">
      <div>
        <div className="navbar-title">{page.title}</div>
        {page.sub && <div className="navbar-sub">{page.sub}</div>}
      </div>
      <div className="navbar-actions">
        <button className="nav-icon-btn theme-toggle" onClick={toggleTheme} title="Toggle theme">
          {theme === 'dark' ? <Sun size={13} /> : <Moon size={13} />}
        </button>
        <button className="nav-icon-btn" title="Refresh data">
          <RefreshCw size={13} />
        </button>
        <button className="nav-icon-btn" title={`${activeAlerts.length} active alerts`} style={{ position: 'relative' }}>
          <Bell size={13} />
          {criticalCount > 0 && (
            <span className="notif-dot" style={{
              position: 'absolute', top: 5, right: 5,
              width: 5, height: 5,
              background: 'var(--red)',
              borderRadius: '50%',
              border: '1.5px solid var(--bg-surface)',
            }} />
          )}
        </button>
        <div className="nav-avatar" title="User menu">
          <span style={{ fontSize: 10, fontWeight: 700, color: '#fff' }}>AU</span>
        </div>
      </div>
    </header>
  )
}