import React from 'react'
import { FairnessReport as FairnessReportType } from '../../types/screening'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts'

interface FairnessReportProps {
  report: FairnessReportType
}

const DEMOGRAPHIC_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
const PIE_COLORS = ['#10b981', '#ef4444', '#f59e0b']

export const FairnessReport: React.FC<FairnessReportProps> = ({ report }) => {
  // Demographic equity bar data
  const equityData = [
    ...Object.entries(report.demographic_equity.gender).map(([key, value]) => ({
      category: 'Gender',
      group: key,
      value,
    })),
    ...Object.entries(report.demographic_equity.race).map(([key, value]) => ({
      category: 'Race',
      group: key,
      value,
    })),
    ...Object.entries(report.demographic_equity.age).map(([key, value]) => ({
      category: 'Age',
      group: key,
      value,
    })),
  ]

  // Recommendation distribution pie data
  const pieData = [
    { name: 'Recommended', value: report.recommendation_distribution.recommended },
    { name: 'Not Recommended', value: report.recommendation_distribution.not_recommended },
    { name: 'Needs Review', value: report.recommendation_distribution.needs_review },
  ].filter(d => d.value > 0)

  return (
    <div className="space-y-6">
      {/* Bias Mitigation Impact */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Bias Mitigation Impact</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">Before</p>
            <p className="text-2xl font-bold text-gray-900">
              {report.bias_mitigation_impact.before_adjustment.toFixed(2)}
            </p>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-600 mb-1">After</p>
            <p className="text-2xl font-bold text-blue-600">
              {report.bias_mitigation_impact.after_adjustment.toFixed(2)}
            </p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-green-600 mb-1">Improvement</p>
            <p className="text-2xl font-bold text-green-600">
              +{report.bias_mitigation_impact.improvement_percentage.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Demographic Equity Chart */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Demographic Equity Scores</h3>
        <ResponsiveContainer width="100%" height={Math.max(200, equityData.length * 40)}>
          <BarChart data={equityData} layout="vertical" margin={{ left: 10, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 11 }} />
            <YAxis type="category" dataKey="group" width={100} tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
              formatter={(value: number) => [value.toFixed(3), 'Equity Score']}
              labelFormatter={(label: string, payload: any) => {
                if (payload?.[0]?.payload) {
                  return `${payload[0].payload.category} - ${label}`
                }
                return label
              }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={16}>
              {equityData.map((_, index) => (
                <Cell key={index} fill={DEMOGRAPHIC_COLORS[index % DEMOGRAPHIC_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Recommendation Distribution */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommendation Distribution</h3>
        <div className="flex items-center justify-center">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                labelLine={{ stroke: '#9ca3af' }}
              >
                {pieData.map((_, index) => (
                  <Cell key={index} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
