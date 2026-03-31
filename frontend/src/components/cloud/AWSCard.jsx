import { TrendingDown, TrendingUp, ArrowRight } from 'lucide-react'

const sparkData = [3100, 3400, 3600, 3500, 3700, 3900]
const max = Math.max(...sparkData)

export default function AWSCard({ onClick }) {
  const delta = 7.2
  const isUp = delta > 0

  return (
    <div className="provider-card" style={{ cursor: 'pointer' }} onClick={onClick}>
      <div className="provider-card__header">
        <div className="provider-card__name">
          <span className="provider-dot" style={{ background: 'var(--aws)' }} />
          Amazon Web Services
        </div>
        <span className="provider-badge" style={{
          background: isUp ? 'var(--red-dim)' : 'var(--green-dim)',
          color: isUp ? 'var(--red)' : 'var(--green)',
          display: 'flex', alignItems: 'center', gap: 3, fontSize: 11,
        }}>
          {isUp ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
          {delta}%
        </span>
      </div>

      <div>
        <div className="provider-card__cost">$3,900</div>
        <div className="provider-card__meta">This month's cost</div>
      </div>

      {/* Sparkline */}
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 28, margin: '12px 0 4px' }}>
        {sparkData.map((v, i) => (
          <div key={i} style={{
            flex: 1, borderRadius: 2,
            height: `${Math.round((v / max) * 100)}%`,
            background: i === sparkData.length - 1 ? 'var(--aws)' : 'var(--aws-dim)',
            transition: 'height 0.3s ease',
          }} />
        ))}
      </div>

      <div className="provider-card__storage">
        <span className="provider-card__storage-label">Storage used</span>
        <span className="provider-card__storage-val">14.2 TB</span>
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 4,
        fontSize: 11, color: 'var(--accent)', marginTop: 10,
        paddingTop: 10, borderTop: '1px solid var(--border)',
        cursor: 'pointer',
      }}>
        View breakdown <ArrowRight size={11} />
      </div>
    </div>
  )
}