import { useState, useMemo } from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import useCloudStore from '../../store/cloudStore'
import { Zap, TrendingDown, ArrowDownRight, Layers, ShieldAlert, Sparkles } from 'lucide-react'
import {
  STORAGE_CONFIG,
  TOTAL_STORAGE_GB,
  TOTAL_STORAGE_LABEL,
  TOTAL_STORAGE_STATUS,
  getProviderStorage,
} from '../../config/storageConfig'

const PROVIDER_COLORS = {
  AWS: { stroke: '#ff8c38', grad: 'awsGrad', bg: 'rgba(255, 140, 56, 0.15)', name: 'Amazon Web Services' },
  GCP: { stroke: '#34aaff', grad: 'gcpGrad', bg: 'rgba(52, 170, 255, 0.15)', name: 'Google Cloud Platform' },
  Azure: { stroke: '#9d72ff', grad: 'azureGrad', bg: 'rgba(157, 114, 255, 0.15)', name: 'Microsoft Azure' },
}

export const CENTRAL_PROVIDER_STORAGE = STORAGE_CONFIG

function buildChartData(costData, dailyTrend) {
  if (dailyTrend && dailyTrend.length > 0) {
    return dailyTrend.map(d => {
      const aws = Number(d.AWS) || 0
      const gcp = Number(d.GCP) || 0
      const azure = Number(d.Azure) || 0
      const total = typeof d.Total === 'number' && d.Total > 0 ? d.Total : Number((aws + gcp + azure).toFixed(2))
      return {
        ...d,
        label: d.formatted_date || d.date || d.day,
        day: d.day,
        day_num: d.day_num,
        formatted_date: d.formatted_date || d.date || d.day,
        AWS: aws,
        GCP: gcp,
        Azure: azure,
        Total: total,
        monthly_runrate: d.monthly_runrate || Math.round(total * 30),
        milestone: d.milestone,
        phase: d.phase,
        storage_aws: STORAGE_CONFIG.AWS.sizeGb,
        storage_gcp: STORAGE_CONFIG.GCP.sizeGb,
        storage_azure: STORAGE_CONFIG.Azure.sizeGb,
        storage_total: TOTAL_STORAGE_GB,
      }
    })
  }

  if (!costData || costData.length === 0) return []

  const awsTotal = costData.filter(c => (c.provider || '').toLowerCase() === 'aws').reduce((a, c) => a + (c.monthly_cost || 0), 0)
  const gcpTotal = costData.filter(c => (c.provider || '').toLowerCase() === 'gcp').reduce((a, c) => a + (c.monthly_cost || 0), 0)
  const azureTotal = costData.filter(c => (c.provider || '').toLowerCase() === 'azure').reduce((a, c) => a + (c.monthly_cost || 0), 0)

  const total = awsTotal + gcpTotal + azureTotal
  if (total === 0) return []
  return [{
    label: 'Current',
    AWS: awsTotal,
    GCP: gcpTotal,
    Azure: azureTotal,
    Total: total,
    storage_aws: STORAGE_CONFIG.AWS.sizeGb,
    storage_gcp: STORAGE_CONFIG.GCP.sizeGb,
    storage_azure: STORAGE_CONFIG.Azure.sizeGb,
    storage_total: TOTAL_STORAGE_GB,
  }]
}

