import { BiasMetric, BiasSeverity } from '../../types/bias'
import { cn } from '../../utils/cn'

interface BiasMetricsCardProps {
  metrics: BiasMetric[]
  overallFairnessScore: number
}

export function BiasMetricsCard({ metrics, overallFairnessScore }: BiasMetricsCardProps) {
  const getSeverityColor = (severity: BiasSeverity) => {
    switch (severity) {
      case 'low':
        return 'chip-success'
      case 'medium':
        return 'chip-warning'
      case 'high':
        return 'chip-error'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-primary'
    if (score >= 60) return 'text-tertiary'
    return 'text-error'
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex items-center justify-between">
          <h3 className="text-heading-md text-on-surface">Bias Metrics</h3>
          <div className="flex items-center gap-md">
            <span className="text-body text-on-surface-variant">Overall Fairness Score:</span>
            <span className={cn('metric-value', getScoreColor(overallFairnessScore || 0))}>
              {overallFairnessScore ? overallFairnessScore.toFixed(1) : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-outline-variant">
              <th className="text-left py-md px-lg text-label text-on-surface-variant uppercase tracking-wide">Category</th>
              <th className="text-left py-md px-lg text-label text-on-surface-variant uppercase tracking-wide">Indicator</th>
              <th className="text-left py-md px-lg text-label text-on-surface-variant uppercase tracking-wide">Value</th>
              <th className="text-left py-md px-lg text-label text-on-surface-variant uppercase tracking-wide">Threshold</th>
              <th className="text-left py-md px-lg text-label text-on-surface-variant uppercase tracking-wide">Severity</th>
            </tr>
          </thead>
          <tbody>
            {metrics && metrics.length > 0 ? metrics.map((metric, index) => (
              <tr key={index} className="border-b border-outline-variant hover:bg-surface-container">
                <td className="py-md px-lg text-body text-on-surface font-medium">{metric.category || 'N/A'}</td>
                <td className="py-md px-lg text-body text-on-surface-variant">{metric.indicator || 'N/A'}</td>
                <td className="py-md px-lg text-body text-on-surface font-medium">
                  {metric.value !== undefined ? metric.value.toFixed(2) : 'N/A'}
                </td>
                <td className="py-md px-lg text-body text-on-surface-variant">
                  {metric.threshold !== undefined ? metric.threshold.toFixed(2) : 'N/A'}
                </td>
                <td className="py-md px-lg">
                  <span className={cn('chip', getSeverityColor(metric.severity || 'low'))}>
                    {metric.severity || 'low'}
                  </span>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={5} className="text-center py-xl text-on-surface-variant text-body">
                  No bias metrics available
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {metrics.length === 0 && (
        <div className="text-center py-xl text-on-surface-variant text-body">No bias metrics available</div>
      )}
    </div>
  )
}
