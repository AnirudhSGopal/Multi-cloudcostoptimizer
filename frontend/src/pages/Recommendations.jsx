import { useState } from 'react'
import { DollarSign, ShieldCheck, HardDrive, ChevronRight, Zap } from 'lucide-react'

const RECS = [
  { id: 1, category: 'cost',     provider: 'AWS',   priority: 'high',
    title: 'Enable S3 Intelligent-Tiering',
    description: 'Move infrequently accessed objects in 12 S3 buckets to Intelligent-Tiering automatically.',
    saving: 340, effort: 'Low',  impact: '8.2 TB data, 60% retrieval cost reduction' },
  { id: 2, category: 'security', provider: 'Azure', priority: 'critical',
    title: 'Disable public access on prod-assets blob',
    description: "Container 'prod-assets' has anonymous public read access. Restrict to private.",
    saving: 0,   effort: 'Low',  impact: 'Data exposure risk — public internet readable' },
  { id: 3, category: 'cost',     provider: 'Azure', priority: 'high',
    title: 'Delete orphaned blob snapshots',
    description: '47 blob snapshots no longer associated with active blobs consuming billable storage.',
    saving: 210, effort: 'Low',  impact: '47 snapshots, immediate cost elimination' },
  { id: 4, category: 'security', provider: 'GCP',   priority: 'critical',
    title: 'Enable uniform bucket-level access',
    description: 'Disable legacy ACLs on 3 GCP buckets to prevent IAM misconfiguration.',
    saving: 0,   effort: 'Low',  impact: 'IAM inconsistency across 3 buckets' },
  { id: 5, category: 'cost',     provider: 'GCP',   priority: 'medium',
    title: 'Compress and partition BigQuery tables',
    description: 'Apply table partitioning and clustering to 5 large BigQuery tables.',
    saving: 480, effort: 'Medium', impact: '5 tables, 40% query cost reduction' },
  { id: 6, category: 'storage',  provider: 'AWS',   priority: 'medium',
    title: 'Archive old S3 objects to Glacier',
    description: 'Objects older than 90 days in 4 S3 buckets can be archived for 80% cost reduction.',
    saving: 210, effort: 'Medium', impact: '4 buckets, ~3.1 TB archivable data' },
]

const CAT_ICON = {
  cost:     { Icon: DollarSign,  bg: 'var(--blue-dim)',  color: 'var(--blue)'  },
  security: { Icon: ShieldCheck, bg: 'var(--red-dim)',   color: 'var(--red)'   },
  storage:  { Icon: HardDrive,   bg: 'var(--azure-dim)', color: 'var(--azure)' },
}

const FILTERS = ['all', 'cost', 'security', 'storage']
const totalSavings = RECS.reduce((a, r) => a + r.saving, 0)

export default function Recommendations() {
  const [filter, setFilter] = useState('all')
  const filtered = filter === 'all' ? RECS : RECS.filter(r => r.category === filter)
  const criticalCount = RECS.filter(r => r.priority === 'critical').length

  return (
    <div className="page-content">

      {/* Summary */}
      <div className="summary-grid">
        <div className="summary-card">
          <div className="summary-card__label">Total recommendations</div>
          <div className="summary-card__value" style={{ color: 'var(--blue)' }}>{RECS.length}</div>
        </div>
        <div className="summary-card">
          <div className="summary-card__label">Potential monthly savings</div>
          <div className="summary-card__value" style={{ color: 'var(--green)' }}>${totalSavings.toLocaleString()}</div>
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
          {filtered.length} recommendations · sorted by priority
        </span>
      </div>

      {/* Cards */}
      <div className="rec-list">
        {filtered.map((rec) => {
          const cat = CAT_ICON[rec.category]
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
                    <span className="rec-card__saving">+ ${rec.saving}/mo savings</span>
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
    </div>
  )
}