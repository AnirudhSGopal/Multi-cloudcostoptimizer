import { useNavigate } from 'react-router-dom'
import { ShieldCheck, ShieldAlert, ShieldX, Lock, ArrowRight } from 'lucide-react'
import AlertBanner from '../components/security/AlertBanner'
import ComplianceTable from '../components/security/ComplianceTable'
import SecurityGauge from '../components/charts/SecurityGauge'
import useCloudStore from '../store/cloudStore'

const SCORES = [
  { label: 'AWS',     score: 82, icon: ShieldCheck, color: 'var(--green)',  status: 'Good'    },
  { label: 'GCP',     score: 68, icon: ShieldAlert, color: 'var(--yellow)', status: 'Review'  },
  { label: 'Azure',   score: 71, icon: ShieldX,     color: 'var(--yellow)', status: 'Review'  },
  { label: 'Overall', score: 74, icon: Lock,        color: 'var(--blue)',   status: 'Moderate' },
]

export default function SecurityAudit() {
  const { alerts, dismissedAlerts, dismissAlert } = useCloudStore()
  const activeAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id))

  return (
    <div className="page-content">

      {/* Alerts */}
      {activeAlerts.length > 0 && (
        <div>
          <div className="section-header">
            <span className="section-title">Active alerts ({activeAlerts.length})</span>
          </div>
          <div className="alerts-stack">
            {activeAlerts.map(alert => (
              <AlertBanner key={alert.id} alert={alert} onDismiss={dismissAlert} />
            ))}
          </div>
        </div>
      )}

      {/* Score cards */}
      <div>
        <div className="section-header">
          <span className="section-title">Security scores by provider</span>
        </div>
        <div className="score-grid">
          {SCORES.map((s) => {
            const Icon = s.icon
            return (
              <div key={s.label} className="card">
                <div className="score-card__header">
                  <span className="score-card__label">{s.label}</span>
                  <Icon size={15} color={s.color} />
                </div>
                <div className="score-card__gauge">
                  <SecurityGauge score={s.score} label="" size={90} />
                </div>
                <div className="score-card__status" style={{ color: s.color }}>
                  {s.status}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Compliance */}
      <div className="card">
        <div className="section-header" style={{ marginBottom: 0 }}>
          <span className="card__title" style={{ margin: 0 }}>Compliance check results</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Last scanned 5 min ago</span>
        </div>
        <ComplianceTable />
      </div>

    </div>
  )
}