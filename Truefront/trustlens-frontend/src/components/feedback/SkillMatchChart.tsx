import React from 'react'

interface SkillMatch {
  skill: string
  match: number
}

interface SkillMatchChartProps {
  skills: SkillMatch[]
}

export const SkillMatchChart: React.FC<SkillMatchChartProps> = ({ skills }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">Skill Match Analysis</h2>
      {skills.length === 0 ? (
        <p className="text-gray-500">No skill data available</p>
      ) : (
        <div className="space-y-4">
          {skills.map((item, index) => (
            <div key={index}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-700">{item.skill}</span>
                <span className="text-sm text-gray-600">{(item.match * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${
                    item.match >= 0.8 ? 'bg-green-500' : item.match >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${item.match * 100}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
