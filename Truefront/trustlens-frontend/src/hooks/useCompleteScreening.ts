import { useMutation, useQuery } from '@tanstack/react-query'
import { candidateService } from '../services/candidateService'
import { screeningService } from '../services/screeningService'
import { biasService } from '../services/biasService'
import { queryKeys } from '../store/queryKeys'
import toast from 'react-hot-toast'

export function useCompleteScreeningWorkflow() {
  return useMutation({
    mutationFn: async (data: {
      candidates: any[]
      jobRole: string
      jobDescription: string
    }) => {
      try {
        console.log('[Workflow] Starting complete screening workflow')
        
        // Step 1: Screen candidates
        const session = await candidateService.screenCandidates(
          data.candidates,
          data.jobRole,
          data.jobDescription
        )

        console.log('[Workflow] Screening session created:', session.session_id)
        
        // Step 2: Get screening results
        const results = await screeningService.getScreeningResults(session.session_id)
        console.log('[Workflow] Got screening results:', results)
        
        // Step 3: Get fairness report
        const report = await screeningService.getFairnessReport(session.session_id)
        console.log('[Workflow] Got fairness report:', report)

        // Step 4: Get bias metrics for each candidate
        const biasMetrics = await Promise.all(
          data.candidates.map(async (candidate) => {
            try {
              const metrics = await biasService.getBiasMetrics(candidate.candidate_id, 'fairness_adjusted')
              return {
                candidate_id: candidate.candidate_id,
                metrics,
              }
            } catch (error) {
              console.error('[Workflow] Error getting bias metrics for', candidate.candidate_id, error)
              return {
                candidate_id: candidate.candidate_id,
                metrics: null,
              }
            }
          })
        )

        console.log('[Workflow] Got bias metrics')

        return {
          session,
          results,
          report,
          biasMetrics,
        }
      } catch (error) {
        console.error('[Workflow] Error in screening workflow:', error)
        throw error
      }
    },
    onSuccess: (data) => {
      toast.success('Screening completed successfully!')
      console.log('[Workflow] Complete workflow result:', data)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || error.message || 'Screening workflow failed'
      toast.error(message)
      console.error('[Workflow] Error:', error)
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

export function useCandidateBiasMetrics(candidateId: string) {
  return useQuery({
    queryKey: queryKeys.bias.metrics(candidateId, 'fairness_adjusted'),
    queryFn: () => biasService.getBiasMetrics(candidateId, 'fairness_adjusted'),
    enabled: !!candidateId,
    retry: 2,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}
