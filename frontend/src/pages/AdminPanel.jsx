import { useState, useEffect, useCallback } from 'react'
import {
  Users, Cloud, Shield, BarChart3, Activity,
  Search, ChevronLeft, ChevronRight, Trash2, X,
  CheckCircle, XCircle, AlertTriangle, RefreshCw,
  Database, Bot, Key, Server
} from 'lucide-react'
import useAdminStore from '../store/adminStore'
import toast from 'react-hot-toast'

// ═══════════════════════════════════════════════════════════════════════════════
//  TAB NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════════

const TABS = [
  { id: 'users',    label: 'Users',          icon: Users },
  { id: 'accounts', label: 'Cloud Accounts', icon: Cloud },
  { id: 'scans',    label: 'Scans',          icon: Shield },
  { id: 'stats',    label: 'Platform Stats', icon: BarChart3 },
  { id: 'health',   label: 'System Health',  icon: Activity },
]

// ═══════════════════════════════════════════════════════════════════════════════
//  CONFIRM MODAL
// ═══════════════════════════════════════════════════════════════════════════════

function ConfirmModal({ open, title, message, onConfirm, onCancel, danger = false }) {
  if (!open) return null
  return (
    <div className="admin-modal-overlay" onClick={onCancel}>
      <div className="admin-modal" onClick={e => e.stopPropagation()}>
        <div className="admin-modal-header">
          <AlertTriangle size={18} color={danger ? 'var(--red)' : 'var(--yellow)'} />
          <span>{title}</span>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: 13, lineHeight: 1.6, margin: '12px 0 20px' }}>
          {message}
        </p>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button className="admin-btn admin-btn-ghost" onClick={onCancel}>Cancel</button>
          <button
            className={`admin-btn ${danger ? 'admin-btn-danger' : 'admin-btn-primary'}`}
            onClick={onConfirm}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  PAGINATION
// ═══════════════════════════════════════════════════════════════════════════════

