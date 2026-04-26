import React from 'react'
import { DisparityIndicator as DisparityIndicatorType } from '../../types/bias'
import { formatPercentage } from '../../utils/formatting'

interface DisparityIndicatorProps {
  indicators: DisparityIndicatorType[]
}

export const DisparityIndicator: React.FC<DisparityIndicatorProps> = ({ indicators }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'text-green-600'
      case 'medium':
        return 'text-yellow-600'
      case 'high':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Disparity Indicators</h2>
      {indicators.length === 0 ? (
        <p className="text-gray-500">No disparity data available</p>
      ) : (
        <div className="space-y-3">
          {indicators.map((indicator, index) => (
            <div key={index} className="p-3 bg-gray-50 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-gray-900">{indicator.group}</span>
                <span className={`text-sm font-medium ${getSeverityColor(indicator.severity)}`}>
                  {indicator.severity}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-sm">
                <div>
                  <span className="text-gray-500">Score:</span>
                  <span className="ml-1 text-gray-900">{indicator.score.toFixed(1)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Benchmark:</span>
                  <span className="ml-1 text-gray-900">{indicator.benchmark.toFixed(1)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Disparity:</span>
                  <span className={`ml-1 ${getSeverityColor(indicator.severity)}`}>
                    {formatPercentage(indicator.disparity)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
