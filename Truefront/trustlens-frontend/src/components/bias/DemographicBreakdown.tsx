import React from 'react'
import { DemographicBreakdown as DemographicBreakdownType } from '../../types/bias'

interface DemographicBreakdownProps {
  breakdown: DemographicBreakdownType
}

export const DemographicBreakdown: React.FC<DemographicBreakdownProps> = ({ breakdown }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">{breakdown.category} Breakdown</h2>
      <div className="space-y-3">
        {Object.entries(breakdown.groups).map(([group, data]) => (
          <div key={group} className="p-3 bg-gray-50 rounded-md">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-gray-900">{group}</span>
              <span className="text-sm text-gray-500">{data.count} candidates</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-500">Avg Score:</span>
                <span className="ml-1 text-gray-900">{data.avg_score.toFixed(1)}</span>
              </div>
              <div>
                <span className="text-gray-500">Selection Rate:</span>
                <span className="ml-1 text-gray-900">{(data.selection_rate * 100).toFixed(1)}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