function Pagination({ page, pages, total, onPageChange }) {
  if (pages <= 1) return null
  return (
    <div className="admin-pagination">
      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{total} total</span>
      <div style={{ display: 'flex', gap: 4 }}>
        <button
          className="admin-btn admin-btn-ghost admin-btn-sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeft size={14} />
        </button>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)', padding: '4px 8px' }}>
          {page} / {pages}
        </span>
        <button
          className="admin-btn admin-btn-ghost admin-btn-sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  STATUS BADGE
// ═══════════════════════════════════════════════════════════════════════════════

function StatusBadge({ status, label }) {
  const colors = {
    healthy: 'var(--green)', connected: 'var(--green)', completed: 'var(--green)',
    active: 'var(--green)', true: 'var(--green)', admin: 'var(--accent)',
    unhealthy: 'var(--red)', error: 'var(--red)', failed: 'var(--red)',
    false: 'var(--red)', disabled: 'var(--red)',
    pending: 'var(--yellow)', running: 'var(--yellow)', warning: 'var(--yellow)',
    analyst: 'var(--azure)', viewer: 'var(--text-secondary)',
    degraded: 'var(--yellow)', cancelled: 'var(--text-muted)',
  }
  const color = colors[String(status).toLowerCase()] || 'var(--text-muted)'
  return (
    <span className="admin-badge" style={{
      color,
      background: `color-mix(in srgb, ${color} 12%, transparent)`,
      border: `1px solid color-mix(in srgb, ${color} 25%, transparent)`,
    }}>
      {label || String(status)}
    </span>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  USERS TAB
// ═══════════════════════════════════════════════════════════════════════════════

function UsersTab() {
  const {
    users, usersTotal, usersPage, usersPages, usersLoading, usersSearch,
    fetchUsers, setUsersSearch, setUsersPage, updateUser, deleteUser
  } = useAdminStore()

  const [deleteModal, setDeleteModal] = useState(null)
  const [searchInput, setSearchInput] = useState(usersSearch)

  useEffect(() => { fetchUsers() }, [])

  const handleSearch = useCallback((e) => {
    e.preventDefault()
    setUsersSearch(searchInput)
    setUsersPage(1)
    fetchUsers({ search: searchInput, page: 1 })
  }, [searchInput])

  const handleRoleChange = async (userId, newRole) => {
    const result = await updateUser(userId, { role: newRole })
    if (result.success) toast.success('Role updated')
    else toast.error(result.error)
  }

  const handleToggleActive = async (userId, currentActive) => {
    const result = await updateUser(userId, { is_active: !currentActive })
    if (result.success) toast.success(currentActive ? 'User disabled' : 'User enabled')
    else toast.error(result.error)
  }

  const handleDelete = async () => {
    if (!deleteModal) return
    const result = await deleteUser(deleteModal.id)
    if (result.success) toast.success('User deleted')
    else toast.error(result.error)
    setDeleteModal(null)
  }

  const handlePageChange = (p) => {
    setUsersPage(p)
    fetchUsers({ page: p })
  }

  return (
    <div className="admin-tab-content">
      <form onSubmit={handleSearch} className="admin-search-bar">
        <Search size={14} color="var(--text-muted)" />
        <input
          type="text"
          placeholder="Search users by name or email..."
          value={searchInput}
          onChange={e => setSearchInput(e.target.value)}
        />
        <button type="submit" className="admin-btn admin-btn-primary admin-btn-sm">Search</button>
      </form>

      <div className="admin-table-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Username</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Created</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {usersLoading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <RefreshCw size={16} className="admin-spinner" /> Loading...
              </td></tr>
            ) : users.length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No users found</td></tr>
            ) : users.map(u => (
              <tr key={u.id}>
                <td>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text-muted)' }}>
                    #{u.id}
                  </span>
                </td>
                <td style={{ fontWeight: 600 }}>{u.username}</td>
                <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                <td>
                  <select
                    className="admin-select"
                    value={u.role}
                    onChange={e => handleRoleChange(u.id, e.target.value)}
                  >
                    <option value="admin">Admin</option>
                    <option value="analyst">Analyst</option>
                    <option value="viewer">Viewer</option>
                  </select>
                </td>
                <td>
                  <button
                    className="admin-btn admin-btn-ghost admin-btn-sm"
                    onClick={() => handleToggleActive(u.id, u.is_active)}
                    title={u.is_active ? 'Click to disable' : 'Click to enable'}
                  >
                    <StatusBadge status={u.is_active ? 'active' : 'disabled'} label={u.is_active ? 'Active' : 'Disabled'} />
                  </button>
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button
                    className="admin-btn admin-btn-ghost admin-btn-sm admin-btn-icon-danger"
                    onClick={() => setDeleteModal(u)}
                    title="Delete user"
                  >
                    <Trash2 size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={usersPage} pages={usersPages} total={usersTotal} onPageChange={handlePageChange} />

      <ConfirmModal
        open={!!deleteModal}
        title="Delete User"
        message={`Are you sure you want to delete "${deleteModal?.username}"? This will permanently remove all their cloud accounts, metrics, and scan history.`}
        danger
        onConfirm={handleDelete}
        onCancel={() => setDeleteModal(null)}
      />
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  CLOUD ACCOUNTS TAB
// ═══════════════════════════════════════════════════════════════════════════════

function CloudAccountsTab() {
  const {
    cloudAccounts, cloudAccountsTotal, cloudAccountsPage, cloudAccountsPages,
    cloudAccountsLoading, cloudAccountsProvider, cloudAccountsStatus,
    fetchCloudAccounts, setCloudAccountsProvider, setCloudAccountsStatus,
  } = useAdminStore()

  useEffect(() => { fetchCloudAccounts() }, [])

  const handleProviderFilter = (p) => {
    setCloudAccountsProvider(p)
    fetchCloudAccounts({ provider: p, page: 1 })
  }

  const handleStatusFilter = (s) => {
    setCloudAccountsStatus(s)
    fetchCloudAccounts({ status: s, page: 1 })
  }

  const handlePageChange = (p) => {
    fetchCloudAccounts({ page: p })
  }

  const providerColors = { aws: 'var(--aws)', gcp: 'var(--gcp)', azure: 'var(--azure)' }

  return (
    <div className="admin-tab-content">
      <div className="admin-filters">
        <div className="admin-filter-group">
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Provider</span>
          <div className="admin-filter-chips">
            {['', 'aws', 'gcp', 'azure'].map(p => (
              <button
                key={p}
                className={`admin-chip ${cloudAccountsProvider === p ? 'active' : ''}`}
                onClick={() => handleProviderFilter(p)}
              >
                {p || 'All'}
              </button>
            ))}
          </div>
        </div>
        <div className="admin-filter-group">
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Status</span>
          <div className="admin-filter-chips">
            {['', 'connected', 'error', 'pending'].map(s => (
              <button
                key={s}
                className={`admin-chip ${cloudAccountsStatus === s ? 'active' : ''}`}
                onClick={() => handleStatusFilter(s)}
              >
                {s || 'All'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="admin-table-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>User</th>
              <th>Provider</th>
              <th>Label</th>
              <th>Status</th>
              <th>Last Synced</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {cloudAccountsLoading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <RefreshCw size={16} className="admin-spinner" /> Loading...
              </td></tr>
            ) : cloudAccounts.length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No cloud accounts found</td></tr>
            ) : cloudAccounts.map(acc => (
              <tr key={acc.id}>
                <td>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text-muted)' }}>
                    #{acc.id}
                  </span>
                </td>
                <td style={{ fontWeight: 600 }}>{acc.username}</td>
                <td>
                  <span style={{
                    color: providerColors[acc.provider] || 'var(--text-primary)',
                    fontWeight: 700, fontSize: 11, textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}>
                    {acc.provider}
                  </span>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{acc.account_label || '—'}</td>
                <td><StatusBadge status={acc.status} /></td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {acc.last_synced_at ? new Date(acc.last_synced_at).toLocaleString() : 'Never'}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {acc.created_at ? new Date(acc.created_at).toLocaleDateString() : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={cloudAccountsPage} pages={cloudAccountsPages} total={cloudAccountsTotal} onPageChange={handlePageChange} />
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SCANS TAB
// ═══════════════════════════════════════════════════════════════════════════════

function ScansTab() {
  const {
    scans, scansTotal, scansPage, scansPages, scansLoading, scansStatus,
    fetchScans, setScansStatus,
  } = useAdminStore()

  useEffect(() => { fetchScans() }, [])

  const handleStatusFilter = (s) => {
    setScansStatus(s)
    fetchScans({ status: s, page: 1 })
  }

  const handlePageChange = (p) => {
    fetchScans({ page: p })
  }

  return (
    <div className="admin-tab-content">
      <div className="admin-filters">
        <div className="admin-filter-group">
          <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Status</span>
          <div className="admin-filter-chips">
            {['', 'pending', 'running', 'completed', 'failed', 'cancelled'].map(s => (
              <button
                key={s}
                className={`admin-chip ${scansStatus === s ? 'active' : ''}`}
                onClick={() => handleStatusFilter(s)}
              >
                {s || 'All'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="admin-table-wrapper">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>User</th>
              <th>Repository</th>
              <th>Status</th>
              <th>Score</th>
              <th>Findings</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {scansLoading ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                <RefreshCw size={16} className="admin-spinner" /> Loading...
              </td></tr>
            ) : scans.length === 0 ? (
              <tr><td colSpan={7} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>No scans found</td></tr>
            ) : scans.map(scan => (
              <tr key={scan.id}>
                <td>
                  <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: 'var(--text-muted)' }}>
                    #{scan.id}
                  </span>
                </td>
                <td style={{ fontWeight: 600 }}>{scan.username}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: 12, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {scan.repo_url}
                </td>
                <td><StatusBadge status={scan.status} /></td>
                <td>
                  {scan.security_score != null ? (
                    <span style={{
                      fontFamily: 'JetBrains Mono, monospace', fontSize: 12, fontWeight: 700,
                      color: scan.security_score >= 85 ? 'var(--green)' : scan.security_score >= 60 ? 'var(--yellow)' : 'var(--red)',
                    }}>
                      {scan.security_score}
                    </span>
                  ) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                </td>
                <td style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: 'var(--text-secondary)' }}>
                  {scan.total_findings ?? '—'}
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {scan.created_at ? new Date(scan.created_at).toLocaleString() : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={scansPage} pages={scansPages} total={scansTotal} onPageChange={handlePageChange} />
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  PLATFORM STATS TAB
// ═══════════════════════════════════════════════════════════════════════════════

function StatsTab() {
  const { stats, statsLoading, fetchStats } = useAdminStore()

  useEffect(() => { fetchStats() }, [])

  if (statsLoading || !stats) {
    return (
      <div className="admin-tab-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <RefreshCw size={20} className="admin-spinner" color="var(--text-muted)" />
      </div>
    )
  }

  const cards = [
    { label: 'Total Users', value: stats.total_users, sub: `${stats.active_users} active`, color: 'var(--accent)' },
    { label: 'Cloud Accounts', value: stats.total_cloud_accounts, sub: `${stats.sync_error_rate}% error rate`, color: 'var(--green)' },
    { label: 'Total Scans', value: stats.total_scans, sub: `${stats.completed_scans} completed`, color: 'var(--azure)' },
    { label: 'Findings', value: stats.total_recommendations, sub: 'vulnerabilities found', color: 'var(--yellow)' },
    { label: 'Total Cost Tracked', value: `$${stats.total_estimated_savings.toLocaleString()}`, sub: 'across platform', color: 'var(--aws)' },
    { label: 'Failed Scans', value: stats.failed_scans, sub: 'scan failures', color: 'var(--red)' },
  ]

  // Simple bar chart data for accounts by provider
  const providerData = Object.entries(stats.accounts_by_provider || {})
  const maxProviderCount = Math.max(1, ...providerData.map(([, v]) => v))

  return (
    <div className="admin-tab-content">
      <div className="admin-stats-grid">
        {cards.map(card => (
          <div key={card.label} className="admin-stat-card">
            <div className="admin-stat-label">{card.label}</div>
            <div className="admin-stat-value" style={{ color: card.color }}>{card.value}</div>
            <div className="admin-stat-sub">{card.sub}</div>
          </div>
        ))}
      </div>

      {providerData.length > 0 && (
        <div className="admin-chart-card">
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            Cloud Accounts by Provider
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {providerData.map(([provider, count]) => {
              const colors = { aws: 'var(--aws)', gcp: 'var(--gcp)', azure: 'var(--azure)' }
              const color = colors[provider] || 'var(--accent)'
              return (
                <div key={provider} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <span style={{
                    width: 50, fontSize: 11, fontWeight: 700,
                    textTransform: 'uppercase', letterSpacing: 0.5,
                    color, textAlign: 'right',
                  }}>
                    {provider}
                  </span>
                  <div style={{ flex: 1, height: 28, background: 'var(--bg-input)', borderRadius: 6, overflow: 'hidden', position: 'relative' }}>
                    <div style={{
                      height: '100%',
                      width: `${(count / maxProviderCount) * 100}%`,
                      background: `linear-gradient(90deg, color-mix(in srgb, ${color} 30%, transparent), ${color})`,
                      borderRadius: 6,
                      transition: 'width 0.6s ease',
                      minWidth: count > 0 ? 28 : 0,
                    }} />
                    <span style={{
                      position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
                      fontSize: 12, fontWeight: 700, fontFamily: 'JetBrains Mono, monospace',
                      color: 'var(--text-secondary)',
                    }}>
                      {count}
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  SYSTEM HEALTH TAB
// ═══════════════════════════════════════════════════════════════════════════════

function HealthTab() {
  const { health, healthLoading, fetchHealth } = useAdminStore()

  useEffect(() => { fetchHealth() }, [])

  if (healthLoading || !health) {
    return (
      <div className="admin-tab-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 200 }}>
        <RefreshCw size={20} className="admin-spinner" color="var(--text-muted)" />
      </div>
    )
  }

  const checkIcons = {
    database: Database,
    gemini_api: Bot,
    encryption_key: Key,
    celery_redis: Server,
  }

  const checkLabels = {
    database: 'Database',
    gemini_api: 'Gemini API',
    encryption_key: 'Encryption Key',
    celery_redis: 'Celery / Redis',
  }

  return (
    <div className="admin-tab-content">
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
        <div className={`admin-health-overall ${health.overall}`}>
          {health.overall === 'healthy' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
          <span>System {health.overall === 'healthy' ? 'Healthy' : 'Degraded'}</span>
        </div>
        <button className="admin-btn admin-btn-ghost admin-btn-sm" onClick={fetchHealth}>
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      <div className="admin-health-grid">
        {Object.entries(health.checks).map(([key, check]) => {
          const Icon = checkIcons[key] || Activity
          const isHealthy = check.status === 'healthy'
          return (
            <div key={key} className={`admin-health-card ${isHealthy ? 'healthy' : 'unhealthy'}`}>
              <div className="admin-health-card-header">
                <Icon size={18} />
                <span>{checkLabels[key] || key}</span>
                <div className="admin-health-indicator-wrapper">
                  {isHealthy
                    ? <CheckCircle size={16} color="var(--green)" />
                    : <XCircle size={16} color="var(--red)" />
                  }
                </div>
              </div>
              <div className="admin-health-card-status">
                <StatusBadge status={check.status} />
              </div>
              <p className="admin-health-card-message">{check.message}</p>
            </div>
          )
        })}
      </div>

      {health.checked_at && (
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 16, textAlign: 'right' }}>
          Last checked: {new Date(health.checked_at).toLocaleString()}
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════════
//  MAIN ADMIN PANEL
// ═══════════════════════════════════════════════════════════════════════════════

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('users')

  const renderTab = () => {
    switch (activeTab) {
      case 'users':    return <UsersTab />
      case 'accounts': return <CloudAccountsTab />
      case 'scans':    return <ScansTab />
      case 'stats':    return <StatsTab />
      case 'health':   return <HealthTab />
      default:         return <UsersTab />
    }
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <div>
          <h1 className="admin-title">Admin Panel</h1>
          <p className="admin-subtitle">Platform management & system oversight</p>
        </div>
      </div>

      <div className="admin-tabs">
        {TABS.map(tab => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              className={`admin-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <Icon size={14} />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      <div className="admin-content">
        {renderTab()}
      </div>
    </div>
  )
}