// ── Realistic Glassmorphism Tooltip with Invariant Storage & 40/30/30 Breakdown ─
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null

  const row = payload[0]?.payload || {}
  const total = typeof row.Total === 'number' && row.Total > 0
    ? row.Total
    : payload.reduce((sum, p) => sum + (Number(p.value) || 0), 0)
  const phase = row.phase
  const milestone = row.milestone
  const dateStr = row.formatted_date || label

  return (
    <div style={{
      background: 'rgba(13, 16, 26, 0.96)',
      backdropFilter: 'blur(14px)',
      border: '1px solid rgba(79, 142, 247, 0.25)',
      boxShadow: '0 8px 32px rgba(0, 0, 0, 0.6), 0 0 16px rgba(79, 142, 247, 0.15)',
      borderRadius: 10,
      padding: '12px 16px',
      fontSize: 12,
      minWidth: 260,
      zIndex: 1000,
    }}>
      {/* Header: Date + Phase + Invariant Storage Badge */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, gap: 10 }}>
        <div>
          <div style={{ color: '#ffffff', fontWeight: 700, fontSize: 13 }}>{dateStr}</div>
          {row.day && <div style={{ color: '#64748b', fontSize: 10.5 }}>{row.day} of 30-Day Cycle</div>}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {phase && (
            <span style={{
              fontSize: 10, padding: '2px 8px', borderRadius: 6,
              background: phase === 'Optimized' ? 'rgba(34,197,94,0.18)' : phase === 'Optimizing' ? 'rgba(52,170,255,0.18)' : 'rgba(239,68,68,0.18)',
              border: `1px solid ${phase === 'Optimized' ? 'rgba(34,197,94,0.4)' : phase === 'Optimizing' ? 'rgba(52,170,255,0.4)' : 'rgba(239,68,68,0.4)'}`,
              color: phase === 'Optimized' ? '#4ade80' : phase === 'Optimizing' ? '#60a5fa' : '#f87171',
              fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.5,
            }}>
              {phase}
            </span>
          )}
          {phase === 'Optimized' && (
            <span style={{
              fontSize: 9.5, padding: '2px 6px', borderRadius: 4,
              background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.35)',
              color: '#7dd3fc', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 3
            }}>
              Storage unchanged
            </span>
          )}
        </div>
      </div>

      {/* Milestone notification */}
      {milestone && (
        <div style={{
          margin: '6px 0 10px 0',
          padding: '6px 8px',
          borderRadius: 6,
          background: milestone.includes('Anomaly') ? 'rgba(239, 68, 68, 0.12)' : 'rgba(79, 142, 247, 0.12)',
          border: `1px solid ${milestone.includes('Anomaly') ? 'rgba(239, 68, 68, 0.25)' : 'rgba(79, 142, 247, 0.25)'}`,
          fontSize: 11,
          color: milestone.includes('Anomaly') ? '#fca5a5' : '#93c5fd',
          display: 'flex', alignItems: 'center', gap: 6,
          lineHeight: 1.3,
        }}>
          <span>{milestone}</span>
        </div>
      )}

      {/* Multi-Cloud Provider Breakdown: Provider (share %) · Storage size · Daily cost */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, margin: '8px 0' }}>
        {payload.map(p => {
          const conf = PROVIDER_COLORS[p.name] || { stroke: p.color, name: p.name }
          const storageConf = getProviderStorage(p.name)
          const valNum = Number(p.value) || 0

          return (
            <div key={p.name} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '3px 0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: conf.stroke, flexShrink: 0 }} />
                <span style={{ color: '#f1f5f9', fontWeight: 600, fontSize: 11.5 }}>
                  {p.name} ({storageConf.shareLabel})
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ color: '#94a3b8', fontSize: 11, fontFamily: 'monospace' }}>
                  {storageConf.sizeLabel}
                </span>
                <span style={{ color: '#475569', fontSize: 10 }}>·</span>
                <strong style={{ color: '#ffffff', fontFamily: 'monospace', fontSize: 12 }}>
                  ${valNum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </strong>
              </div>
            </div>
          )
        })}
      </div>

      {/* Total spend & Total Storage line under Total Daily Spend */}
      <div style={{
        marginTop: 8,
        paddingTop: 8,
        borderTop: '1px solid rgba(255, 255, 255, 0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ color: '#64748b', fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>Total Daily Spend</div>
            <div style={{ color: phase === 'Optimized' ? '#4ade80' : '#ffffff', fontWeight: 800, fontSize: 14, fontFamily: 'monospace' }}>
              ${Number(total).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <div style={{ color: '#94a3b8', fontSize: 10.5, marginTop: 3, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span>{TOTAL_STORAGE_STATUS}</span>
            </div>
          </div>
          {row.monthly_runrate && (
            <div style={{ textAlign: 'right' }}>
              <div style={{ color: '#64748b', fontSize: 10, textTransform: 'uppercase', letterSpacing: 0.5 }}>Monthly Run-Rate</div>
              <div style={{ color: '#94a3b8', fontSize: 12, fontFamily: 'monospace', fontWeight: 600 }}>
                ${Number(row.monthly_runrate).toLocaleString()}
              </div>
              <div style={{ color: '#64748b', fontSize: 9.5, marginTop: 2 }}>
                30-day projection
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function CostChart({ data }) {
  const storeCostData = useCloudStore(s => s.costData)
  const storeDailyTrend = useCloudStore(s => s.dailyTrend)
  const chartData = data || buildChartData(storeCostData, storeDailyTrend)

  const [activeView, setActiveView] = useState('all') // 'all', 'AWS', 'GCP', 'Azure'

  const getPointSpend = (pt) => {
    if (!pt) return 0
    if (typeof pt.Total === 'number' && pt.Total > 0) return pt.Total
    const sum = (Number(pt.AWS) || 0) + (Number(pt.GCP) || 0) + (Number(pt.Azure) || 0)
    return Number(sum.toFixed(2))
  }

  // Summary calculations computed from baseline daily spend - optimized daily spend
  const stats = useMemo(() => {
    if (!chartData || chartData.length === 0) return null

    const baselinePt = chartData.find(d => d.phase === 'Baseline') || chartData[0]
    const optimizedPt = [...chartData].reverse().find(d => d.phase === 'Optimized') || chartData[chartData.length - 1]

    const baselineDaily = getPointSpend(baselinePt)
    const optimizedDaily = getPointSpend(optimizedPt)

    const dailySaved = Math.max(0, baselineDaily - optimizedDaily)
    const reductionPct = baselineDaily > 0 ? ((dailySaved / baselineDaily) * 100).toFixed(1) : '0.0'
    const monthlySaved = (dailySaved * 30).toFixed(2)

    return {
      baselineDaily,
      optimizedDaily,
      reductionPct,
      dailySaved: dailySaved.toFixed(2),
      monthlySaved,
      totalStorageGb: TOTAL_STORAGE_GB,
    }
  }, [chartData])

  // Formatter using $0, $50, $100, $150, $200 or one decimal place ($1.2k) without repeating
  const yFormatter = (val) => {
    if (val === 0) return '$0'
    if (val < 1000) {
      return `$${Math.round(val)}`
    }
    const kVal = val / 1000
    return kVal % 1 === 0 ? `$${kVal.toFixed(0)}k` : `$${kVal.toFixed(1)}k`
  }

  const TABS = [
    { id: 'all', label: STORAGE_CONFIG.Total.tabLabel },
    { id: 'AWS', label: STORAGE_CONFIG.AWS.tabLabel },
    { id: 'GCP', label: STORAGE_CONFIG.GCP.tabLabel },
    { id: 'Azure', label: STORAGE_CONFIG.Azure.tabLabel },
  ]

  if (!chartData?.length) {
    return (
      <div role="status" style={{ color: 'var(--text-muted)', padding: '24px 0', textAlign: 'center' }}>
        Cost history will appear after a cloud account is connected and synced.
      </div>
    )
  }

  return (
    <div style={{ width: '100%' }}>
      {/* ── Realistic Top Status Banner ────────────────────────────────── */}
      {stats && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: 10,
          marginBottom: 14,
          padding: '10px 14px',
          background: 'rgba(15, 19, 32, 0.75)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: 8,
        }}>
          <div>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Baseline Daily
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'monospace' }}>
              ${stats.baselineDaily.toFixed(2)}/day
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
              ${(stats.baselineDaily * 30).toLocaleString()}/mo rate
            </div>
            <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2, fontFamily: 'monospace' }}>
              {TOTAL_STORAGE_STATUS}
            </div>
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
              <span style={{ fontSize: 10.5, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Current Optimized
              </span>
              <span style={{
                fontSize: 9, padding: '1px 5px', borderRadius: 4,
                background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)',
                color: '#7dd3fc', fontWeight: 600,
              }}>
                Storage unchanged
              </span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--green)', fontFamily: 'monospace' }}>
              ${stats.optimizedDaily.toFixed(2)}/day
            </div>
            <div style={{ fontSize: 10, color: 'var(--green)', marginTop: 2 }}>
              ${(stats.optimizedDaily * 30).toLocaleString()}/mo rate
            </div>
            <div style={{ fontSize: 10, color: '#38bdf8', marginTop: 2, fontFamily: 'monospace' }}>
              {TOTAL_STORAGE_STATUS}
            </div>
          </div>

          <div>
            <div style={{ fontSize: 10.5, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Optimization Drop
            </div>
            <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--green)', display: 'flex', alignItems: 'center', gap: 3 }}>
              <TrendingDown size={15} /> -{stats.reductionPct}%
            </div>
            <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 2 }}>
              -${stats.dailySaved}/day saved
            </div>
            <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2, fontFamily: 'monospace' }}>
              {TOTAL_STORAGE_STATUS}
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start', gap: 4 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              fontSize: 11, padding: '4px 10px', borderRadius: 99,
              background: 'rgba(34, 197, 94, 0.14)', border: '1px solid rgba(34, 197, 94, 0.3)',
              color: 'var(--green)', fontWeight: 600,
            }}>
              <Zap size={11} /> +${Number(stats.monthlySaved).toLocaleString()}/mo Net Savings
            </span>
            <div style={{ fontSize: 10, color: '#7dd3fc', paddingLeft: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
              <span>📦 {TOTAL_STORAGE_STATUS}</span>
            </div>
          </div>
        </div>
      )}

      {/* ── View Controls Bar with Invariant Storage on Tabs ───────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveView(tab.id)}
              style={{
                background: activeView === tab.id ? 'var(--accent)' : 'var(--bg-elevated)',
                color: activeView === tab.id ? '#fff' : 'var(--text-secondary)',
                border: '1px solid',
                borderColor: activeView === tab.id ? 'var(--accent)' : 'var(--border)',
                padding: '5px 12px',
                borderRadius: 6,
                fontSize: 11.5,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 5,
              }}
            >
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 11, color: 'var(--text-muted)' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '2px 8px', borderRadius: 99,
            background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.25)',
            color: '#38bdf8', fontSize: 10.5, fontWeight: 600,
          }}>
            📦 {TOTAL_STORAGE_STATUS}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#ff8c38' }} /> AWS
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#34aaff' }} /> GCP
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: '#9d72ff' }} /> Azure
          </span>
        </div>
      </div>

      {/* ── Main Responsive Area Chart ───────────────────────────────── */}
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={chartData} margin={{ top: 12, right: 10, left: -10, bottom: 0 }}>
          <defs>
            <linearGradient id="awsGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff8c38" stopOpacity={0.40} />
              <stop offset="95%" stopColor="#ff8c38" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="gcpGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#34aaff" stopOpacity={0.40} />
              <stop offset="95%" stopColor="#34aaff" stopOpacity={0.02} />
            </linearGradient>
            <linearGradient id="azureGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#9d72ff" stopOpacity={0.40} />
              <stop offset="95%" stopColor="#9d72ff" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" vertical={false} />

          <XAxis
            dataKey="label"
            tick={{ fill: '#64748b', fontSize: 10.5 }}
            axisLine={{ stroke: 'rgba(255, 255, 255, 0.08)' }}
            tickLine={false}
            interval={chartData.length > 15 ? 3 : 0}
          />

          <YAxis
            tick={{ fill: '#64748b', fontSize: 10.5 }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
            tickFormatter={yFormatter}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Reference line marking AI Optimizer deployment on Day 12 */}
          {chartData.length >= 14 && (
            <ReferenceLine
              x={chartData[11]?.label}
              stroke="#34aaff"
              strokeDasharray="4 4"
              label={{
                value: '⚡ AI Optimizer Active',
                fill: '#60a5fa',
                fontSize: 10,
                position: 'insideTopLeft',
                offset: 10,
              }}
            />
          )}

          {(activeView === 'all' || activeView === 'AWS') && (
            <Area
              type="monotone"
              dataKey="AWS"
              name="AWS"
              stroke="#ff8c38"
              strokeWidth={2}
              fill="url(#awsGrad)"
              dot={false}
              activeDot={{ r: 4, stroke: '#ff8c38', strokeWidth: 2, fill: '#0f1320' }}
            />
          )}

          {(activeView === 'all' || activeView === 'GCP') && (
            <Area
              type="monotone"
              dataKey="GCP"
              name="GCP"
              stroke="#34aaff"
              strokeWidth={2}
              fill="url(#gcpGrad)"
              dot={false}
              activeDot={{ r: 4, stroke: '#34aaff', strokeWidth: 2, fill: '#0f1320' }}
            />
          )}

          {(activeView === 'all' || activeView === 'Azure') && (
            <Area
              type="monotone"
              dataKey="Azure"
              name="Azure"
              stroke="#9d72ff"
              strokeWidth={2}
              fill="url(#azureGrad)"
              dot={false}
              activeDot={{ r: 4, stroke: '#9d72ff', strokeWidth: 2, fill: '#0f1320' }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}