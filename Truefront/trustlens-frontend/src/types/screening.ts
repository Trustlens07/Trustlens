export type FairnessMode = 'standard' | 'aggressive' | 'conservative'

export interface ScreeningRequest {
  job_role: string
  job_description: string
  fairness_mode: FairnessMode
  resumes: {
    candidate_id: string
    name: string
    email: string
    skills: string[]
  }[]
}

export interface ScreeningSession {
  session_id: string
  job_role: string
  job_description: string
  fairness_mode: FairnessMode
  status: 'processing' | 'completed' | 'error'
  created_at: string
  total_candidates: number
}

export interface ScreeningResult {
  candidate_id: string
  name: string
  email: string
  original_score: number
  enhanced_score: number
  fairness_adjusted_score: number
  recommended: boolean
  bias_flags: string[]
}

export interface ScreeningResultsResponse {
  session_id: string
  results: ScreeningResult[]
  summary: {
    total_candidates: number
    recommended_count: number
    average_original_score: number
    average_enhanced_score: number
    average_fairness_score: number
  }
}

export interface FairnessReport {
  session_id: string
  demographic_equity: {
    gender: Record<string, number>
    race: Record<string, number>
    age: Record<string, number>
  }
  bias_mitigation_impact: {
    before_adjustment: number
    after_adjustment: number
    improvement_percentage: number
  }
  recommendation_distribution: {
    recommended: number
    not_recommended: number
    needs_review: number
  }
  generated_at: string
}
