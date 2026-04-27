// Mock Backend Service - for development/testing without real backend
import {
  ScreeningRequest,
  ScreeningSession,
  ScreeningResultsResponse,
  FairnessReport,
  ScreeningResult,
} from '../types/screening'

// Store sessions in memory for this session
const sessions = new Map<string, any>()

const generateSessionId = () => `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

const mockScreeningResults = (request: ScreeningRequest): ScreeningResult[] => {
  return request.resumes.map((candidate, index) => ({
    candidate_id: candidate.candidate_id,
    name: candidate.name,
    email: candidate.email,
    original_score: Math.random() * 100,
    enhanced_score: Math.random() * 100,
    fairness_adjusted_score: Math.random() * 100,
    recommended: Math.random() > 0.3,
    bias_flags: Math.random() > 0.7 ? ['potential-bias-detected'] : [],
  }))
}

export const mockBackendService = {
  screenResumes: async (data: ScreeningRequest): Promise<ScreeningSession> => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 1500))

    const sessionId = generateSessionId()
    const session: ScreeningSession = {
      session_id: sessionId,
      job_role: data.job_role,
      job_description: data.job_description,
      fairness_mode: data.fairness_mode,
      status: 'completed',
      created_at: new Date().toISOString(),
      total_candidates: data.resumes.length,
    }

    // Store results for later retrieval
    const results = mockScreeningResults(data)
    sessions.set(sessionId, { session, results })

    return session
  },

  getScreeningResults: async (sessionId: string): Promise<ScreeningResultsResponse> => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 500))

    const sessionData = sessions.get(sessionId)
    if (!sessionData) {
      throw new Error(`Session ${sessionId} not found`)
    }

    const { session, results } = sessionData
    const summary = {
      total_candidates: results.length,
      recommended_count: results.filter((r: ScreeningResult) => r.recommended).length,
      average_original_score: results.reduce((sum: number, r: ScreeningResult) => sum + r.original_score, 0) / results.length,
      average_enhanced_score: results.reduce((sum: number, r: ScreeningResult) => sum + r.enhanced_score, 0) / results.length,
      average_fairness_score: results.reduce((sum: number, r: ScreeningResult) => sum + r.fairness_adjusted_score, 0) / results.length,
    }

    return {
      session_id: sessionId,
      results,
      summary,
    }
  },

  getFairnessReport: async (sessionId: string): Promise<FairnessReport> => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800))

    const sessionData = sessions.get(sessionId)
    if (!sessionData) {
      throw new Error(`Session ${sessionId} not found`)
    }

    const { results } = sessionData

    return {
      session_id: sessionId,
      demographic_equity: {
        gender: {
          male: 45,
          female: 48,
          non_binary: 52,
        },
        race: {
          caucasian: 44,
          african_american: 52,
          hispanic: 50,
          asian: 49,
        },
        age: {
          '18-30': 48,
          '31-40': 51,
          '41-50': 49,
          '50+': 48,
        },
      },
      bias_mitigation_impact: {
        before_adjustment: 12.5,
        after_adjustment: 3.2,
        improvement_percentage: 74.4,
      },
      recommendation_distribution: {
        recommended: results.filter((r: ScreeningResult) => r.recommended).length,
        not_recommended: results.filter((r: ScreeningResult) => !r.recommended).length,
        needs_review: 0,
      },
      generated_at: new Date().toISOString(),
    }
  },
}
