import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'

const mockData = [
  { name: 'AWS S3',          value: 42, color: '#f97316' },
  { name: 'GCP Storage',     value: 28, color: '#3b82f6' },
  { name: 'Azure Blob',      value: 30, color: '#8b5cf6' },
]

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1e2235', border: '1px solid #2d3452',
      borderRadius: 8, padding: '8px 12px', fontSize: 12,
    }}>
      <p style={{ color: payload[0].payload.color }}>
        {payload[0].name}: <strong>{payload[0].value}%</strong>
      </p>
    </div>
  )
}

export default function StorageChart({ data = mockData }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={data} cx="50%" cy="50%"
          innerRadius={60} outerRadius={90}
          paddingAngle={3} dataKey="value"
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  )
}