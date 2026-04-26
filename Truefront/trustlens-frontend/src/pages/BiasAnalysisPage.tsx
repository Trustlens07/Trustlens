import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCandidates } from '../hooks/useCandidates'
import { useBiasAnalysis } from '../hooks/useBias'
import { useAuth } from '../hooks/useAuth'
import { BiasSeverity, DemographicBreakdown, DisparityIndicator } from '../types/bias'
import { Header } from '../components/common/Header'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

export default function BiasAnalysisPage() {
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  const { data: candidates, isLoading: candidatesLoading } = useCandidates({ limit: 100 })
  const biasAnalysis = useBiasAnalysis()
  const [analysisResult, setAnalysisResult] = useState<any>(null)

  if (authLoading) {
    return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner size="lg" /></div>
  }

  if (!user) {
    navigate('/login')
    return null
  }

  const handleRunAnalysis = async () => {
    if (!candidates?.candidates.length) return

    const candidateData = candidates.candidates
      .filter(c => c.status === 'completed')
      .map(c => ({
        candidate_id: c.id,
        score: 0, // Will be populated from scores
        attributes: { name: c.name, job_role: c.job_role, skills: c.skills },
      }))

    if (candidateData.length === 0) {
      return
    }

    const result = await biasAnalysis.mutateAsync({ candidates: candidateData })
    setAnalysisResult(result)
  }

  // Extract data from analysis result or use defaults
  const demographicBreakdown: DemographicBreakdown[] = analysisResult?.demographic_breakdown || []
  const disparityIndicators: DisparityIndicator[] = analysisResult?.disparity_indicators || []
  const overallFairnessScore = analysisResult?.overall_fairness_score || 0

  // Count bias alerts (medium + high severity)
  const biasAlertCount = disparityIndicators.filter(d => d.severity === 'medium' || d.severity === 'high').length
  const demographicGroupCount = demographicBreakdown.reduce(
    (acc, d) => acc + Object.keys(d.groups).length, 0
  )

  const getSeverityColor = (severity: BiasSeverity) => {
    switch (severity) {
      case 'low':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'high':
        return 'bg-red-100 text-red-800 border-red-200'
    }
  }

  const getSeverityDot = (severity: BiasSeverity) => {
    switch (severity) {
      case 'low':
        return 'bg-green-400'
      case 'medium':
        return 'bg-yellow-400'
      case 'high':
        return 'bg-red-400'
    }
  }

  const BAR_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Bias Analysis</h2>
            <p className="text-gray-600">
              Analyze demographic breakdown and identify potential bias indicators across your candidate pool.
            </p>
          </div>
          <button
            onClick={handleRunAnalysis}
            disabled={biasAnalysis.isPending || candidatesLoading}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {biasAnalysis.isPending ? 'Analyzing...' : 'Run Analysis'}
          </button>
        </div>

        {/* Overall Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Total Candidates</p>
            <p className="text-2xl font-bold text-gray-900">{candidates?.total || 0}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Demographic Groups</p>
            <p className="text-2xl font-bold text-blue-600">{demographicGroupCount || '-'}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Bias Alerts</p>
            <p className="text-2xl font-bold text-yellow-600">{biasAlertCount || '-'}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-600">Overall Fairness</p>
            <p className="text-2xl font-bold text-green-600">
              {overallFairnessScore ? overallFairnessScore.toFixed(1) : '-'}
            </p>
          </div>
        </div>

        {!analysisResult ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <p className="text-gray-500 mb-4">
              {candidates?.candidates.filter(c => c.status === 'completed').length === 0
                ? 'No completed candidates to analyze. Process candidates first.'
                : 'Click "Run Analysis" to analyze bias across your candidate pool.'}
            </p>
          </div>
        ) : (
          <>
            {/* Demographic Breakdown */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
              {demographicBreakdown.map((breakdown) => (
                <div key={breakdown.category} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    {breakdown.category} Distribution
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(breakdown.groups).map(([key, value]) => (
                      <div key={key} className="border-b border-gray-100 pb-3 last:border-0">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm font-medium text-gray-700">{key}</span>
                          <span className="text-sm text-gray-500">{value.count} candidates</span>
                        </div>
                        <div className="flex justify-between text-xs text-gray-600">
                          <span>Avg Score: {value.avg_score.toFixed(1)}</span>
                          <span>Selection: {(value.selection_rate * 100).toFixed(0)}%</span>
                        </div>
                        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${value.selection_rate * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Mini bar chart for this category */}
                  {Object.entries(breakdown.groups).length > 0 && (
                    <div className="mt-4">
                      <ResponsiveContainer width="100%" height={120}>
                        <BarChart data={Object.entries(breakdown.groups).map(([key, value]) => ({
                          name: key,
                          score: value.avg_score,
                        }))}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                          <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                          <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                          <Tooltip formatter={(value: number) => [value.toFixed(1), 'Avg Score']} />
                          <Bar dataKey="score" radius={[4, 4, 0, 0]} barSize={20}>
                            {Object.entries(breakdown.groups).map((_, index) => (
                              <Cell key={index} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Disparity Indicators */}
            {disparityIndicators.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Disparity Indicators</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Score differences between demographic groups. Higher values indicate greater disparity.
                </p>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Group</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Score Difference</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Disparity</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Severity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {disparityIndicators.map((indicator, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm font-medium text-gray-900">{indicator.group}</td>
                          <td className="py-3 px-4 text-sm text-gray-900 font-medium">
                            {indicator.score.toFixed(1)}
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {indicator.disparity.toFixed(2)}
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${getSeverityColor(
                                indicator.severity
                              )}`}
                            >
                              <span className={`h-2 w-2 rounded-full ${getSeverityDot(indicator.severity)}`} />
                              {indicator.severity}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Recommendations */}
            <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">Recommendations</h3>
              <ul className="space-y-2 text-sm text-blue-800">
                {biasAlertCount > 0 && (
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>Review screening criteria for potential bias - {biasAlertCount} alert(s) detected</span>
                  </li>
                )}
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Consider implementing blind screening to reduce demographic bias</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Use aggressive fairness mode in screening to mitigate identified disparities</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-600 mt-0.5">•</span>
                  <span>Regularly re-run bias analysis as new candidates are processed</span>
                </li>
              </ul>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
