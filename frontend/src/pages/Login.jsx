import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import useAuthStore from '../store/authStore'
import { Sun, Moon } from 'lucide-react'

const styles = `
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@400;500;600;700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root,
  [data-theme="dark"] {
    --bg: #0d0f14;
    --surface: #13161e;
    --surface2: #1a1e2a;
    --border: #252a38;
    --border2: #2e3547;
    --accent: #4f8ef7;
    --accent-dim: rgba(79,142,247,0.12);
    --accent-glow: rgba(79,142,247,0.25);
    --green: #22c55e;
    --green-dim: rgba(34,197,94,0.12);
    --red: #ef4444;
    --red-dim: rgba(239,68,68,0.1);
    --text: #e2e8f0;
    --text-muted: #64748b;
    --text-dim: #94a3b8;
    --radius: 10px;
    --font-head: 'Syne', sans-serif;
    --font-mono: 'Space Mono', monospace;
    --left-panel-bg: linear-gradient(160deg, #13161e 0%, #0f1219 100%);
  }

  [data-theme="light"] {
    --bg: #f0f2f8;
    --surface: #ffffff;
    --surface2: #f7f8fc;
    --border: #e2e5f0;
    --border2: #d0d4e8;
    --accent: #3d7fff;
    --accent-dim: rgba(61,127,255,0.10);
    --accent-glow: rgba(61,127,255,0.20);
    --green: #18a065;
    --green-dim: rgba(24,160,101,0.10);
    --red: #e03535;
    --red-dim: rgba(224,53,53,0.10);
    --text: #0f1320;
    --text-muted: #8892b0;
    --text-dim: #4a5578;
    --radius: 10px;
    --font-head: 'Syne', sans-serif;
    --font-mono: 'Space Mono', monospace;
    --left-panel-bg: linear-gradient(160deg, #f3f5f8 0%, #e2e6ee 100%);
  }

  .auth-root {
    min-height: 100vh;
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-head);
    overflow: hidden;
    position: relative;
  }

  .bg-layer {
    position: fixed; inset: 0; z-index: 0;
    background:
      radial-gradient(ellipse 60% 50% at 15% 20%, rgba(79,142,247,0.06) 0%, transparent 70%),
      radial-gradient(ellipse 50% 60% at 85% 75%, rgba(34,197,94,0.04) 0%, transparent 60%),
      radial-gradient(ellipse 40% 40% at 50% 50%, rgba(79,142,247,0.03) 0%, transparent 80%);
  }

  .grid-overlay {
    position: fixed; inset: 0; z-index: 0;
    background-image:
      linear-gradient(rgba(79,142,247,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(79,142,247,0.03) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 30%, transparent 100%);
  }

  .layout {
    position: relative; z-index: 1;
    display: flex; height: 100vh;
  }

  /* LEFT PANEL */
  .left-panel {
    width: 420px; flex-shrink: 0;
    display: flex; flex-direction: column;
    padding: 40px;
    border-right: 1px solid var(--border2);
    background: var(--left-panel-bg);
    position: relative; overflow: hidden;
  }

  .left-panel::before {
    content: '';
    position: absolute; top: -80px; left: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(79,142,247,0.08) 0%, transparent 70%);
    pointer-events: none;
  }

  .logo-row { display: flex; align-items: center; gap: 10px; }

  .logo-icon {
    width: 38px; height: 38px; border-radius: 9px;
    background: linear-gradient(135deg, #4f8ef7 0%, #2563eb 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px;
    box-shadow: 0 0 0 1px rgba(79,142,247,0.3), 0 4px 16px rgba(79,142,247,0.2);
  }

  .logo-text { font-family: var(--font-head); font-weight: 800; font-size: 18px; color: var(--text); }
  .logo-sub  { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); margin-top: 1px; }

  .left-content { margin-top: auto; margin-bottom: auto; }

  .tagline { font-size: 28px; font-weight: 800; line-height: 1.25; color: var(--text); margin-bottom: 16px; }
  .tagline span { color: var(--accent); }

  .left-desc {
    font-family: var(--font-mono);
    font-size: 12px; line-height: 1.7;
    color: var(--text-muted);
    margin-bottom: 32px;
  }

  .stat-pills { display: flex; flex-direction: column; gap: 10px; }

  .stat-pill {
    display: flex; align-items: center; gap: 12px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px 16px;
    transition: border-color 0.2s;
  }
  .stat-pill:hover { border-color: var(--border2); }

  .pill-icon {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0;
  }
  .pill-icon.blue  { background: var(--accent-dim); }
  .pill-icon.green { background: var(--green-dim); }
  .pill-icon.red   { background: var(--red-dim); }

  .pill-label { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); }
  .pill-value { font-weight: 700; font-size: 14px; color: var(--text); margin-top: 1px; }

  .ai-badge {
    margin-top: 28px;
    display: flex; align-items: center; gap: 8px;
    font-family: var(--font-mono); font-size: 11px; color: var(--green);
  }

  .ai-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 0 2px var(--green-dim);
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 2px var(--green-dim); }
    50%       { opacity: 0.7; box-shadow: 0 0 0 5px transparent; }
  }

  /* RIGHT PANEL */
  .right-panel {
    flex: 1;
    display: flex; align-items: center; justify-content: center;
    padding: 40px;
  }

  .auth-card { width: 100%; max-width: 400px; }

  /* TOGGLE */
  .toggle-bar {
    display: flex;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 4px;
    margin-bottom: 32px;
  }

  .toggle-btn {
    flex: 1; padding: 9px;
    font-family: var(--font-head); font-size: 14px; font-weight: 600;
    border: none; background: transparent;
    border-radius: 7px; cursor: pointer;
    color: var(--text-muted);
    transition: all 0.2s ease;
  }

  .toggle-btn.active {
    background: var(--surface2);
    color: var(--text);
    box-shadow: 0 1px 4px rgba(0,0,0,0.4);
    border: 1px solid var(--border2);
  }

  /* FORM PANEL */
  .form-panel {
    animation: fadeIn 0.25s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .form-heading { font-size: 22px; font-weight: 800; color: var(--text); margin-bottom: 6px; }

  .form-sub {
    font-family: var(--font-mono);
    font-size: 11px; color: var(--text-muted);
    margin-bottom: 26px; line-height: 1.6;
  }

  /* FIELDS */
  .field      { margin-bottom: 16px; }
  .field-row  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; }

  .field label, .field-row label {
    display: block;
    font-family: var(--font-mono);
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--text-muted); margin-bottom: 7px;
  }

  .input-wrap { position: relative; }

  .input-wrap .icon {
    position: absolute; left: 13px; top: 50%; transform: translateY(-50%);
    color: var(--text-muted); font-size: 14px; pointer-events: none;
  }

  .field input, .field-row input {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 11px 13px 11px 38px;
    font-family: var(--font-mono); font-size: 12px;
    color: var(--text); outline: none;
    transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
  }

  .field input::placeholder, .field-row input::placeholder { color: var(--text-muted); }

  .field input:focus, .field-row input:focus {
    border-color: var(--accent);
    background: var(--surface2);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }

  /* PROVIDER PILLS */
  .provider-field       { margin-bottom: 16px; }
  .provider-field label {
    display: block;
    font-family: var(--font-mono); font-size: 10px; font-weight: 700;
    letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--text-muted); margin-bottom: 7px;
  }
  .provider-pills { display: flex; gap: 8px; }

  .provider-pill {
    flex: 1; padding: 9px 6px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-family: var(--font-mono); font-size: 11px;
    color: var(--text-muted);
    cursor: pointer; text-align: center;
    transition: all 0.15s;
    user-select: none;
  }
  .provider-pill.selected {
    border-color: var(--accent);
    background: var(--accent-dim);
    color: var(--accent);
  }

  /* FORGOT */
  .forgot-row { display: flex; justify-content: flex-end; margin-top: -8px; margin-bottom: 20px; }
  .forgot-link {
    font-family: var(--font-mono); font-size: 10px;
    color: var(--accent); text-decoration: none;
    opacity: 0.8; transition: opacity 0.2s; background: none; border: none; cursor: pointer;
  }
  .forgot-link:hover { opacity: 1; }

  /* SUBMIT */
  .submit-btn {
    width: 100%; padding: 13px;
    background: var(--accent);
    border: none; border-radius: 8px;
    font-family: var(--font-head); font-size: 14px; font-weight: 700;
    color: #fff; cursor: pointer;
    transition: opacity 0.2s, transform 0.1s, box-shadow 0.2s;
    box-shadow: 0 4px 16px rgba(79,142,247,0.3);
    margin-top: 4px;
  }
  .submit-btn:hover { opacity: 0.92; box-shadow: 0 6px 24px rgba(79,142,247,0.4); }
  .submit-btn:active { transform: scale(0.99); }

  /* DIVIDER */
  /* TERMS */
  .terms {
    margin-top: 18px;
    font-family: var(--font-mono); font-size: 10px;
    color: var(--text-muted); text-align: center; line-height: 1.6;
  }
  .terms a { color: var(--accent); text-decoration: none; opacity: 0.8; }
  .terms a:hover { opacity: 1; }

  /* BOTTOM BAR */
  .ai-bar {
    position: fixed; bottom: 0; left: 0; right: 0;
    border-top: 1px solid var(--border);
    background: var(--surface);
    padding: 10px 40px;
    display: flex; align-items: center; justify-content: space-between;
    z-index: 10;
  }
  .ai-bar-left {
    display: flex; align-items: center; gap: 8px;
    font-family: var(--font-mono); font-size: 11px; color: var(--green);
  }
  .ai-bar-right { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); }

  /* ALERT BANNER */
  .alert-banner {
    background: rgba(79,142,247,0.06);
    border: 1px solid rgba(79,142,247,0.15);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 22px;
    display: flex; align-items: center; gap: 10px;
    font-family: var(--font-mono); font-size: 11px; color: var(--text-dim);
    line-height: 1.5;
  }
  .alert-bolt { color: var(--accent); font-size: 14px; flex-shrink: 0; }
`;

