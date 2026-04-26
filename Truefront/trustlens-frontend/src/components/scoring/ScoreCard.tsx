import React from 'react'
import { formatScore } from '../../utils/formatting'

interface ScoreCardProps {
  title: string
  score: number
  maxScore?: number
  subtitle?: string
}

export const ScoreCard: React.FC<ScoreCardProps> = ({
  title,
  score,
  maxScore = 100,
  subtitle,
}) => {
  const percentage = (score / maxScore) * 100
  const getColor = () => {
    if (percentage >= 80) return 'text-green-600'
    if (percentage >= 60) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
      <div className={`text-3xl font-bold ${getColor()}`}>
        {formatScore(score)}
        <span className="text-lg text-gray-400">/{maxScore}</span>
      </div>
      {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}
