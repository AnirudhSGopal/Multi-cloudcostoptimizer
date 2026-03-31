export default function Button({ children, onClick, size = 'md', icon: Icon, variant = 'primary', disabled = false, type = 'button' }) {
  const cls = ['btn', `btn-${variant}`, size === 'sm' ? 'btn-sm' : ''].filter(Boolean).join(' ')
  return (
    <button type={type} onClick={onClick} disabled={disabled} className={cls}
      style={{ opacity: disabled ? 0.55 : 1, cursor: disabled ? 'not-allowed' : 'pointer' }}>
      {Icon && <Icon size={size === 'sm' ? 13 : 15} />}
      {children}
    </button>
  )
}