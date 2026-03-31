import { NavLink } from 'react-router-dom'
import { LayoutDashboard, DollarSign, ShieldCheck, Lightbulb, Settings, Zap } from 'lucide-react'
import useCloudStore from '../store/cloudStore'

export default function Sidebar() {
  const { alerts, dismissedAlerts } = useCloudStore()
  const activeAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id))
  const criticalCount = activeAlerts.filter(a => a.type === 'critical').length

  const navItems = [
    { to: '/dashboard',       icon: LayoutDashboard, label: 'Dashboard'       },
    { to: '/cost-analysis',   icon: DollarSign,      label: 'Cost Analysis'   },
    { to: '/security',        icon: ShieldCheck,     label: 'Security Audit',  badge: activeAlerts.length, badgeColor: criticalCount > 0 ? 'var(--red)' : 'var(--yellow)' },
    { to: '/recommendations', icon: Lightbulb,       label: 'Recommendations', badge: 6 },
    { to: '/settings',        icon: Settings,        label: 'Settings'        },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <Zap size={14} color="#fff" />
        </div>
        <div>
          <div className="sidebar-logo-name">CloudOpt</div>
          <div className="sidebar-logo-sub">AI Cost &amp; Security</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, icon: Icon, label, badge, badgeColor }) => (
          <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'active' : ''}>
            <Icon size={14} />
            <span style={{ flex: 1 }}>{label}</span>
            {badge > 0 && (
              <span style={{
                fontSize: 10, fontWeight: 700,
                padding: '1px 6px', borderRadius: 99,
                background: badgeColor ? `${badgeColor}22` : 'var(--accent-dim)',
                color: badgeColor || 'var(--accent)',
                border: `1px solid ${badgeColor ? `${badgeColor}44` : 'var(--accent-glow)'}`,
                fontFamily: 'JetBrains Mono, monospace',
                lineHeight: 1.6,
              }}>
                {badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div style={{ padding: '10px 18px', borderTop: '1px solid var(--border)' }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '7px 10px', borderRadius: 7,
          background: 'var(--green-dim)', border: '1px solid rgba(46,204,142,0.2)',
          fontSize: 11, color: 'var(--green)', fontWeight: 500,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%',
            background: 'var(--green)',
            boxShadow: '0 0 6px var(--green)',
            animation: 'pulse 2s ease-in-out infinite',
            flexShrink: 0,
          }} />
          AI Engine Active
        </div>
      </div>

      <div className="sidebar-footer">v1.0.0 · 3 providers connected</div>
    </aside>
  )
}