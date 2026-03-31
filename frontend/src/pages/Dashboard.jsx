import { useNavigate } from 'react-router-dom'
import { DollarSign, HardDrive, ShieldAlert, TrendingDown, ArrowRight, Zap } from 'lucide-react'
import AlertBanner from '../components/security/AlertBanner'
import AWSCard from '../components/cloud/AWSCard'
import GCPCard from '../components/cloud/GCPCard'
import AzureCard from '../components/cloud/AzureCard'
import CostChart from '../components/charts/CostChart'
import StorageChart from '../components/charts/StorageChart'
import SecurityGauge from '../components/charts/SecurityGauge'
import useCloudStore from '../store/cloudStore'

const STAT_CARDS = [
  {
    label: 'Total Monthly Cost', value: '$9,800', sub: 'All providers combined',
    delta: '▲ $780 vs last month', deltaUp: true,
    icon: DollarSign, iconBg: 'var(--blue-dim)', iconColor: 'var(--blue)',
    insight: 'AWS driving 40% of spend',
  },
  {
    label: 'Total Storage Used', value: '34.0 TB', sub: 'Across AWS, GCP, Azure',
    delta: '▼ 1.2% vs last month', deltaUp: false,
    icon: HardDrive, iconBg: 'var(--azure-dim)', iconColor: 'var(--azure)',
    insight: '8.2 TB infrequently accessed',
  },
  {
    label: 'Security Alerts', value: '3', sub: '2 critical · 1 warning',
    delta: 'Immediate action required', deltaUp: true,
    icon: ShieldAlert, iconBg: 'var(--red-dim)', iconColor: 'var(--red)',
    valueColor: 'var(--red)', insight: 'Azure public access unresolved',
  },
  {
    label: 'Potential Savings', value: '$1,240', sub: '6 AI recommendations',
    delta: 'S3 tiering + Glacier top sources', deltaUp: false,
    icon: TrendingDown, iconBg: 'var(--green-dim)', iconColor: 'var(--green)',
    valueColor: 'var(--green)', insight: 'Act now to save this month',
  },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const { alerts, dismissedAlerts, dismissAlert } = useCloudStore()
  const activeAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id))

  return (
    <div className="page-content">

      {/* ── AI Insight Banner ── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 14px',
        background: 'linear-gradient(135deg, var(--accent-dim), var(--azure-dim))',
        border: '1px solid var(--accent-glow)',
        borderRadius: 'var(--r-md)', fontSize: 12,
      }}>
        <Zap size={14} color="var(--accent)" style={{ flexShrink: 0 }} />
        <span style={{ color: 'var(--text-secondary)' }}>
          AI detected an <strong style={{ color: 'var(--text-primary)' }}>anomalous spend spike (+23%)</strong> in
          AWS us-east-1 over 48h — likely unoptimized S3 lifecycle policies on 4 buckets (8.2 TB).
          Estimated savings: <strong style={{ color: 'var(--green)' }}>$312/mo</strong>.
        </span>
        <button
          onClick={() => navigate('/recommendations')}
          className="btn btn-sm btn-ghost"
          style={{ marginLeft: 'auto', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 5 }}
        >
          View fix <ArrowRight size={11} />
        </button>
      </div>

      {/* ── Active Alerts ── */}
      {activeAlerts.length > 0 && (
        <div>
          <div className="section-header">
            <span className="section-title">Active alerts ({activeAlerts.length})</span>
            <button className="btn btn-sm btn-ghost" onClick={() => navigate('/security')}
              style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
              View all <ArrowRight size={11} />
            </button>
          </div>
          <div className="alerts-stack">
            {activeAlerts.map(alert => (
              <AlertBanner key={alert.id} alert={alert} onDismiss={dismissAlert} />
            ))}
          </div>
        </div>
      )}

      {/* ── Stat Cards ── */}
      <div>
        <div className="section-header">
          <span className="section-title">At a glance</span>
        </div>
        <div className="stats-grid">
          {STAT_CARDS.map((s) => {
            const Icon = s.icon
            return (
              <div key={s.label} className="stat-card">
                <div className="stat-card__header">
                  <div className="stat-card__label">{s.label}</div>
                  <div className="stat-card__icon" style={{ background: s.iconBg }}>
                    <Icon size={15} color={s.iconColor} />
                  </div>
                </div>
                <div className="stat-card__value" style={{ color: s.valueColor || 'var(--text-primary)' }}>
                  {s.value}
                </div>
                <div className="stat-card__sub">{s.sub}</div>
                <div style={{
                  marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--border)',
                  fontSize: 11,
                  color: s.deltaUp ? 'var(--red)' : s.label === 'Potential Savings' ? 'var(--green)' : 'var(--text-muted)',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <span>{s.delta}</span>
                  <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>{s.insight}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ── Provider Cards ── */}
      <div>
        <div className="section-header">
          <span className="section-title">Provider breakdown</span>
          <button className="btn btn-sm btn-ghost" onClick={() => navigate('/cost-analysis')}
            style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11 }}>
            Full analysis <ArrowRight size={11} />
          </button>
        </div>
        <div className="providers-grid">
          <AWSCard   onClick={() => navigate('/cost-analysis')} />
          <GCPCard   onClick={() => navigate('/cost-analysis')} />
          <AzureCard onClick={() => navigate('/cost-analysis')} />
        </div>
      </div>

      {/* ── Charts ── */}
      <div>
        <div className="section-header">
          <span className="section-title">Trends &amp; distribution</span>
        </div>
        <div className="charts-grid">
          <div className="card chart-card">
            <div className="card__title">Cost trend — 6 months</div>
            <CostChart />
          </div>
          <div className="card chart-card">
            <div className="card__title">Storage distribution</div>
            <StorageChart />
          </div>
          <div className="card chart-card">
            <div className="card__title">Security score</div>
            <SecurityGauge score={74} />
            <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { label: 'Encryption', val: 92, color: 'var(--green)' },
                { label: 'IAM',        val: 68, color: 'var(--yellow)' },
                { label: 'Logging',    val: 55, color: 'var(--yellow)' },
              ].map(({ label, val, color }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11 }}>
                  <span style={{ color: 'var(--text-muted)', width: 64 }}>{label}</span>
                  <div style={{ flex: 1, height: 3, background: 'var(--border-mid)', borderRadius: 99 }}>
                    <div style={{ width: `${val}%`, height: '100%', background: color, borderRadius: 99 }} />
                  </div>
                  <span style={{ color, fontFamily: 'JetBrains Mono, monospace', fontSize: 10.5, width: 28, textAlign: 'right' }}>
                    {val}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}