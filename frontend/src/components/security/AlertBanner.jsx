import { useState } from 'react'
import { AlertCircle, AlertTriangle, Info, X, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'

import toast from 'react-hot-toast'

const CONFIG = {
  critical: { Icon: AlertCircle,  cls: 'critical', label: 'CRITICAL' },
  warning:  { Icon: AlertTriangle,cls: 'warning',  label: 'WARNING'  },
  info:     { Icon: Info,         cls: 'info',      label: 'INFO'     },
}

export default function AlertBanner({ alert, onDismiss }) {
  const [expanded, setExpanded] = useState(false)
  const { type = 'info', title, impact, resource, owner, time, fixSteps = [] } = alert
  const { Icon, cls, label } = CONFIG[type] || CONFIG.info

  function handleFixNow() {
    toast.promise(
      new Promise(resolve => setTimeout(resolve, 1500)),
      {
        loading: 'Applying AI auto-remediation...',
        success: 'Vulnerability fixed successfully!',
        error: 'Failed to apply fix.',
      }
    ).then(() => {
      onDismiss?.(alert.id)
    })
  }

  function handleInvestigate() {
    toast(`Investigation workflow started for: ${title}`, { icon: '🔍' })
  }

  return (
    <div className={`alert-banner ${cls}`} style={{ flexDirection: 'column', gap: 0, padding: 0, overflow: 'hidden' }}>

      {/* Main row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, padding: '11px 14px' }}>
        <div className="alert-icon-wrap" style={{ marginTop: 1 }}>
          <Icon size={14} />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3, flexWrap: 'wrap' }}>
            <span style={{
              fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 4,
              background: type === 'critical' ? 'rgba(255,91,91,0.18)' : type === 'warning' ? 'rgba(245,166,35,0.18)' : 'rgba(61,127,255,0.18)',
              color: type === 'critical' ? 'var(--red)' : type === 'warning' ? 'var(--yellow)' : 'var(--accent)',
              border: `1px solid ${type === 'critical' ? 'rgba(255,91,91,0.3)' : type === 'warning' ? 'rgba(245,166,35,0.3)' : 'rgba(61,127,255,0.3)'}`,
              fontFamily: 'JetBrains Mono, monospace',
              letterSpacing: '0.5px',
            }}>{label}</span>
            <span className="alert-title" style={{ margin: 0 }}>{title}</span>
          </div>

          {impact && impact !== title && (
            <div className="alert-msg" style={{ marginBottom: 6 }}>{impact}</div>
          )}

          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 11 }}>
            <span style={{ color: 'var(--text-muted)' }}>
              Resource: <span style={{ color: 'var(--text-secondary)', fontFamily: 'JetBrains Mono, monospace', fontSize: 10.5 }}>{resource}</span>
            </span>
            <span style={{ color: 'var(--text-muted)' }}>
              Owner: <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>{owner}</span>
            </span>
            <span style={{ color: 'var(--text-muted)' }}>{time}</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
          {type === 'critical' && (
            <button onClick={handleFixNow} className="btn btn-sm" style={{
              background: 'var(--red)', color: '#fff', border: 'none', borderRadius: 6,
              fontSize: 11, fontWeight: 600, padding: '4px 10px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <ExternalLink size={11} /> Fix Now
            </button>
          )}
          {type === 'warning' && (
            <button onClick={handleInvestigate} className="btn btn-sm btn-ghost" style={{ fontSize: 11, padding: '4px 10px', cursor: 'pointer' }}>
              Investigate
            </button>
          )}
          <button
            onClick={() => setExpanded(e => !e)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 2 }}
            title="View fix steps"
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          <button
            onClick={() => onDismiss?.(alert.id)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', padding: 2 }}
            title="Dismiss"
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* Expanded fix steps */}
      {expanded && fixSteps.length > 0 && (
        <div style={{
          borderTop: `1px solid ${type === 'critical' ? 'var(--alert-critical-border)' : type === 'warning' ? 'var(--alert-warning-border)' : 'var(--alert-info-border)'}`,
          padding: '10px 14px 12px 38px',
          background: 'rgba(0,0,0,0.15)',
        }}>
          <div style={{ fontSize: 10.5, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.6px', marginBottom: 8 }}>
            Remediation steps
          </div>
          <ol style={{ paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 5 }}>
            {fixSteps.map((step, i) => (
              <li key={i} style={{ fontSize: 11.5, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}