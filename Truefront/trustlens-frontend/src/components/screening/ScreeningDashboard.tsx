import React from 'react'

interface ScreeningDashboardProps {
  onStartScreening: () => void
  onViewResults: (sessionId: string) => void
  recentSessions: Array<{ id: string; jobRole: string; createdAt: string }>
}

export const ScreeningDashboard: React.FC<ScreeningDashboardProps> = ({
  onStartScreening,
  onViewResults,
  recentSessions,
}) => {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Start New Screening</h2>
        <button
          onClick={onStartScreening}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          New Screening Session
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Sessions</h2>
        {recentSessions.length === 0 ? (
          <p className="text-gray-500">No recent screening sessions</p>
        ) : (
          <ul className="space-y-2">
            {recentSessions.map((session) => (
              <li
                key={session.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
              >
                <div>
                  <p className="font-medium text-gray-900">{session.jobRole}</p>
                  <p className="text-sm text-gray-500">
                    {new Date(session.createdAt).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => onViewResults(session.id)}
                  className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-md"
                >
                  View Results
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
