import { useAuth } from '../context/AuthContext.jsx'
import './Topbar.css'

export default function Topbar({ title, subtitle }) {
  const { logout } = useAuth()

  return (
    <header className="topbar">
      <div>
        <h1 className="topbar__title">{title}</h1>
        {subtitle && <p className="topbar__subtitle">{subtitle}</p>}
      </div>
      <button className="topbar__logout" onClick={logout}>
        Sign out
      </button>
    </header>
  )
}
