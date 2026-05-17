import { useState, useRef } from 'react'
import { ShieldCheck, ShieldAlert, ShieldX, Lock, Upload, GitBranch, X } from 'lucide-react'
import AlertBanner from '../components/security/AlertBanner'
import ComplianceTable from '../components/security/ComplianceTable'
import SecurityGauge from '../components/charts/SecurityGauge'
import useCloudStore from '../store/cloudStore'

// ─── default overall score (shown before any scan) ────────────────────────────

const DEFAULT_OVERALL = { score: 74, icon: Lock, color: 'var(--blue)', status: 'Moderate' }

// ─── map Claude overall score → icon + color ──────────────────────────────────

function resolveOverallMeta(status) {
  if (status === 'Good')     return { icon: ShieldCheck, color: 'var(--green)'  }
  if (status === 'Critical') return { icon: ShieldX,     color: 'var(--red)'    }
  return                            { icon: Lock,        color: 'var(--blue)'   }
}

// ─── map Claude alert shape → AlertBanner shape ───────────────────────────────

function toAlertShape(a) {
  return {
    id:       a.id,
    type:     a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warning' : 'info',
    title:    a.message,
    impact:   a.message,
    resource: a.location ?? 'Unknown',
    owner:    'Security Team',
    time:     'just now',
    fixSteps: [],
  }
}

// ─── map Claude compliance rows → ComplianceTable shape ──────────────────────

function toComplianceRow(r) {
  const status = r.status === 'pass' ? 'Pass' : 'Fail'
  const score  = r.status === 'pass' ? '>85%' : r.severity === 'high' ? '<70%' : '70–85%'
  return { framework: r.check, status, score, findings: r.detail }
}

// ─── Claude API ───────────────────────────────────────────────────────────────

async function runClaudeAnalysis({ repoUrl, fileContents }) {
  const context = [
    repoUrl      ? `Repository URL: ${repoUrl}` : '',
    fileContents ? `Uploaded file contents:\n${fileContents}` : '',
  ].filter(Boolean).join('\n\n')

  const prompt = `You are a security auditor. Analyze this application and identify real security vulnerabilities, misconfigurations, and compliance gaps.

${context}

Check for: hardcoded secrets/API keys, XSS, CSRF, insecure auth, missing input validation, exposed endpoints, missing security headers, open CORS, insecure storage, IAM misconfigurations, unencrypted data.

Return ONLY valid JSON — no markdown fences, no explanation:
{
  "overall": {"score": 0-100, "status": "Good|Moderate|Critical"},
  "alerts": [
    {"id":"a1","severity":"critical|warning|info","message":"Specific issue found","location":"filename or component"}
  ],
  "compliance": [
    {"check":"CIS Benchmark","status":"pass|fail","severity":"high|medium|low","detail":"Brief finding"},
    {"check":"SOC 2 Controls","status":"pass|fail","severity":"high|medium|low","detail":"Brief finding"},
    {"check":"ISO 27001","status":"pass|fail","severity":"high|medium|low","detail":"Brief finding"},
    {"check":"PCI DSS","status":"pass|fail","severity":"high|medium|low","detail":"Brief finding"}
  ]
}
Max 6 alerts. Be specific to the code/repo provided.`

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1000,
      messages: [{ role: 'user', content: prompt }],
    }),
  })

  const data = await res.json()
  const raw  = data.content.map(c => c.text || '').join('').replace(/```json|```/g, '').trim()
  return JSON.parse(raw)
}

// ─── component ────────────────────────────────────────────────────────────────

