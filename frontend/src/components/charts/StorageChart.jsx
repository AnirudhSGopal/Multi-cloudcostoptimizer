import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { STORAGE_CONFIG, TOTAL_STORAGE_STATUS } from '../../config/storageConfig'

const defaultStorageData = [
  {
    name: STORAGE_CONFIG.AWS.serviceName,
    provider: STORAGE_CONFIG.AWS.provider,
    value: STORAGE_CONFIG.AWS.sharePct,
    sizeGb: STORAGE_CONFIG.AWS.sizeGb,
    color: '#ff8c38',
    label: STORAGE_CONFIG.AWS.sizeLabel,
  },
  {
    name: STORAGE_CONFIG.GCP.serviceName,
    provider: STORAGE_CONFIG.GCP.provider,
    value: STORAGE_CONFIG.GCP.sharePct,
    sizeGb: STORAGE_CONFIG.GCP.sizeGb,
    color: '#34aaff',
    label: STORAGE_CONFIG.GCP.sizeLabel,
  },
  {
    name: STORAGE_CONFIG.Azure.serviceName,
    provider: STORAGE_CONFIG.Azure.provider,
    value: STORAGE_CONFIG.Azure.sharePct,
    sizeGb: STORAGE_CONFIG.Azure.sizeGb,
    color: '#9d72ff',
    label: STORAGE_CONFIG.Azure.sizeLabel,
  },
]

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  const item = payload[0].payload
  return (
    <div style={{
      background: 'rgba(13, 16, 26, 0.95)', border: '1px solid rgba(79, 142, 247, 0.3)',
      borderRadius: 8, padding: '8px 12px', fontSize: 12, boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
    }}>
      <div style={{ color: item.color, fontWeight: 700, marginBottom: 2 }}>
        {item.name}: <strong>{item.value}%</strong>
      </div>
      <div style={{ color: '#cbd5e1', fontSize: 11, fontFamily: 'monospace' }}>
        Storage: <strong>{item.label}</strong>
      </div>
      <div style={{ color: '#38bdf8', fontSize: 10, marginTop: 3 }}>
        📦 {TOTAL_STORAGE_STATUS}
      </div>
    </div>
  )
}

export default function StorageChart({ data = defaultStorageData }) {
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