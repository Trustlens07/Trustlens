import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { useUIStore } from '../../store/uiStore'

export const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { sidebarOpen } = useUIStore()

  const menuItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/upload', label: 'Upload' },
    { path: '/candidates', label: 'Candidates' },
    { path: '/bias-analysis', label: 'Bias Analysis' },
    { path: '/reports', label: 'Reports' },
  ]

  if (!sidebarOpen) return null

  return (
    <aside className="sidebar min-h-screen">
      <nav className="p-lg">
        <ul className="space-y-xs">
          {menuItems.map((item) => (
            <li key={item.path}>
              <button
                onClick={() => navigate(item.path)}
                className={`w-full text-left px-md py-sm rounded text-body transition-colors ${
                  location.pathname === item.path
                    ? 'bg-primary-container text-on-primary-container font-medium'
                    : 'text-on-surface hover:bg-surface-container'
                }`}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
