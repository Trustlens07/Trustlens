import React from 'react'
import { formatScore } from '../../utils/formatting'

interface ScoreComparisonProps {
  originalScore: number
  enhancedScore: number
}

export const ScoreComparison: React.FC<ScoreComparisonProps> = ({
  originalScore,
  enhancedScore,
}) => {
  const difference = enhancedScore - originalScore
  const isImprovement = difference > 0

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-lg font-semibold mb-4">Score Comparison</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600 mb-1">Original Score</p>
          <p className="text-2xl font-bold text-gray-900">{formatScore(originalScore)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600 mb-1">Enhanced Score</p>
          <p className="text-2xl font-bold text-blue-600">{formatScore(enhancedScore)}</p>
        </div>
      </div>
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Difference:{' '}
          <span className={`font-medium ${isImprovement ? 'text-green-600' : 'text-red-600'}`}>
            {isImprovement ? '+' : ''}{formatScore(difference)}
          </span>
        </p>
      </div>
    </div>
  )
}
