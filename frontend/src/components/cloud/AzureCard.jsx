import { TrendingDown, ArrowRight } from 'lucide-react'

const sparkData = [3400, 3300, 3200, 3350, 3180, 3200]
const max = Math.max(...sparkData)

export default function AzureCard({ onClick }) {
  return (
    <div className="provider-card" style={{ cursor: 'pointer' }} onClick={onClick}>
      <div className="provider-card__header">
        <div className="provider-card__name">
          <span className="provider-dot" style={{ background: 'var(--azure)' }} />
          Microsoft Azure
        </div>
        <span className="provider-badge" style={{
          background: 'var(--green-dim)', color: 'var(--green)',
          display: 'flex', alignItems: 'center', gap: 3, fontSize: 11,
        }}>
          <TrendingDown size={10} /> 2.4%
        </span>
      </div>
      <div>
        <div className="provider-card__cost">$3,200</div>
        <div className="provider-card__meta">This month's cost</div>
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 3, height: 28, margin: '12px 0 4px' }}>
        {sparkData.map((v, i) => (
          <div key={i} style={{
            flex: 1, borderRadius: 2,
            height: `${Math.round((v / max) * 100)}%`,
            background: i === sparkData.length - 1 ? 'var(--azure)' : 'var(--azure-dim)',
          }} />
        ))}
      </div>
      <div className="provider-card__storage">
        <span className="provider-card__storage-label">Storage used</span>
        <span className="provider-card__storage-val">11.1 TB</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--accent)', marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--border)', cursor: 'pointer' }}>
        View breakdown <ArrowRight size={11} />
      </div>
    </div>
  )
}