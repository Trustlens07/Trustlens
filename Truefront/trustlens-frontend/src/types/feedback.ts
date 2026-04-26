export interface FeedbackRequest {
  candidate_id: string
  rating: number
  comment: string
}

export interface FeedbackResponse {
  id: string
  candidate_id: string
  rating: number
  comment: string
  created_at: string
}

export interface CandidateFeedback {
  feedbacks: FeedbackResponse[]
  average_rating: number
  total_feedbacks: number
}
