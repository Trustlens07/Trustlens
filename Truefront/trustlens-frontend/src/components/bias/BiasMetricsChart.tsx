import { BiasMetric, BiasSeverity } from '../../types/bias'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts'

interface BiasMetricsChartProps {
  metrics: BiasMetric[]
}

const severityColors: Record<BiasSeverity, string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#ef4444',
}

export function BiasMetricsChart({ metrics }: BiasMetricsChartProps) {
  const chartData = metrics.map((metric) => ({
    name: metric.indicator.length > 25
      ? metric.indicator.slice(0, 25) + '...'
      : metric.indicator,
    fullName: metric.indicator,
    value: metric.value,
    threshold: metric.threshold,
    severity: metric.severity,
    category: metric.category,
  }))

  if (metrics.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Bias Metrics Chart</h2>
        <p className="text-gray-500">No data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <ResponsiveContainer width="100%" height={Math.max(200, metrics.length * 45)}>
        <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" domain={[0, 'auto']} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={160} tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            formatter={(value: number, name: string) => [
              value.toFixed(3),
              name === 'value' ? 'Metric Value' : 'Threshold',
            ]}
            labelFormatter={(_label: string, payload: any) => {
              if (payload?.[0]?.payload) {
                const d = payload[0].payload
                return `${d.category} - ${d.fullName}`
              }
              return ''
            }}
          />
          <ReferenceLine x={0} stroke="#9ca3af" />
          <Bar dataKey="value" name="value" radius={[0, 4, 4, 0]} barSize={16}>
            {chartData.map((entry, index) => (
              <Cell key={index} fill={severityColors[entry.severity]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex items-center gap-4 justify-center text-xs">
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-green-500" />
          <span className="text-gray-600">Low</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-yellow-500" />
          <span className="text-gray-600">Medium</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 rounded bg-red-500" />
          <span className="text-gray-600">High</span>
        </div>
      </div>
    </div>
  )
}
