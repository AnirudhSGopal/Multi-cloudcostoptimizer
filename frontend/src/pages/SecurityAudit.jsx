import { useState, useRef } from 'react'
import { ShieldCheck, ShieldAlert, ShieldX, Lock, Upload, GitBranch, X, Loader2 } from 'lucide-react'
import AlertBanner from '../components/security/AlertBanner'
import ComplianceTable from '../components/security/ComplianceTable'
import SecurityGauge from '../components/charts/SecurityGauge'
import useCloudStore from '../store/cloudStore'
import { apiClient } from '../services/api'

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
  const type = a.severity === 'critical' ? 'critical' : a.severity === 'warning' ? 'warning' : 'info'
  
  let fixSteps = []
  if (type === 'critical') {
    fixSteps = [
      `Locate the affected resource or file: ${a.location ?? 'Unknown'}.`,
      'Identify and extract any hardcoded credentials, API keys, or JWT secrets.',
      'Configure the service to inject these values via environment variables.',
      'Rotate any exposed credentials immediately on the provider control panel.'
    ]
  } else if (type === 'warning') {
    fixSteps = [
      `Review access rules and permissions for: ${a.location ?? 'Unknown'}.`,
      'Enforce least-privilege configurations and restrict open access controls.',
      'Enable server-side validation and secure configurations.',
      'Run verification scripts to ensure that resources are not publicly queryable.'
    ]
  } else {
    fixSteps = [
      'Assess development guidelines and enforce secure header best practices.',
      'Implement missing security libraries or middleware.',
      'Set up continuous security testing in the CI/CD pipeline.'
    ]
  }

  return {
    id:       a.id,
    type,
    title:    a.message,
    impact:   a.message,
    resource: a.location ?? 'Unknown',
    owner:    'Security Team',
    time:     'just now',
    fixSteps,
  }
}

// ─── map Claude compliance rows → ComplianceTable shape ──────────────────────

function toComplianceRow(r) {
  const status = r.status === 'pass' ? 'Pass' : 'Fail'
  const score  = r.status === 'pass' ? '>85%' : r.severity === 'high' ? '<70%' : '70–85%'
  return { framework: r.check, status, score, findings: r.detail }
}

// ─── component ────────────────────────────────────────────────────────────────

export default function SecurityAudit() {
  const { 
    alerts: storeAlerts, 
    dismissedAlerts, 
    dismissAlert,
    scanOverall,
    scanCompliance,
    scanTime,
    repoUrl: storeRepoUrl,
    hasScanned,
    scanning,
    progress,
    scanError,
    setRepoUrl,
    startBackgroundScan,
    setError
  } = useCloudStore()

  const [repoUrlInput, setRepoUrlInput] = useState(storeRepoUrl || '')
  const [files, setFiles]               = useState([])
  const fileRef = useRef()

  const rawAlerts    = storeAlerts
  const activeAlerts = rawAlerts.filter(a => !dismissedAlerts.includes(a.id))

  const activeOverall = scanOverall !== null
    ? { ...scanOverall, ...resolveOverallMeta(scanOverall.status) }
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
    const url = repoUrlInput.trim()
    if (!url && files.length === 0) {
      setError('Add a repo URL or upload at least one file.')
      return
    }
    setError('')
    setRepoUrl(url)

    const filesWithContent = []
    for (const f of files) {
      try {
        const text = await f.text()
        filesWithContent.push({ name: f.name, content: text.slice(0, 3000) })
      } catch (_) {}
    }

    startBackgroundScan(url, filesWithContent)
  }

  const OverallIcon = activeOverall.icon

  return (
    <div className="page-content">

      {/* ── Scan input ── */}
      <div className="card">
        <div className="section-header" style={{ marginBottom: 10 }}>
          <span className="card__title" style={{ margin: 0 }}>Security scan</span>
          {scanTime && (
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Last scanned {new Date(scanTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
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
              value={repoUrlInput}
              onChange={e => setRepoUrlInput(e.target.value)}
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
            {files.length > 0 ? `${files.length} file${files.length > 1 ? 's' : ''}` : 'Select Folder'}
          </button>
          <input
            ref={fileRef}
            type="file"
            webkitdirectory="true"
            directory="true"
            multiple
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
            {scanning ? <Loader2 size={13} className="spin" /> : <ShieldCheck size={13} />}
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

        {scanError && <p style={{ fontSize: 11, color: 'var(--red)', marginTop: 6 }}>{scanError}</p>}
      </div>

      {/* ── Active alerts ── */}
      {activeAlerts.length > 0 && (
        <div>
          <div className="section-header">
            <span className="section-title">
              {hasScanned ? 'Scan Findings' : 'Active alerts'} ({activeAlerts.length})
            </span>
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
              <span style={{ fontSize: 15, fontWeight: 600, color: activeOverall.color }}>
                {activeOverall.status}
              </span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Overall security posture based on the latest AI scan.
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
        <ComplianceTable scanData={scanCompliance} />
      </div>

    </div>
  )
}