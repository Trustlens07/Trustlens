import React from 'react'
import { formatDate } from '../../utils/dates'
import { formatScore } from '../../utils/formatting'

interface ScoreHistoryEntry {
  version: string
  score: number
  createdAt: string
}

interface ScoreHistoryProps {
  history: ScoreHistoryEntry[]
}

export const ScoreHistory: React.FC<ScoreHistoryProps> = ({ history }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Score History</h3>
      {history.length === 0 ? (
        <p className="text-gray-500">No score history available</p>
      ) : (
        <ul className="space-y-3">
          {history.map((entry, index) => (
            <li
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
            >
              <div>
                <p className="font-medium text-gray-900">{entry.version}</p>
                <p className="text-xs text-gray-500">{formatDate(entry.createdAt)}</p>
              </div>
              <span className="text-lg font-semibold text-gray-900">
                {formatScore(entry.score)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
