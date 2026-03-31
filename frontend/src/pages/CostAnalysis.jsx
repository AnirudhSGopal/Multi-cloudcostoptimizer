import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import CostChart from '../components/charts/CostChart'
import useCloudStore from '../store/cloudStore'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts'

const SERVICE_DATA = [
  { service: 'S3',         cost: 1240, provider: 'AWS',   color: 'var(--aws)'   },
  { service: 'EC2',        cost: 2100, provider: 'AWS',   color: 'var(--aws)'   },
  { service: 'GCS',        cost: 870,  provider: 'GCP',   color: 'var(--gcp)'   },
  { service: 'BigQuery',   cost: 1030, provider: 'GCP',   color: 'var(--gcp)'   },
  { service: 'Blob Store', cost: 980,  provider: 'Azure', color: 'var(--azure)' },
  { service: 'AKS',        cost: 1420, provider: 'Azure', color: 'var(--azure)' },
]

const PROVIDER_HEX = { AWS: '#ff8c38', GCP: '#34aaff', Azure: '#9d72ff' }
const RANGES    = ['7d', '30d', '90d', '1y']
const PROVIDERS = ['all', 'AWS', 'GCP', 'Azure']
const TOTAL     = SERVICE_DATA.reduce((a, b) => a + b.cost, 0)

export default function CostAnalysis() {
  const { dateRange, setDateRange } = useCloudStore()
  const [activeProvider, setActiveProvider] = useState('all')
  const [activeRange, setActiveRange]       = useState('30d')
  const navigate = useNavigate()

  const filtered = activeProvider === 'all'
    ? SERVICE_DATA
    : SERVICE_DATA.filter(d => d.provider === activeProvider)

  return (
    <div className="page-content">

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
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={filtered} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="service"
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                axisLine={false} tickLine={false} />
              <YAxis
                tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                axisLine={false} tickLine={false}
                tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ color: 'var(--text-secondary)', marginBottom: 4 }}
                formatter={(val, name, props) => [`$${val.toLocaleString()}`, props.payload.provider]}
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              />
              <Bar dataKey="cost" radius={[4, 4, 0, 0]}>
                {filtered.map((entry, i) => (
                  <Cell key={i} fill={PROVIDER_HEX[entry.provider]} fillOpacity={0.85} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card__title">Service breakdown</div>
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
                  <td className="td-mono td-strong">${row.cost.toLocaleString()}</td>
                  <td className="td-mono" style={{ color: 'var(--text-muted)' }}>
                    {Math.round((row.cost / TOTAL) * 100)}%
                  </td>
                </tr>
              ))}
              <tr>
                <td colSpan={2} style={{ color: 'var(--text-muted)', fontWeight: 500, fontSize: 11 }}>
                  Total ({filtered.length} services)
                </td>
                <td className="td-total td-mono">
                  ${filtered.reduce((a, b) => a + b.cost, 0).toLocaleString()}
                </td>
                <td />
              </tr>
            </tbody>
          </table>
          <button
            onClick={() => navigate('/recommendations')}
            className="btn btn-sm btn-ghost"
            style={{ marginTop: 12, width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 5 }}
          >
            See savings recommendations <ArrowRight size={12} />
          </button>
        </div>
      </div>
    </div>
  )
}