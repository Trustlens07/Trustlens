export type ScoreVersion = 'original' | 'enhanced'

export interface SkillScore {
  skill: string
  score: number
  relevance: number
}

export interface ScoreBreakdown {
  skills: SkillScore[]
  experience: number
  education: number
  projects: number
  soft_skills: number
  overall: number
}

export interface ScoreResponse {
  candidate_id: string
  version: ScoreVersion
  breakdown: ScoreBreakdown
  calculated_at: string
  explanation?: string
}

export interface CandidateStatusWithScore {
  candidate_id: string
  status: 'pending' | 'processing' | 'completed' | 'error'
  score?: number
  version?: ScoreVersion
  error_message?: string
}
