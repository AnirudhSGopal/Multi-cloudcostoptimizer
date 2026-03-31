import { useState } from 'react'
import { Eye, EyeOff, Save, CheckCircle, Wifi } from 'lucide-react'
import Button from '../components/common/Button'
import toast from 'react-hot-toast'

function CredentialField({ label, value, onChange, placeholder, type = 'password' }) {
  const [show, setShow] = useState(false)
  const isSecret = type === 'password'
  return (
    <div className="form-field">
      <label className="form-label">{label}</label>
      <div className="form-input-wrap">
        <input
          type={isSecret && !show ? 'password' : 'text'}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={placeholder}
          className="form-input"
        />
        {isSecret && (
          <button className="form-input-toggle" onClick={() => setShow(s => !s)}>
            {show ? <EyeOff size={13} /> : <Eye size={13} />}
          </button>
        )}
      </div>
    </div>
  )
}

function ProviderSection({ name, color, fields }) {
  const [values, setValues]   = useState(() => Object.fromEntries(fields.map(f => [f.key, ''])))
  const [saved, setSaved]     = useState(false)
  const [testing, setTesting] = useState(false)

  const handleSave = () => {
    toast.success(`${name} credentials saved`)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleTest = async () => {
    setTesting(true)
    await new Promise(r => setTimeout(r, 1200))
    setTesting(false)
    toast.success(`${name} connection verified`)
  }

  return (
    <div className="provider-settings-card">
      <div className="provider-settings-header">
        <div className="provider-settings-name">
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
          {name}
          {saved && <CheckCircle size={13} color="var(--green)" style={{ marginLeft: 4 }} />}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <Button onClick={handleTest} size="sm" variant="ghost" icon={Wifi}>
            {testing ? 'Testing…' : 'Test'}
          </Button>
          <Button onClick={handleSave} size="sm" icon={Save}>Save</Button>
        </div>
      </div>
      <div className="provider-settings-body">
        {fields.map(f => (
          <CredentialField
            key={f.key}
            label={f.label}
            placeholder={f.placeholder}
            type={f.type || 'password'}
            value={values[f.key]}
            onChange={val => setValues(prev => ({ ...prev, [f.key]: val }))}
          />
        ))}
      </div>
    </div>
  )
}

const PROVIDERS = [
  {
    name: 'Amazon Web Services', color: 'var(--aws)',
    fields: [
      { key: 'accessKey',    label: 'Access Key ID',     placeholder: 'AKIAIOSFODNN7EXAMPLE', type: 'text'     },
      { key: 'secretKey',    label: 'Secret Access Key', placeholder: 'wJalrXUtnFEMI/K7MDENG…'                 },
      { key: 'region',       label: 'Default Region',    placeholder: 'us-east-1', type: 'text'                },
    ],
  },
  {
    name: 'Google Cloud Platform', color: 'var(--gcp)',
    fields: [
      { key: 'projectId',    label: 'Project ID',                    placeholder: 'my-gcp-project-123', type: 'text' },
      { key: 'serviceKey',   label: 'Service Account Key (JSON)',    placeholder: 'Paste JSON key content…'          },
    ],
  },
  {
    name: 'Microsoft Azure', color: 'var(--azure)',
    fields: [
      { key: 'subId',        label: 'Subscription ID', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', type: 'text' },
      { key: 'tenantId',     label: 'Tenant ID',       placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', type: 'text' },
      { key: 'clientId',     label: 'Client ID',       placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', type: 'text' },
      { key: 'clientSecret', label: 'Client Secret',   placeholder: 'your-client-secret'                              },
    ],
  },
]

export default function Settings() {
  const [aiUrl, setAiUrl] = useState(import.meta.env.VITE_AI_SERVICE_URL || '')

  return (
    <div className="page-content">
      <div className="settings-layout">
        <div>
          <div className="settings-section-title">Cloud Provider Credentials</div>
          <div className="settings-providers">
            {PROVIDERS.map(p => <ProviderSection key={p.name} {...p} />)}
          </div>

          <div style={{ marginTop: 16 }}>
            <div className="settings-section-title">AI Service Configuration</div>
            <div className="provider-settings-card">
              <div className="provider-settings-header">
                <span className="provider-settings-name">AI Backend</span>
                <Button onClick={() => toast.success('AI URL saved')} size="sm" icon={Save}>Save</Button>
              </div>
              <div className="provider-settings-body">
                <div className="form-field">
                  <label className="form-label">Backend URL</label>
                  <input
                    value={aiUrl}
                    onChange={e => setAiUrl(e.target.value)}
                    placeholder="http://localhost:8001"
                    className="form-input"
                    style={{ paddingRight: 11 }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right info panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="info-card">
            <div className="info-card__title">Connection Status</div>
            {[
              { label: 'AWS',   status: 'Connected',     color: 'var(--green)'  },
              { label: 'GCP',   status: 'Connected',     color: 'var(--green)'  },
              { label: 'Azure', status: 'Connected',     color: 'var(--green)'  },
              { label: 'AI Engine', status: 'Active',   color: 'var(--blue)'   },
            ].map(({ label, status, color }) => (
              <div key={label} className="info-card__row">
                <span className="info-card__row-label">{label}</span>
                <span style={{ color, fontWeight: 600, fontSize: 11.5 }}>● {status}</span>
              </div>
            ))}
          </div>
          <div className="info-card">
            <div className="info-card__title">Security Tips</div>
            {[
              'Use IAM roles over access keys where possible',
              'Rotate credentials every 90 days',
              'Never commit credentials to version control',
              'Enable MFA on all cloud accounts',
            ].map((tip, i) => (
              <div key={i} className="info-card__row" style={{ alignItems: 'flex-start' }}>
                <span style={{ color: 'var(--accent)', fontWeight: 700, marginRight: 6, flexShrink: 0 }}>→</span>
                <span className="info-card__row-label" style={{ lineHeight: 1.5 }}>{tip}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}