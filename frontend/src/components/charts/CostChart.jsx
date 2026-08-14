import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import useCloudStore from '../../store/cloudStore'

const mockData = [
  { month: 'Oct', AWS: 4200, GCP: 2800, Azure: 3100 },
  { month: 'Nov', AWS: 3800, GCP: 3100, Azure: 2900 },
  { month: 'Dec', AWS: 5100, GCP: 2600, Azure: 3400 },
  { month: 'Jan', AWS: 4700, GCP: 3300, Azure: 3800 },
  { month: 'Feb', AWS: 4300, GCP: 3000, Azure: 3500 },
  { month: 'Mar', AWS: 3900, GCP: 2700, Azure: 3200 },
]

function buildChartData(costData) {
  if (!costData || costData.length === 0) return mockData

  const awsTotal = costData.filter(c => (c.provider || '').toLowerCase() === 'aws').reduce((a, c) => a + (c.monthly_cost || 0), 0)
  const gcpTotal = costData.filter(c => (c.provider || '').toLowerCase() === 'gcp').reduce((a, c) => a + (c.monthly_cost || 0), 0)
  const azureTotal = costData.filter(c => (c.provider || '').toLowerCase() === 'azure').reduce((a, c) => a + (c.monthly_cost || 0), 0)

  const months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
  const factors = [0.92, 0.96, 1.05, 1.02, 0.98, 1.00]

  return months.map((month, i) => ({
    month,
    AWS: Math.round((awsTotal || 0) * factors[i]),
    GCP: Math.round((gcpTotal || 0) * factors[i]),
    Azure: Math.round((azureTotal || 0) * factors[i]),
  }))
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#0f1320', border: '1px solid #1c2236', borderRadius: 8, padding: '10px 14px', fontSize: 11.5 }}>
      <p style={{ color: '#6e7d9c', marginBottom: 6, fontWeight: 600 }}>{label}</p>
      {payload.map(p => (
        <p key={p.name} style={{ color: p.color, marginBottom: 2 }}>
          {p.name}: <strong>${p.value.toLocaleString()}</strong>
        </p>
      ))}
    </div>
  )
}

const renderLegend = ({ payload }) => (
  <div style={{ display: 'flex', justifyContent: 'center', gap: 20, marginTop: 8 }}>
    {payload.map(entry => (
      <span key={entry.value} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#6e7d9c' }}>
        <span style={{ width: 20, height: 2, background: entry.color, display: 'inline-block', borderRadius: 2 }} />
        {entry.value}
      </span>
    ))}
  </div>
)

export default function CostChart({ data }) {
  const storeCostData = useCloudStore(s => s.costData)
  const chartData = data || buildChartData(storeCostData)

  const maxVal = Math.max(1, ...chartData.flatMap(d => [d.AWS || 0, d.GCP || 0, d.Azure || 0]))
  const yFormatter = maxVal < 1000 ? (v => `$${v}`) : (v => `$${(v/1000).toFixed(1)}k`)

  return (
    <ResponsiveContainer width="100%" height={240}>
      <AreaChart data={chartData} margin={{ top: 6, right: 4, left: -8, bottom: 0 }}>
        <defs>
          {[['awsGrad','#ff8c38'],['gcpGrad','#34aaff'],['azureGrad','#9d72ff']].map(([id, color]) => (
            <linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor={color} stopOpacity={0.25} />
              <stop offset="95%" stopColor={color} stopOpacity={0}    />
            </linearGradient>
          ))}
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1c2236" vertical={false} />
        <XAxis dataKey="month" tick={{ fill: '#3a4560', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#3a4560', fontSize: 11 }} axisLine={false} tickLine={false}
          tickFormatter={yFormatter} />
        <Tooltip content={<CustomTooltip />} />
        <Legend content={renderLegend} />
        <Area type="monotone" dataKey="AWS"   stroke="#ff8c38" strokeWidth={1.5} fill="url(#awsGrad)"   dot={false} />
        <Area type="monotone" dataKey="GCP"   stroke="#34aaff" strokeWidth={1.5} fill="url(#gcpGrad)"   dot={false} />
        <Area type="monotone" dataKey="Azure" stroke="#9d72ff" strokeWidth={1.5} fill="url(#azureGrad)" dot={false} />
      </AreaChart>
    </ResponsiveContainer>
  )
}