import { ArrowRight, Plug } from 'lucide-react'

export default function GCPCard({ cost = 0, storage = '0.0 GB', connected = false, onClick }) {
  return (
    <div className="provider-card" style={{ cursor: 'pointer', opacity: connected ? 1 : 0.75 }} onClick={onClick}>
      <div className="provider-card__header">
        <div className="provider-card__name">
          <span className="provider-dot" style={{ background: 'var(--gcp)' }} />
          Google Cloud Platform
        </div>
        {connected ? (
          <span className="provider-badge" style={{
            background: 'var(--green-dim)',
            color: 'var(--green)',
            display: 'flex', alignItems: 'center', gap: 3, fontSize: 11,
          }}>
            Live
          </span>
        ) : (
          <span className="provider-badge" style={{
            background: 'var(--bg-card-hover)',
            color: 'var(--text-muted)',
            display: 'flex', alignItems: 'center', gap: 3, fontSize: 11,
          }}>
            <Plug size={10} /> Disconnected
          </span>
        )}
      </div>

      <div>
        <div className="provider-card__cost">${cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        <div className="provider-card__meta">Monthly cost</div>
      </div>

      <div className="provider-card__storage" style={{ marginTop: 12 }}>
        <span className="provider-card__storage-label">Resources / Storage</span>
        <span className="provider-card__storage-val">{storage}</span>
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