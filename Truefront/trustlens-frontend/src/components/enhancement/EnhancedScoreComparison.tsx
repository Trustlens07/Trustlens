import React from 'react'
import { formatScore } from '../../utils/formatting'

interface EnhancedScoreComparisonProps {
  originalScore: number
  enhancedScore: number
  explanation: string
}

export const EnhancedScoreComparison: React.FC<EnhancedScoreComparisonProps> = ({
  originalScore,
  enhancedScore,
  explanation,
}) => {
  const difference = enhancedScore - originalScore
  const isImprovement = difference > 0

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">AI Enhancement Results</h2>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-4 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-600 mb-1">Original Score</p>
          <p className="text-2xl font-bold text-gray-900">{formatScore(originalScore)}</p>
        </div>
        <div className="p-4 bg-blue-50 rounded-md">
          <p className="text-sm text-gray-600 mb-1">Enhanced Score</p>
          <p className="text-2xl font-bold text-blue-600">{formatScore(enhancedScore)}</p>
        </div>
      </div>
      <div className="p-4 bg-green-50 rounded-md mb-4">
        <p className="text-sm text-gray-600">
          Score Change:{' '}
          <span className={`font-bold ${isImprovement ? 'text-green-600' : 'text-red-600'}`}>
            {isImprovement ? '+' : ''}{formatScore(difference)}
          </span>
        </p>
      </div>
      <div className="p-4 bg-yellow-50 rounded-md">
        <h3 className="text-sm font-medium text-gray-700 mb-2">AI Explanation</h3>
        <p className="text-sm text-gray-600">{explanation}</p>
      </div>
    </div>
  )
}
