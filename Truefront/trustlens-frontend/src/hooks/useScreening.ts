import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { screeningService } from '../services/screeningService'
import { queryKeys } from '../store/queryKeys'
import toast from 'react-hot-toast'

export function useScreenResumes() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: screeningService.screenResumes,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.screening.results(data.session_id) 
      })
      toast.success('Screening started successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to start screening')
    },
  })
}

export function useScreeningResults(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.screening.results(sessionId),
    queryFn: () => screeningService.getScreeningResults(sessionId),
    enabled: !!sessionId,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    refetchInterval: (query) => {
      // Poll if no results yet
      return query.state.data?.results?.length === 0 ? 3000 : false
    },
  })
}

export function useFairnessReport(sessionId: string) {
  return useQuery({
    queryKey: queryKeys.screening.report(sessionId),
    queryFn: () => screeningService.getFairnessReport(sessionId),
    enabled: !!sessionId,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}
