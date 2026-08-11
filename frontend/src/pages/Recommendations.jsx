import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { DollarSign, ShieldCheck, HardDrive, ChevronRight, Zap, Plug, ArrowRight } from 'lucide-react'
import useCloudStore from '../store/cloudStore'
import Button from '../components/common/Button'

const CAT_ICON = {
  cost:     { Icon: DollarSign,  bg: 'var(--blue-dim)',  color: 'var(--blue)'  },
  security: { Icon: ShieldCheck, bg: 'var(--red-dim)',   color: 'var(--red)'   },
  storage:  { Icon: HardDrive,   bg: 'var(--azure-dim)', color: 'var(--azure)' },
}

const FILTERS = ['all', 'cost', 'security', 'storage']

export default function Recommendations() {
  const { recommendations, accounts, fetchAccounts, syncAllAccounts, costLoading } = useCloudStore()
  const [filter, setFilter] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    fetchAccounts().then(() => syncAllAccounts())
  }, [fetchAccounts, syncAllAccounts])

  const normalizedRecs = (recommendations || []).map(r => ({
    id: r.id || Math.random().toString(),
    category: r.category || 'cost',
    provider: (r.provider || 'aws').toUpperCase(),
    priority: r.priority || 'medium',
    title: r.title,
    description: r.description,
    impact: r.impact_statement || 'Optimization opportunity',
    saving: r.estimated_monthly_savings || 0,
    effort: r.effort || 'Low',
  }))

  const filtered = filter === 'all'
    ? normalizedRecs
    : normalizedRecs.filter(r => r.category === filter)

  const totalSavings = normalizedRecs.reduce((a, r) => a + r.saving, 0)
  const criticalCount = normalizedRecs.filter(r => r.priority === 'critical').length

  return (
    <div className="page-content">

      {/* Empty State Banner if no accounts connected */}
      {accounts.length === 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
          padding: '16px 20px',
          background: 'linear-gradient(135deg, rgba(52,170,255,0.1), rgba(157,114,255,0.1))',
          border: '1px solid var(--accent-glow)',
          borderRadius: 'var(--r-md)', marginBottom: 16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Plug size={20} color="var(--accent)" />
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                No Cloud Accounts Connected
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                Connect your cloud accounts in Settings to run AI cost optimization & resource discovery.
              </div>
            </div>
          </div>
          <Button onClick={() => navigate('/settings')} icon={ArrowRight}>
            Connect Provider
          </Button>
        </div>
      )}

      {/* Summary Cards */}
      <div className="summary-grid">
        <div className="summary-card">
          <div className="summary-card__label">Total recommendations</div>
          <div className="summary-card__value" style={{ color: 'var(--blue)' }}>{normalizedRecs.length}</div>
        </div>
        <div className="summary-card">
          <div className="summary-card__label">Potential monthly savings</div>
          <div className="summary-card__value" style={{ color: 'var(--green)' }}>
            ${totalSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-card__label">Critical issues</div>
          <div className="summary-card__value" style={{ color: 'var(--red)' }}>{criticalCount}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        {FILTERS.map(f => (
          <button key={f} className={`filter-btn ${filter === f ? 'active' : ''}`}
            onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>
          {filtered.length} recommendations · rule-based calculations + Gemini AI insights
        </span>
      </div>

      {/* Cards */}
      {filtered.length > 0 ? (
        <div className="rec-list">
          {filtered.map((rec) => {
            const cat = CAT_ICON[rec.category] || CAT_ICON.cost
            const CatIcon = cat.Icon
            return (
              <div key={rec.id} className="rec-card">
                <div className="rec-card__icon" style={{ background: cat.bg }}>
                  <CatIcon size={16} color={cat.color} />
                </div>
                <div className="rec-card__body">
                  <div className="rec-card__title-row">
                    <span className="rec-card__title">{rec.title}</span>
                    <span className={`badge badge-${rec.priority}`}>{rec.priority}</span>
                    <span className={`badge badge-${rec.provider.toLowerCase()}`}>{rec.provider}</span>
                  </div>
                  <p className="rec-card__desc">{rec.description}</p>
                  <div style={{
                    fontSize: 11, color: 'var(--text-muted)',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--r-sm)',
                    padding: '4px 8px', marginBottom: 8,
                    display: 'inline-flex', alignItems: 'center', gap: 5,
                  }}>
                    <Zap size={10} color="var(--accent)" />
                    Impact: <span style={{ color: 'var(--text-secondary)' }}>{rec.impact}</span>
                  </div>
                  <div className="rec-card__meta">
                    {rec.saving > 0 && (
                      <span className="rec-card__saving">+ ${rec.saving.toFixed(2)}/mo savings</span>
                    )}
                    {rec.saving === 0 && (
                      <span style={{ color: 'var(--red)', fontWeight: 600, fontSize: 11 }}>Security critical</span>
                    )}
                    <span className="rec-card__effort">Effort: {rec.effort}</span>
                  </div>
                </div>
                <ChevronRight size={15} className="rec-card__chevron" />
              </div>
            )
          })}
        </div>
      ) : (
        <div style={{ padding: '60px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
          {costLoading ? 'Running AI cost & resource optimization...' : 'No optimization recommendations found.'}
        </div>
      )}
    </div>
  )
}