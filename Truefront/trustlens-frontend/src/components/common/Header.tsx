import React from 'react'
import { useAuthStore } from '../../store/authStore'
import { useNavigate } from 'react-router-dom'

export const Header: React.FC = () => {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="bg-surface-container-lowest border-b border-outline-variant px-gutter py-md">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-lg">
          <h1 className="text-heading-lg text-on-surface">TrustLens</h1>
          <span className="text-body text-on-surface-variant">Fairness AI Recruitment Platform</span>
        </div>
        <div className="flex items-center space-x-lg">
          {user && (
            <>
              <span className="text-body text-on-surface-variant">{user.email}</span>
              <button
                onClick={handleLogout}
                className="btn-outline"
              >
                Logout
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  )
}
