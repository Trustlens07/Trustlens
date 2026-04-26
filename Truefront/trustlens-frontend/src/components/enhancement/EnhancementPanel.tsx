import { useState } from 'react'
import { useEnhanceScore } from '../../hooks/useScores'
import { ScoreResponse } from '../../types/score'
import { Sparkles, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'

interface EnhancementPanelProps {
  candidateId: string
  originalScore: ScoreResponse | undefined
  onEnhanced: (enhancedScore: ScoreResponse) => void
}

export function EnhancementPanel({ candidateId, originalScore, onEnhanced }: EnhancementPanelProps) {
  const [isEnhancing, setIsEnhancing] = useState(false)
  const enhanceScore = useEnhanceScore()

  const handleEnhance = async () => {
    setIsEnhancing(true)
    try {
      const result = await enhanceScore.mutateAsync(candidateId)
      onEnhanced(result)
      toast.success('Score enhanced with AI analysis')
    } catch (error) {
      toast.error('Failed to enhance score')
    } finally {
      setIsEnhancing(false)
    }
  }

  return (
    <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-200 p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-5 w-5 text-purple-600" />
            <h3 className="text-lg font-semibold text-gray-900">AI Enhancement</h3>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Enhance the candidate's score using Gemini AI for deeper analysis and bias mitigation.
          </p>
          
          {originalScore?.explanation && (
            <div className="bg-white rounded-lg p-4 border border-gray-200 mb-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Original Analysis</h4>
              <p className="text-sm text-gray-600">{originalScore.explanation}</p>
            </div>
          )}
        </div>

        <button
          onClick={handleEnhance}
          disabled={isEnhancing}
          className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isEnhancing ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Enhancing...
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              Enhance Score
            </>
          )}
        </button>
      </div>
    </div>
  )
}
