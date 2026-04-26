import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { biasService } from '../services/biasService'
import { DisparityIndicator } from '../types/bias'
import { ScoreVersion } from '../types/score'
import { showErrorToast, showSuccessToast } from '../utils/errorHandler'
import { queryKeys } from '../store/queryKeys'

export const useBiasMetrics = (candidateId: string, version: ScoreVersion = 'original') => {
  return useQuery({
    queryKey: queryKeys.bias.metrics(candidateId, version),
    queryFn: () => biasService.getBiasMetrics(candidateId, version),
    enabled: !!candidateId,
    staleTime: 5 * 60 * 1000,
  })
}

export const useAnalyzeBias = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: { candidates: Array<{ candidate_id: string; score: number; attributes: Record<string, any> }> }) => {
      const response = await biasService.analyzeBias(data)
      return response.data
    },
    onSuccess: () => {
      showSuccessToast('Bias analysis completed')
      queryClient.invalidateQueries({ queryKey: queryKeys.bias.all })
    },
    onError: (error) => {
      showErrorToast(error)
    },
  })
}

export const useDisparityIndicators = (candidateId: string, version: ScoreVersion = 'original') => {
  const { data: metrics } = useBiasMetrics(candidateId, version)

  const indicators: DisparityIndicator[] = []

  if (metrics?.demographic_breakdown) {
    const breakdown = metrics.demographic_breakdown

    Object.entries(breakdown).forEach(([category, groups]) => {
      const groupEntries = Object.entries(groups)
      if (groupEntries.length < 2) return

      const scores = groupEntries.map(([, data]) => (data as any).avg_score || 0)
      const maxScore = Math.max(...scores)

      groupEntries.forEach(([group, data]) => {
        const score = (data as any).avg_score || 0
        const benchmark = maxScore
        const disparity = benchmark > 0 ? (benchmark - score) / benchmark : 0
        const severity = disparity > 0.3 ? 'high' : disparity > 0.15 ? 'medium' : 'low'

        indicators.push({
          group: `${category}: ${group}`,
          score,
          benchmark,
          disparity,
          severity,
        })
      })
    })
  }

  return { indicators, isLoading: !metrics }
}
