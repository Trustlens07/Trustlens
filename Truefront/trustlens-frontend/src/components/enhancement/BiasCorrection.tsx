import React from 'react'

interface BiasCorrectionProps {
  corrections: Array<{
    type: string
    description: string
    impact: string
  }>
}

export const BiasCorrection: React.FC<BiasCorrectionProps> = ({ corrections }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Bias Corrections Applied</h2>
      {corrections.length === 0 ? (
        <p className="text-gray-500">No bias corrections applied</p>
      ) : (
        <ul className="space-y-3">
          {corrections.map((correction, index) => (
            <li key={index} className="p-3 bg-blue-50 rounded-md">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900">{correction.type}</span>
                <span className="text-xs text-blue-600">{correction.impact}</span>
              </div>
              <p className="text-sm text-gray-600">{correction.description}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
