import React, { useState } from 'react'

interface DecisionPanelProps {
  applicationId: string
  candidateName: string
  onSubmitDecision: (applicationId: string, decision: 'accept' | 'reject', notes?: string) => void
}

export const DecisionPanel: React.FC<DecisionPanelProps> = ({
  applicationId,
  candidateName,
  onSubmitDecision,
}) => {
  const [notes, setNotes] = useState('')

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Decision for {candidateName}</h2>
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Add notes about this decision..."
        rows={3}
        className="w-full px-3 py-2 border border-gray-300 rounded-md mb-4"
      />
      <div className="flex space-x-2">
        <button
          onClick={() => onSubmitDecision(applicationId, 'accept', notes)}
          className="flex-1 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          Accept
        </button>
        <button
          onClick={() => onSubmitDecision(applicationId, 'reject', notes)}
          className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
        >
          Reject
        </button>
      </div>
    </div>
  )
}
