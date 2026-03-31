import { TrendingUp, ArrowRight } from 'lucide-react'

const sparkData = [2200, 2400, 2500, 2600, 2650, 2700]
const max = Math.max(...sparkData)

export default function GCPCard({ onClick }) {
  return (
    <div className="provider-card" style={{ cursor: 'pointer' }} onClick={onClick}>
      <div className="provider-card__header">
        <div className="provider-card__name">
          <span className="provider-dot" style={{ background: 'var(--gcp)' }} />
          Google Cloud Platform
        </div>
        <span className="provider-badge" style={{
          background: 'var(--red-dim)', color: 'var(--red)',
          display: 'flex', alignItems: 'center', gap: 3, fontSize: 11,
        }}>
          <TrendingUp size={10} /> 3.1%
        </span>
      </div>
      <div>
        <div className="provider-card__cost">$2,700</div>
        <div className="provider-card__meta">This month's cost</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 28, margin: '12px 0 4px' }}>
        {sparkData.map((v, i) => (
          <div key={i} style={{
            flex: 1, borderRadius: 2,
            height: `${Math.round((v / max) * 100)}%`,
            background: i === sparkData.length - 1 ? 'var(--gcp)' : 'var(--gcp-dim)',
          }} />
        ))}
      </div>
      <div className="provider-card__storage">
        <span className="provider-card__storage-label">Storage used</span>
        <span className="provider-card__storage-val">8.7 TB</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--accent)', marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)', cursor: 'pointer' }}>
        View breakdown <ArrowRight size={11} />
      </div>
    </div>
  )
}