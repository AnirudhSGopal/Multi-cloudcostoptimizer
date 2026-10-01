export default function ComplianceTable({ scanData }) {
  const dataToRender = scanData || []

  if (dataToRender.length === 0) {
    return (
      <p role="status" style={{ color: 'var(--text-muted)', padding: '16px 0' }}>
        Compliance results will appear after a security scan.
      </p>
    )
  }

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
          {dataToRender.map(row => (
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