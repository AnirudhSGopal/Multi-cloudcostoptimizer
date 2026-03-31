const rows = [
  { framework: 'CIS Benchmark', status: 'Fail', score: '71%', findings: '12 high, 4 medium' },
  { framework: 'SOC 2 Controls', status: 'Pass', score: '92%', findings: '1 medium' },
  { framework: 'ISO 27001',      status: 'Pass', score: '88%', findings: '3 low' },
  { framework: 'PCI DSS',        status: 'Fail', score: '76%', findings: '2 high, 5 medium' },
]

export default function ComplianceTable() {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="data-table">
        <thead>
          <tr>
            <th>Framework</th>
            <th>Status</th>
            <th>Compliance Score</th>
            <th>Findings</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(row => (
            <tr key={row.framework}>
              <td className="td-strong">{row.framework}</td>
              <td>
                <span className={`badge ${row.status === 'Pass' ? 'badge-pass' : 'badge-fail'}`}>
                  {row.status}
                </span>
              </td>
              <td className="td-mono">{row.score}</td>
              <td>{row.findings}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}