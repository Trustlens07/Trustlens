import React from 'react'

interface ScreeningResult {
  application_id: string
  name: string
  score: number
  status: 'shortlisted' | 'rejected'
}

interface ScreeningResultsProps {
  results: ScreeningResult[]
  onDecision: (applicationId: string, decision: 'accept' | 'reject') => void
  onExport: (format: 'csv' | 'json') => void
}

export const ScreeningResults: React.FC<ScreeningResultsProps> = ({
  results,
  onDecision,
  onExport,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex justify-end space-x-2">
        <button
          onClick={() => onExport('csv')}
          className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
        >
          Export CSV
        </button>
        <button
          onClick={() => onExport('json')}
          className="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-md"
        >
          Export JSON
        </button>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Score</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            {results.map((result) => (
              <tr key={result.application_id} className="border-t border-gray-200">
                <td className="px-4 py-3 text-sm text-gray-900">{result.name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{result.score.toFixed(1)}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                      result.status === 'shortlisted'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {result.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onDecision(result.application_id, 'accept')}
                      className="px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => onDecision(result.application_id, 'reject')}
                      className="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded"
                    >
                      Reject
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
