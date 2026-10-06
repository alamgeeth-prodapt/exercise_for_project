import { NavLink } from 'react-router-dom'
import SignalBars from './SignalBars.jsx'
import './Sidebar.css'

const links = [
  { to: '/', label: 'Dashboard', icon: '◧' },
  { to: '/customers', label: 'Customers', icon: '☰' },
  { to: '/custom-prediction', label: 'Custom Prediction', icon: '✎' },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar__mark">
        <SignalBars variant="meter" strength={4} label="Signal" />
        <span>Prodapt</span>
      </div>
      <nav className="sidebar__nav">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === '/'}
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          >
            <span className="sidebar__icon">{link.icon}</span>
            {link.label}
          </NavLink>
        ))}
      </nav>
      <p className="sidebar__foot">Telecom churn analytics</p>
    </aside>
  )
}
