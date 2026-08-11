import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Plug } from 'lucide-react'
import CostChart from '../components/charts/CostChart'
import useCloudStore from '../store/cloudStore'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts'
import Button from '../components/common/Button'

const PROVIDER_HEX = { aws: '#ff8c38', gcp: '#34aaff', azure: '#9d72ff', AWS: '#ff8c38', GCP: '#34aaff', Azure: '#9d72ff' }
const RANGES    = ['7d', '30d', '90d', '1y']
const PROVIDERS = ['all', 'AWS', 'GCP', 'Azure']

export default function CostAnalysis() {
  const { dateRange, setDateRange, costData, accounts, fetchAccounts, syncAllAccounts, costLoading, costError } = useCloudStore()
  const [activeProvider, setActiveProvider] = useState('all')
  const [activeRange, setActiveRange]       = useState('30d')
  const navigate = useNavigate()

  useEffect(() => {
    fetchAccounts().then(() => syncAllAccounts())
  }, [fetchAccounts, syncAllAccounts])

  // Process live cost data
  const normalizedData = (costData || []).map(item => ({
    service: item.service,
    cost: item.monthly_cost,
    provider: (item.provider || 'aws').toUpperCase(),
    color: PROVIDER_HEX[item.provider?.toLowerCase()] || 'var(--accent)'
  }))

  const filtered = activeProvider === 'all'
    ? normalizedData
    : normalizedData.filter(d => d.provider === activeProvider.toUpperCase())

  const totalCost = filtered.reduce((a, b) => a + b.cost, 0)
  const grandTotal = normalizedData.reduce((a, b) => a + b.cost, 0)

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
                Connect your AWS, GCP, or Azure credentials in Settings to query live multi-cloud cost breakdowns.
              </div>
            </div>
          </div>
          <Button onClick={() => navigate('/settings')} icon={ArrowRight}>
            Connect Provider
          </Button>
        </div>
      )}

      {/* Error notification if billing export or API query fails */}
      {costError && (
        <div style={{
          padding: '10px 14px', borderRadius: 8,
          background: 'var(--red-dim)', border: '1px solid rgba(239,68,68,0.3)',
          color: 'var(--red)', fontSize: 12, marginBottom: 16,
        }}>
          ⚠️ {costError}
        </div>
      )}

      {/* Filter bar */}
      <div className="filter-bar">
        <span className="filter-label">Provider</span>
        {PROVIDERS.map(p => (
          <button key={p} className={`filter-btn ${activeProvider === p ? 'active' : ''}`}
            onClick={() => setActiveProvider(p)}>
            {p === 'all' ? 'All' : p}
          </button>
        ))}
        <div className="filter-bar-right">
          <span className="filter-label">Range</span>
          {RANGES.map(r => (
            <button key={r} className={`filter-btn ${activeRange === r ? 'active-outline' : ''}`}
              onClick={() => { setActiveRange(r); setDateRange(r) }}>
              {r}
            </button>
          ))}
        </div>
      </div>

      {/* Cost trend */}
      <div className="card">
        <div className="card__title">Cost trend over time</div>
        <CostChart />
      </div>

      {/* Charts + table */}
      <div className="cost-two-col">
        <div className="card">
          <div className="card__title">Cost by service</div>
          {filtered.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={filtered} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="service"
                  tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                  axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                  axisLine={false} tickLine={false}
                  tickFormatter={v => `$${v.toFixed(0)}`} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: 'var(--text-secondary)', marginBottom: 4 }}
                  formatter={(val, name, props) => [`$${val.toLocaleString()}`, props.payload.provider]}
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                />
                <Bar dataKey="cost" radius={[4, 4, 0, 0]}>
                  {filtered.map((entry, i) => (
                    <Cell key={i} fill={PROVIDER_HEX[entry.provider] || '#ff8c38'} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              {costLoading ? 'Loading cost data...' : 'No service cost metrics available.'}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card__title">Service breakdown</div>
          {filtered.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Service</th>
                  <th>Provider</th>
                  <th>Cost/mo</th>
                  <th>% of total</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row, i) => (
                  <tr key={i}>
                    <td className="td-strong">{row.service}</td>
                    <td>
                      <span className={`badge badge-${row.provider.toLowerCase()}`}>{row.provider}</span>
                    </td>
                    <td className="td-mono td-strong">${row.cost.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="td-mono" style={{ color: 'var(--text-muted)' }}>
                      {grandTotal > 0 ? Math.round((row.cost / grandTotal) * 100) : 0}%
                    </td>
                  </tr>
                ))}
                <tr>
                  <td colSpan={2} style={{ color: 'var(--text-muted)', fontWeight: 500, fontSize: 11 }}>
                    Total ({filtered.length} services)
                  </td>
                  <td className="td-total td-mono">
                    ${totalCost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td />
                </tr>
              </tbody>
            </table>
          ) : (
            <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
              {costLoading ? 'Syncing live cost data...' : 'Connect your cloud credentials to see service cost breakdowns.'}
            </div>
          )}

          <button
            onClick={() => navigate('/recommendations')}
            className="btn btn-sm btn-ghost"
            style={{ marginTop: 12, width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 5 }}
          >
            See AI savings recommendations <ArrowRight size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}