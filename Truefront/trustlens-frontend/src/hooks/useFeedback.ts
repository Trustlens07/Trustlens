import { useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../services/api'
import { queryKeys } from '../store/queryKeys'
import { FeedbackRequest } from '../types/feedback'
import toast from 'react-hot-toast'

export function useSubmitFeedback() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: FeedbackRequest) => 
      apiClient.post('/feedback', data).then(res => res.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.feedback.candidate(variables.candidate_id) 
      })
      toast.success('Feedback submitted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to submit feedback')
    },
  })
}