const LoginForm = () => {
  const navigate = useNavigate()
  const { login, isLoading, error } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email || !password) {
      toast.error('Please fill in all fields')
      return
    }
    const result = await login(email, password)
    if (result.success) {
      toast.success('Login successful!')
      navigate('/dashboard')
    } else {
      toast.error(result.error)
    }
  }

  return (
    <div className="form-panel">
      <div className="form-heading">Welcome back</div>
      <p className="form-sub">Sign in to view insights for your connected cloud accounts.</p>

      {error && (
        <div className="alert-banner" style={{ background: 'rgba(239,68,68,0.06)', borderColor: 'rgba(239,68,68,0.15)' }}>
          <span className="alert-bolt" style={{ color: 'var(--red)' }}>⚠</span>
          <span style={{ color: 'var(--red)' }}>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Work Email</label>
          <div className="input-wrap">
            <span className="icon">✉</span>
            <input
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>

        <div className="field">
          <label>Password</label>
          <div className="input-wrap">
            <span className="icon">🔒</span>
            <input
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>

        <div className="forgot-row">
          <button type="button" className="forgot-link">Forgot password?</button>
        </div>

        <button type="submit" className="submit-btn" disabled={isLoading}>
          {isLoading ? 'Signing in...' : 'Sign In to CloudOpt →'}
        </button>
      </form>

    </div>
  )
};

const SignupForm = () => {
  const navigate = useNavigate()
  const { signup, isLoading, error } = useAuthStore()
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [provider, setProvider] = useState('AWS')
  const providers = ['AWS', 'GCP', 'Azure', 'Multi']

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!firstName || !lastName || !email || !password) {
      toast.error('Please fill in all fields')
      return
    }
    if (password.length < 12) {
      toast.error('Password must be at least 12 characters')
      return
    }
    const result = await signup(firstName, lastName, email, password, 'viewer')
    if (result.success) {
      toast.success('Account created successfully!')
      navigate('/dashboard')
    } else {
      toast.error(result.error)
    }
  }

  return (
    <div className="form-panel">
      <div className="form-heading">Get started free</div>
      <p className="form-sub">Connect your cloud providers in under 2 minutes. No card required.</p>

      {error && (
        <div className="alert-banner" style={{ background: 'rgba(239,68,68,0.06)', borderColor: 'rgba(239,68,68,0.15)' }}>
          <span className="alert-bolt" style={{ color: 'var(--red)' }}>⚠</span>
          <span style={{ color: 'var(--red)' }}>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="field-row">
          <div>
            <label>First Name</label>
            <div className="input-wrap">
              <span className="icon">👤</span>
              <input
                type="text"
                placeholder="Alex"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label>Last Name</label>
            <div className="input-wrap">
              <span className="icon">👤</span>
              <input
                type="text"
                placeholder="Smith"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
              />
            </div>
          </div>
        </div>

        <div className="field">
          <label>Work Email</label>
          <div className="input-wrap">
            <span className="icon">✉</span>
            <input
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>

        <div className="field">
          <label>Password</label>
          <div className="input-wrap">
            <span className="icon">🔒</span>
            <input
              type="password"
              placeholder="Min. 12 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
        </div>

        <div className="provider-field">
          <label>Primary cloud provider</label>
          <div className="provider-pills">
            {providers.map((p) => (
              <div
                key={p}
                className={`provider-pill${provider === p ? ' selected' : ''}`}
                onClick={() => setProvider(p)}
              >
                {p}
              </div>
            ))}
          </div>
        </div>

        <button type="submit" className="submit-btn" disabled={isLoading}>
          {isLoading ? 'Creating Account...' : 'Create Account →'}
        </button>
      </form>

      <p className="terms">
        By creating an account you agree to our{' '}
        <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.
      </p>
    </div>
  );
};

export default function Login() {
  const [tab, setTab] = useState('login');
  const [theme, setTheme] = useState(
    () => localStorage.getItem('theme') || 'dark'
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () =>
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))

  return (
    <>
      <style>{styles}</style>

      <div className="auth-root">
        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          style={{
            position: 'absolute', top: 20, right: 20, zIndex: 100,
            width: 34, height: 34, borderRadius: 8,
            background: 'var(--surface)', border: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer', color: 'var(--text-dim)',
            transition: 'all 0.15s ease'
          }}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface2)'; e.currentTarget.style.color = 'var(--text)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface)'; e.currentTarget.style.color = 'var(--text-dim)' }}
          title="Toggle theme"
        >
          {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
        </button>
        <div className="bg-layer" />
        <div className="grid-overlay" />

        <div className="layout">
          {/* RIGHT PANEL */}
          <div className="right-panel">
            <div className="auth-card">
              {/* Centered Brand Logo */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 24 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 9,
                  background: 'linear-gradient(135deg, var(--accent) 0%, #2563eb 100%)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 16, color: '#fff',
                  boxShadow: '0 4px 12px var(--accent-glow)'
                }}>⚡</div>
                <div style={{ textAlign: 'left' }}>
                  <div style={{ fontFamily: 'var(--font-head)', fontWeight: 800, fontSize: 18, color: 'var(--text)' }}>CloudOpt</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: 9, color: 'var(--text-muted)' }}>AI Cost &amp; Security</div>
                </div>
              </div>

              {/* Toggle */}
              <div className="toggle-bar">
                <button
                  className={`toggle-btn${tab === 'login' ? ' active' : ''}`}
                  onClick={() => setTab('login')}
                >
                  Sign In
                </button>
                <button
                  className={`toggle-btn${tab === 'signup' ? ' active' : ''}`}
                  onClick={() => setTab('signup')}
                >
                  Create Account
                </button>
              </div>

              {tab === 'login' ? <LoginForm /> : <SignupForm />}
            </div>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="ai-bar">
          <div className="ai-bar-left">
            <div className="ai-dot" />
            CloudOpt
          </div>
          <div className="ai-bar-right">v1.0.0 · Cloud cost and security insights</div>
        </div>
      </div>
    </>
  );
}