export default function SecurityGauge({ score = 74, label = 'Security Score', compact = false }) {
  const color = score >= 80 ? '#2ecc8e' : score >= 60 ? '#f5a623' : '#ff5b5b'
  const size = compact ? 100 : 140
  const r = compact ? 36 : 52
  const cx = size / 2
  const cy = size / 2
  const circumference = 2 * Math.PI * r
  const progress = (score / 100) * circumference

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: compact ? 4 : 6 }}>
      <div style={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={cx} cy={cy} r={r} fill="none"
            stroke="#1c2236" strokeWidth={compact ? 6 : 8} />
          <circle cx={cx} cy={cy} r={r} fill="none"
            stroke={color} strokeWidth={compact ? 6 : 8}
            strokeDasharray={`${progress} ${circumference}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.6s ease' }} />
        </svg>
        <div style={{
          position: 'absolute', inset: 0,
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <span style={{ fontSize: compact ? 18 : 26, fontWeight: 700, color, lineHeight: 1 }}>{score}</span>
          {!compact && <span style={{ fontSize: 10, color: '#3a4560', marginTop: 3 }}>{label}</span>}
        </div>
      </div>
    </div>
  )
}