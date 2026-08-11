import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { DollarSign, HardDrive, ShieldAlert, TrendingDown, ArrowRight, Zap, Plug } from 'lucide-react'
import AlertBanner from '../components/security/AlertBanner'
import AWSCard from '../components/cloud/AWSCard'
import GCPCard from '../components/cloud/GCPCard'
import AzureCard from '../components/cloud/AzureCard'
import CostChart from '../components/charts/CostChart'
import StorageChart from '../components/charts/StorageChart'
import SecurityGauge from '../components/charts/SecurityGauge'
import useCloudStore from '../store/cloudStore'
import Button from '../components/common/Button'

export default function Dashboard() {
  const navigate = useNavigate()
  const {
    alerts,
    dismissedAlerts,
    dismissAlert,
    securityScore,
    accounts,
    costData,
    resources,
    recommendations,
    costLoading,
    fetchAccounts,
    syncAllAccounts,
  } = useCloudStore()

  useEffect(() => {
    fetchAccounts().then(() => {
      syncAllAccounts()
    })
  }, [fetchAccounts, syncAllAccounts])

  const activeAlerts = alerts.filter(a => !dismissedAlerts.includes(a.id))
  const criticalCount = activeAlerts.filter(a => a.type === 'critical').length
  const warningCount = activeAlerts.filter(a => a.type === 'warning').length

  // Calculate live values from connected cloud accounts
  const totalCost = (costData || []).reduce((acc, curr) => acc + (curr.monthly_cost || 0), 0)
  const totalSavings = (recommendations || []).reduce((acc, curr) => acc + (curr.estimated_monthly_savings || 0), 0)
  const totalResourcesCount = (resources || []).length

  const awsCost = (costData || []).filter(c => c.provider === 'aws').reduce((a, c) => a + c.monthly_cost, 0)
  const gcpCost = (costData || []).filter(c => c.provider === 'gcp').reduce((a, c) => a + c.monthly_cost, 0)
  const azureCost = (costData || []).filter(c => c.provider === 'azure').reduce((a, c) => a + c.monthly_cost, 0)

  const hasAWS = accounts.some(a => a.provider === 'aws')
  const hasGCP = accounts.some(a => a.provider === 'gcp')
  const hasAzure = accounts.some(a => a.provider === 'azure')

  const STAT_CARDS = [
    {
      label: 'Total Monthly Cost',
      value: `$${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      sub: accounts.length > 0 ? `${accounts.length} cloud account(s) connected` : 'No accounts connected',
      delta: costLoading ? 'Syncing...' : `${costData.length} active service metrics`,
      deltaUp: false,
      icon: DollarSign, iconBg: 'var(--blue-dim)', iconColor: 'var(--blue)',
      insight: accounts.length > 0 ? 'Live billing data' : 'Connect in Settings',
    },
    {
      label: 'Discovered Resources',
      value: `${totalResourcesCount}`,
      sub: 'Across compute & storage',
      delta: `${resources.filter(r => r.status === 'stopped' || r.status === 'unattached').length} idle / unattached`,
      deltaUp: false,
      icon: HardDrive, iconBg: 'var(--azure-dim)', iconColor: 'var(--azure)',
      insight: 'Real-time discovery',
    },
    {
      label: 'Security Alerts',
      value: activeAlerts.length.toString(),
      sub: `${criticalCount} critical · ${warningCount} warning`,
      delta: criticalCount > 0 ? 'Immediate action required' : 'Review recommended',
      deltaUp: criticalCount > 0,
      icon: ShieldAlert, iconBg: criticalCount > 0 ? 'var(--red-dim)' : 'var(--yellow-dim)', iconColor: criticalCount > 0 ? 'var(--red)' : 'var(--yellow)',
      valueColor: criticalCount > 0 ? 'var(--red)' : 'var(--text-primary)',
      insight: criticalCount > 0 ? 'Critical vulnerabilities found' : 'Security posture stable',
    },
    {
      label: 'AI Cost Savings',
      value: `$${totalSavings.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      sub: `${recommendations.length} optimization recommendation(s)`,
      delta: 'Deterministic rule calculation',
      deltaUp: false,
      icon: TrendingDown, iconBg: 'var(--green-dim)', iconColor: 'var(--green)',
      valueColor: 'var(--green)', insight: 'Ready to optimize',
    },
  ]

  return (
    <div className="page-content">

      {/* ── Empty State Banner if no accounts ── */}
      {accounts.length === 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 16,
          padding: '16px 20px',
          background: 'linear-gradient(135deg, rgba(52,170,255,0.1), rgba(157,114,255,0.1))',
          border: '1px solid var(--accent-glow)',
          borderRadius: 'var(--r-md)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Plug size={20} color="var(--accent)" />
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
                No Cloud Accounts Connected
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                Connect your AWS, GCP, or Azure accounts in Settings to view live multi-cloud billing, resource discovery, and AI optimization recommendations.
              </div>
            </div>
          </div>
          <Button onClick={() => navigate('/settings')} icon={ArrowRight}>
            Connect Provider
          </Button>
        </div>
      )}

      {/* ── AI Insight Banner ── */}
      {recommendations.length > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '10px 14px',
          background: 'linear-gradient(135deg, var(--accent-dim), var(--azure-dim))',
          border: '1px solid var(--accent-glow)',
          borderRadius: 'var(--r-md)', fontSize: 12,
        }}>
          <Zap size={14} color="var(--accent)" style={{ flexShrink: 0 }} />
          <span style={{ color: 'var(--text-secondary)' }}>
            AI Cost Optimizer detected <strong style={{ color: 'var(--text-primary)' }}>{recommendations.length} optimization opportunities</strong>.
            Top recommendation: <strong style={{ color: 'var(--text-primary)' }}>{recommendations[0]?.title}</strong>.
            Estimated savings: <strong style={{ color: 'var(--green)' }}>${totalSavings.toFixed(2)}/mo</strong>.
          </span>
          <button
            onClick={() => navigate('/recommendations')}
            className="btn btn-sm btn-ghost"
            style={{ marginLeft: 'auto', flexShrink: 0, display: 'flex', alignItems: 'center', gap: 5 }}
          >
            View fix <ArrowRight size={11} />
          </button>
        </div>
      )}

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
                  color: s.deltaUp ? 'var(--red)' : s.label === 'AI Cost Savings' ? 'var(--green)' : 'var(--text-muted)',
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
          <AWSCard
            cost={awsCost}
            storage={`${resources.filter(r => r.provider === 'aws').length} resources`}
            connected={hasAWS}
            onClick={() => navigate('/cost-analysis')}
          />
          <GCPCard
            cost={gcpCost}
            storage={`${resources.filter(r => r.provider === 'gcp').length} resources`}
            connected={hasGCP}
            onClick={() => navigate('/cost-analysis')}
          />
          <AzureCard
            cost={azureCost}
            storage={`${resources.filter(r => r.provider === 'azure').length} resources`}
            connected={hasAzure}
            onClick={() => navigate('/cost-analysis')}
          />
        </div>
      </div>

      {/* ── Charts ── */}
      <div>
        <div className="section-header">
          <span className="section-title">Trends &amp; distribution</span>
        </div>
        <div className="charts-grid">
          <div className="card chart-card">
            <div className="card__title">Cost trend — monthly</div>
            <CostChart />
          </div>
          <div className="card chart-card">
            <div className="card__title">Storage distribution</div>
            <StorageChart />
          </div>
          <div className="card chart-card">
            <div className="card__title">Security score</div>
            <SecurityGauge score={securityScore} />
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