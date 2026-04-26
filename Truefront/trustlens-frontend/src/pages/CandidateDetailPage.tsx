import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useCandidate, useCandidateStatus, useProcessCandidate, useDeleteCandidate } from '../hooks/useCandidates'
import { useScore } from '../hooks/useScores'
import { useBiasMetrics } from '../hooks/useBias'
import { CandidateStatusBadge } from '../components/common/CandidateStatusBadge'
import { ScoreChart } from '../components/scoring/ScoreChart'
import { BiasMetricsCard } from '../components/bias/BiasMetricsCard'
import { EnhancementPanel } from '../components/enhancement/EnhancementPanel'
import { FeedbackForm } from '../components/feedback/FeedbackForm'
import { Skeleton } from '../components/common/Skeleton'
import { useAuth } from '../hooks/useAuth'
import { ScoreResponse } from '../types/score'

export default function CandidateDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  const [enhancedScore, setEnhancedScore] = useState<ScoreResponse | undefined>(undefined)
  
  const { data: candidate, isLoading: candidateLoading } = useCandidate(id || '')
  const { data: status } = useCandidateStatus(id || '')
  const { data: originalScore } = useScore(id || '', 'original')
  const { data: biasMetrics } = useBiasMetrics(id || '', 'original')
  const processCandidate = useProcessCandidate()
  const deleteCandidate = useDeleteCandidate()

  if (authLoading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  }

  if (!user) {
    navigate('/login')
    return null
  }

  if (!id) {
    navigate('/')
    return null
  }

  const handleProcess = async () => {
    await processCandidate.mutateAsync(id)
  }

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this candidate?')) {
      await deleteCandidate.mutateAsync(id)
      navigate('/')
    }
  }

  const handleEnhanced = (score: ScoreResponse) => {
    setEnhancedScore(score)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-2"
            >
              ← Back to Dashboard
            </button>
            <div className="flex items-center gap-2">
              {candidate?.status === 'pending' && (
                <button
                  onClick={handleProcess}
                  disabled={processCandidate.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
                >
                  {processCandidate.isPending ? 'Processing...' : 'Process Candidate'}
                </button>
              )}
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm font-medium"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {candidateLoading ? (
          <div className="space-y-6">
            <Skeleton className="h-32 w-full" />
            <Skeleton className="h-64 w-full" />
          </div>
        ) : !candidate ? (
          <div className="text-center py-12 text-gray-500">Candidate not found</div>
        ) : (
          <div className="space-y-6">
            {/* Candidate Info */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-start justify-between">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900 mb-2">{candidate.name}</h1>
                  <p className="text-gray-600 mb-4">{candidate.email}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                      {candidate.job_role}
                    </span>
                    <CandidateStatusBadge status={candidate.status} />
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {candidate.skills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
                {status?.score !== undefined && (
                  <div className="text-right">
                    <p className="text-sm text-gray-600 mb-1">Overall Score</p>
                    <p className="text-4xl font-bold text-blue-600">{status.score.toFixed(1)}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {status.version === 'enhanced' ? 'AI Enhanced' : 'Original'}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Enhancement Panel */}
            {candidate.status === 'completed' && !enhancedScore && (
              <EnhancementPanel
                candidateId={id}
                originalScore={originalScore}
                onEnhanced={handleEnhanced}
              />
            )}

            {/* Score Charts */}
            {originalScore && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Score Breakdown</h3>
                  <ScoreChart breakdown={originalScore.breakdown} type="bar" />
                </div>
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Skills Radar</h3>
                  <ScoreChart breakdown={originalScore.breakdown} type="radar" />
                </div>
              </div>
            )}

            {/* Comparison Chart */}
            {originalScore && enhancedScore && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Original vs Enhanced Comparison
                </h3>
                <ScoreChart
                  breakdown={originalScore.breakdown}
                  type="radar"
                  comparison={enhancedScore.breakdown}
                />
                {enhancedScore.explanation && (
                  <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h4 className="text-sm font-medium text-purple-900 mb-2">AI Analysis</h4>
                    <p className="text-sm text-purple-700">{enhancedScore.explanation}</p>
                  </div>
                )}
              </div>
            )}

            {/* Bias Metrics */}
            {biasMetrics && candidate.status === 'completed' && (
              <BiasMetricsCard
                metrics={biasMetrics.metrics}
                overallFairnessScore={biasMetrics.overall_fairness_score}
              />
            )}

            {/* Feedback Form */}
            {candidate.status === 'completed' && (
              <FeedbackForm candidateId={id} />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
