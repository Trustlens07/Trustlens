import React from 'react'
import { FeedbackResponse } from '../../types/feedback'
import { formatDate } from '../../utils/dates'

interface FeedbackDisplayProps {
  feedback: FeedbackResponse[]
}

export const FeedbackDisplay: React.FC<FeedbackDisplayProps> = ({ feedback }) => {
  if (feedback.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <p className="text-gray-500">No feedback available</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {feedback.map((item) => (
        <div key={item.id} className="bg-white border border-gray-200 rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">{formatDate(item.created_at)}</span>
              <span className="text-yellow-500">
                {'★'.repeat(item.rating)}
                {'☆'.repeat(5 - item.rating)}
              </span>
            </div>
          </div>
          {item.comment && (
            <p className="text-gray-700">{item.comment}</p>
          )}
        </div>
      ))}
    </div>
  )
}
