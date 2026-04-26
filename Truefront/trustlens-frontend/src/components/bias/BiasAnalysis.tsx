import React from 'react'
import { BiasMetric } from '../../types/bias'

interface BiasAnalysisProps {
  metrics: BiasMetric[]
}

export const BiasAnalysis: React.FC<BiasAnalysisProps> = ({ metrics }) => {
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low':
        return 'bg-green-100 text-green-700'
      case 'medium':
        return 'bg-yellow-100 text-yellow-700'
      case 'high':
        return 'bg-red-100 text-red-700'
      default:
        return 'bg-gray-100 text-gray-700'
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Bias Analysis</h2>
      {metrics.length === 0 ? (
        <p className="text-gray-500">No bias metrics available</p>
      ) : (
        <div className="space-y-4">
          {metrics.map((metric, index) => (
            <div key={index} className="p-4 bg-gray-50 rounded-md">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-medium text-gray-900">{metric.category}</h4>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(metric.severity)}`}>
                  {metric.severity}
                </span>
              </div>
              <p className="text-sm text-gray-600 mb-2">{metric.indicator}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Value: {metric.value.toFixed(2)}</span>
                <span className="text-gray-500">Threshold: {metric.threshold.toFixed(2)}</span>
              </div>
              <p className="text-xs text-gray-400 mt-2">{metric.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
