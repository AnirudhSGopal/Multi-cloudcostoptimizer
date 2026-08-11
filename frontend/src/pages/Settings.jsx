import { useState, useEffect } from 'react'
import { Eye, EyeOff, Save, CheckCircle, Wifi, Trash2, ShieldAlert } from 'lucide-react'
import Button from '../components/common/Button'
import useCloudStore from '../store/cloudStore'
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
          <button type="button" className="form-input-toggle" onClick={() => setShow(s => !s)}>
            {show ? <EyeOff size={13} /> : <Eye size={13} />}
          </button>
        )}
      </div>
    </div>
  )
}

function ProviderSection({ providerKey, name, color, fields }) {
  const { accounts, testConnection, addCloudAccount, deleteCloudAccount } = useCloudStore()
  const existingAccount = accounts.find(a => a.provider === providerKey)

  const [values, setValues] = useState(() => Object.fromEntries(fields.map(f => [f.key, ''])))
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleSave = async () => {
    // Basic validation
    const missing = fields.filter(f => f.required !== false && !values[f.key]?.trim())
    if (missing.length > 0) {
      toast.error(`Please fill in: ${missing.map(m => m.label).join(', ')}`)
      return
    }

    setSaving(true)
    const result = await addCloudAccount(providerKey, `${name} Account`, values)
    setSaving(false)

    if (result.success) {
      toast.success(`${name} account saved and connected!`)
    } else {
      toast.error(result.error || `Failed to connect ${name}`)
    }
  }

  const handleTest = async () => {
    const missing = fields.filter(f => f.required !== false && !values[f.key]?.trim())
    if (missing.length > 0) {
      toast.error(`Please fill in credentials first: ${missing.map(m => m.label).join(', ')}`)
      return
    }

    setTesting(true)
    const result = await testConnection(providerKey, values)
    setTesting(false)

    if (result.success) {
      toast.success(`${name} connection verified successfully!`)
    } else {
      toast.error(result.error || `${name} test failed`)
    }
  }

  const handleDelete = async () => {
    if (!existingAccount) return
    if (!window.confirm(`Are you sure you want to disconnect ${name}?`)) return

    setDeleting(true)
    const result = await deleteCloudAccount(existingAccount.id)
    setDeleting(false)

    if (result.success) {
      toast.success(`${name} account disconnected.`)
      setValues(Object.fromEntries(fields.map(f => [f.key, ''])))
    } else {
      toast.error(result.error || `Failed to remove ${name} account`)
    }
  }

  return (
    <div className="provider-settings-card">
      <div className="provider-settings-header">
        <div className="provider-settings-name">
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block' }} />
          {name}
          {existingAccount && (
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              fontSize: 11, padding: '2px 8px', borderRadius: 99,
              background: existingAccount.status === 'connected' ? 'var(--green-dim)' : 'var(--red-dim)',
              color: existingAccount.status === 'connected' ? 'var(--green)' : 'var(--red)',
              marginLeft: 8, fontWeight: 600,
            }}>
              <CheckCircle size={11} /> {existingAccount.status === 'connected' ? 'Connected' : 'Error'}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <Button onClick={handleTest} size="sm" variant="ghost" icon={Wifi} disabled={testing || saving}>
            {testing ? 'Testing…' : 'Test'}
          </Button>
          <Button onClick={handleSave} size="sm" icon={Save} disabled={saving || testing}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
          {existingAccount && (
            <Button onClick={handleDelete} size="sm" variant="ghost" icon={Trash2} disabled={deleting} style={{ color: 'var(--red)' }}>
              {deleting ? 'Removing…' : 'Disconnect'}
            </Button>
          )}
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
    providerKey: 'aws',
    name: 'Amazon Web Services',
    color: 'var(--aws)',
    fields: [
      { key: 'access_key_id',     label: 'Access Key ID',     placeholder: 'AKIAIOSFODNN7EXAMPLE', type: 'text'     },
      { key: 'secret_access_key', label: 'Secret Access Key', placeholder: 'wJalrXUtnFEMI/K7MDENG…'                 },
      { key: 'region',            label: 'Default Region',    placeholder: 'us-east-1', type: 'text', required: false },
    ],
  },
  {
    providerKey: 'gcp',
    name: 'Google Cloud Platform',
    color: 'var(--gcp)',
    fields: [
      { key: 'project_id',           label: 'Project ID',                 placeholder: 'my-gcp-project-123', type: 'text' },
      { key: 'service_account_json', label: 'Service Account Key (JSON)', placeholder: 'Paste JSON key content…'          },
      { key: 'bigquery_dataset',     label: 'Billing Export Dataset',     placeholder: 'billing_export (Optional)', type: 'text', required: false },
    ],
  },
  {
    providerKey: 'azure',
    name: 'Microsoft Azure',
    color: 'var(--azure)',
    fields: [
      { key: 'subscription_id', label: 'Subscription ID', placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', type: 'text' },
      { key: 'tenant_id',       label: 'Tenant ID',       placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', type: 'text' },
      { key: 'client_id',       label: 'Client ID',       placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', type: 'text' },
      { key: 'client_secret',   label: 'Client Secret',   placeholder: 'your-client-secret'                              },
    ],
  },
]

export default function Settings() {
  const { fetchAccounts, accounts, syncAllAccounts } = useCloudStore()
  const [aiUrl, setAiUrl] = useState(import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:5000')

  useEffect(() => {
    fetchAccounts()
  }, [fetchAccounts])

  const getStatus = (pKey) => {
    const acc = accounts.find(a => a.provider === pKey)
    if (!acc) return { status: 'Not Connected', color: 'var(--text-muted)' }
    if (acc.status === 'connected') return { status: 'Connected', color: 'var(--green)' }
    return { status: 'Error', color: 'var(--red)' }
  }

  return (
    <div className="page-content">
      <div className="settings-layout">
        <div>
          <div className="settings-section-title">Cloud Provider Credentials</div>
          <div className="settings-providers">
            {PROVIDERS.map(p => <ProviderSection key={p.providerKey} {...p} />)}
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
                    placeholder="http://localhost:5000"
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
              { key: 'aws', label: 'AWS' },
              { key: 'gcp', label: 'GCP' },
              { key: 'azure', label: 'Azure' },
            ].map(({ key, label }) => {
              const { status, color } = getStatus(key)
              return (
                <div key={key} className="info-card__row">
                  <span className="info-card__row-label">{label}</span>
                  <span style={{ color, fontWeight: 600, fontSize: 11.5 }}>● {status}</span>
                </div>
              )
            })}
            <div className="info-card__row">
              <span className="info-card__row-label">AI Engine</span>
              <span style={{ color: 'var(--blue)', fontWeight: 600, fontSize: 11.5 }}>● Active</span>
            </div>

            {accounts.length > 0 && (
              <Button
                onClick={() => {
                  toast.promise(syncAllAccounts(), {
                    loading: 'Syncing live cost data...',
                    success: 'Live data synced!',
                    error: 'Sync error',
                  })
                }}
                size="sm"
                variant="ghost"
                style={{ marginTop: 8, width: '100%' }}
              >
                Sync Live Data Now
              </Button>
            )}
          </div>

          <div className="info-card">
            <div className="info-card__title">Security & Encryption</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 8 }}>
              All stored credentials are encrypted at rest using AES-128-CBC + HMAC-SHA256 (Fernet). Credentials are never exposed over API responses.
            </div>
            {[
              'Use IAM roles with minimal permissions',
              'GCP requires BigQuery Billing Export enabled',
              'Azure requires Cost Management Reader role',
              'Never commit keys to version control',
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