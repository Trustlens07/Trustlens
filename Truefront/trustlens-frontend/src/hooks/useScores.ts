import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scoringService } from '../services/scoringService'
import { queryKeys } from '../store/queryKeys'
import { ScoreVersion } from '../types/score'
import toast from 'react-hot-toast'

export function useScore(candidateId: string, version: ScoreVersion = 'original') {
  return useQuery({
    queryKey: queryKeys.scores.candidate(candidateId, version),
    queryFn: () => scoringService.getScore(candidateId, version),
    enabled: !!candidateId,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

export function useEnhanceScore() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (candidateId: string) => scoringService.enhanceScore(candidateId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.scores.candidate(data.candidate_id, 'enhanced') 
      })
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.candidates.status(data.candidate_id) 
      })
      toast.success('Score enhanced successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to enhance score')
    },
  })
}
