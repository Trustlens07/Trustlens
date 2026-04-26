import React from 'react'
import { useAuthStore } from '../store/authStore'

const SettingsPage: React.FC = () => {
  const { user } = useAuthStore()

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>
      <div className="space-y-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Account</h2>
          <div className="space-y-2">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Email:</span> {user?.email}
            </p>
            <p className="text-sm text-gray-600">
              <span className="font-medium">User ID:</span> {user?.uid}
            </p>
          </div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Preferences</h2>
          <p className="text-gray-500">Settings options coming soon</p>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage
