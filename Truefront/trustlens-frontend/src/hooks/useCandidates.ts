import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { candidateService } from '../services/candidateService'
import { queryKeys } from '../store/queryKeys'
import { FilterParams } from '../types/api'
import toast from 'react-hot-toast'

export function useCandidates(params: FilterParams = {}) {
  return useQuery({
    queryKey: queryKeys.candidates.list(params),
    queryFn: () => candidateService.getCandidates(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

export function useCandidate(id: string) {
  return useQuery({
    queryKey: queryKeys.candidates.detail(id),
    queryFn: () => candidateService.getCandidate(id),
    enabled: !!id,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

export function useCandidateStatus(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.candidates.status(id),
    queryFn: () => candidateService.getCandidateStatus(id),
    enabled: enabled && !!id,
    refetchInterval: (query) => {
      // Poll every 3 seconds if status is processing
      return query.state.data?.status === 'processing' ? 3000 : false
    },
  })
}

export function useUploadCandidate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: candidateService.uploadCandidate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.lists() })
      toast.success('Candidate uploaded successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to upload candidate')
    },
  })
}

export function useBatchUploadCandidates() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: candidateService.batchUploadCandidates,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.lists() })
      toast.success('Batch upload completed successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to batch upload candidates')
    },
  })
}

export function useProcessCandidate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: candidateService.processCandidate,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.candidates.status(data.candidate_id) 
      })
      toast.success('Candidate processing started')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to process candidate')
    },
  })
}

export function useDeleteCandidate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: candidateService.deleteCandidate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.candidates.lists() })
      toast.success('Candidate deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete candidate')
    },
  })
}