export default function SecurityAudit() {
  const { alerts: storeAlerts, dismissedAlerts, dismissAlert } = useCloudStore()

  const [repoUrl, setRepoUrl]       = useState('')
  const [files, setFiles]           = useState([])
  const [scanning, setScanning]     = useState(false)
  const [progress, setProgress]     = useState(0)
  const [scanTime, setScanTime]     = useState(null)
  const [overall, setOverall]       = useState(null)       // null = show default
  const [scanAlerts, setScanAlerts] = useState(null)       // null = show store alerts
  const [compliance, setCompliance] = useState(null)       // null = ComplianceTable defaults
  const [error, setError]           = useState('')
  const fileRef = useRef()

  const rawAlerts    = scanAlerts !== null ? scanAlerts.map(toAlertShape) : storeAlerts
  const activeAlerts = rawAlerts.filter(a => !dismissedAlerts.includes(a.id))

  const activeOverall = overall !== null
    ? { ...overall, ...resolveOverallMeta(overall.status) }
    : DEFAULT_OVERALL

  // ── file handling ──────────────────────────────────────────────────────────

  function addFiles(incoming) {
    const next = Array.from(incoming)
    setFiles(prev => {
      const names = new Set(prev.map(f => f.name))
      return [...prev, ...next.filter(f => !names.has(f.name))]
    })
  }

  // ── scan ──────────────────────────────────────────────────────────────────

  async function startScan() {
    const url = repoUrl.trim()
    if (!url && files.length === 0) {
      setError('Add a repo URL or upload at least one file.')
      return
    }
    setError('')
    setScanning(true)
    setProgress(20)

    let fileContents = ''
    for (const f of files) {
      try {
        const text = await f.text()
        fileContents += `\n\n--- FILE: ${f.name} ---\n${text.slice(0, 3000)}`
      } catch (_) {}
    }

    setProgress(50)

    try {
      const result = await runClaudeAnalysis({ repoUrl: url, fileContents })
      setProgress(90)
      setOverall(result.overall ?? null)
      setScanAlerts(result.alerts       ? result.alerts                          : [])
      setCompliance(result.compliance   ? result.compliance.map(toComplianceRow) : null)
      setScanTime(new Date())
    } catch (e) {
      setError('Scan failed — check console.')
      console.error(e)
    } finally {
      setScanning(false)
      setProgress(0)
    }
  }

  const OverallIcon = activeOverall.icon

  return (
    <div className="page-content">

      {/* ── Scan input ── */}
      <div className="card">
        <div className="section-header" style={{ marginBottom: 10 }}>
          <span className="card__title" style={{ margin: 0 }}>Security scan</span>
          {scanTime && (
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Last scanned just now</span>
          )}
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
          {/* repo url */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, flex: 1,
            border: '1px solid var(--border)', borderRadius: 8,
            padding: '0 10px', height: 36, background: 'var(--surface)',
          }}>
            <GitBranch size={14} color="var(--text-muted)" />
            <input
              type="text"
              value={repoUrl}
              onChange={e => setRepoUrl(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && startScan()}
              placeholder="https://github.com/owner/repo"
              style={{
                flex: 1, border: 'none', outline: 'none',
                background: 'transparent', fontSize: 13, color: 'var(--text)',
              }}
            />
          </div>

          {/* upload */}
          <button
            className="btn btn-sm btn-ghost"
            onClick={() => fileRef.current?.click()}
            style={{ display: 'flex', alignItems: 'center', gap: 5, height: 36, padding: '0 12px' }}
            title="Upload files"
          >
            <Upload size={13} />
            {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''}` : 'Upload'}
          </button>
          <input
            ref={fileRef}
            type="file"
            multiple
            accept=".js,.jsx,.ts,.tsx,.py,.go,.java,.env,.json,.yaml,.yml,.tf"
            style={{ display: 'none' }}
            onChange={e => addFiles(e.target.files)}
          />

          {/* scan */}
          <button
            className="btn btn-sm"
            onClick={startScan}
            disabled={scanning}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              height: 36, padding: '0 14px',
              opacity: scanning ? 0.6 : 1,
              cursor: scanning ? 'not-allowed' : 'pointer',
            }}
          >
            <ShieldCheck size={13} />
            {scanning ? 'Scanning…' : 'Scan'}
          </button>
        </div>

        {/* file tags */}
        {files.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 6 }}>
            {files.map(f => (
              <span key={f.name} style={{
                display: 'flex', alignItems: 'center', gap: 4,
                fontSize: 11, padding: '2px 8px',
                border: '1px solid var(--border)', borderRadius: 6,
                color: 'var(--text-muted)',
              }}>
                {f.name}
                <X size={10} style={{ cursor: 'pointer' }}
                  onClick={() => setFiles(prev => prev.filter(p => p.name !== f.name))} />
              </span>
            ))}
          </div>
        )}

        {/* progress */}
        {scanning && (
          <div style={{ height: 2, background: 'var(--border)', borderRadius: 99, overflow: 'hidden', marginTop: 4 }}>
            <div style={{
              height: '100%', width: `${progress}%`,
              background: 'var(--accent)', borderRadius: 99,
              transition: 'width 0.4s ease',
            }} />
          </div>
        )}

        {error && <p style={{ fontSize: 11, color: 'var(--red)', marginTop: 6 }}>{error}</p>}
      </div>

      {/* ── Active alerts ── */}
      {activeAlerts.length > 0 && (
        <div>
          <div className="section-header">
            <span className="section-title">Active alerts ({activeAlerts.length})</span>
          </div>
          <div className="alerts-stack">
            {activeAlerts.map(alert => (
              <AlertBanner key={alert.id} alert={alert} onDismiss={dismissAlert} />
            ))}
          </div>
        </div>
      )}

      {/* ── Overall security score — single card ── */}
      <div>
        <div className="section-header">
          <span className="section-title">Security score</span>
        </div>
        <div className="card" style={{ display: 'flex', alignItems: 'center', gap: 24, padding: '20px 24px' }}>
          <div className="score-card__gauge">
            <SecurityGauge score={activeOverall.score} label="" size={120} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <OverallIcon size={18} color={activeOverall.color} />
              <span style={{ fontSize: 22, fontWeight: 700, color: activeOverall.color }}>
                {activeOverall.score}
              </span>
              <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>/ 100</span>
            </div>
            <div style={{ fontSize: 15, fontWeight: 600, color: activeOverall.color, marginBottom: 4 }}>
              {activeOverall.status}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Overall security posture
            </div>
          </div>
        </div>
      </div>

      {/* ── Compliance ── */}
      <div className="card">
        <div className="section-header" style={{ marginBottom: 0 }}>
          <span className="card__title" style={{ margin: 0 }}>Compliance check results</span>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {scanTime ? 'Just scanned' : 'Last scanned 5 min ago'}
          </span>
        </div>
        <ComplianceTable scanData={compliance} />
      </div>

    </div>
  )
}