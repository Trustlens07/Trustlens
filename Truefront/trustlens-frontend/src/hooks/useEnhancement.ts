import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { candidateService } from '../services/candidateService'
import { showErrorToast, showSuccessToast } from '../utils/errorHandler'
import { queryKeys } from '../store/queryKeys'

export const useEnhanceCandidate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (candidateId: string) => candidateService.enhanceCandidate(candidateId),
    onSuccess: (_, candidateId) => {
      showSuccessToast('Candidate enhanced successfully')
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.detail(candidateId) })
      queryClient.invalidateQueries({ queryKey: queryKeys.scores.history(candidateId) })
    },
    onError: (error) => {
      showErrorToast(error)
    },
  })
}

export const useEnhancementStatus = (candidateId: string) => {
  return useQuery({
    queryKey: queryKeys.candidates.status(candidateId),
    queryFn: () => candidateService.getCandidateStatus(candidateId),
    enabled: !!candidateId,
    refetchInterval: (query) => {
      if (query.state.data?.status === 'processing') return 2000
      return false
    },
  })
}
