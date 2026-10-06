import { Outlet } from 'react-router-dom'
import Sidebar from '../components/Sidebar.jsx'
import ChurnAssistant from '../components/ChurnAssistant.jsx'
import './DashboardLayout.css'

export default function DashboardLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-shell__content">
        <Outlet />
      </main>
      <ChurnAssistant />
    </div>
  )
}
