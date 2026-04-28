import apiClient from './api'
import { ScoreResponse, ScoreVersion } from '../types/score'

export const scoringService = {
  getScore: async (candidateId: string, version: ScoreVersion = 'original'): Promise<ScoreResponse> => {
    try {
      console.log(`[Scoring] Getting score for candidate ${candidateId}`)

      try {
        const response = await apiClient.get<any>(`/scores/candidate/${candidateId}`, {
          params: { version },
        })
        console.log(`[Scoring] Real score response:`, response.data)

        // Unwrap {success, data} wrapper
        const d = response.data?.data || response.data

        const result: ScoreResponse = {
          candidate_id: d.candidate_id ?? candidateId,
          version: (d.version as ScoreVersion) ?? version,
          breakdown: {
            skills: d.breakdown?.skills
              ? Object.entries(d.breakdown.skills).map(([skill, score]) => ({
                  skill,
                  score: Number(score),
                  relevance: 1,
                }))
              : [{ skill: 'Overall', score: d.skill_score ?? 0, relevance: 1 }],
            experience: d.experience_score ?? d.breakdown?.experience ?? 0,
            education: d.education_score ?? d.breakdown?.education ?? 0,
            projects: d.breakdown?.projects ?? 0,
            soft_skills: d.breakdown?.soft_skills ?? 0,
            overall: d.overall_score ?? 0,
          },
          explanation: d.explanation ?? d.bias_correction_applied ?? '',
          calculated_at: d.enhanced_at ?? d.created_at ?? new Date().toISOString(),
          ranking_percentile: d.ranking_percentile,
        }

        console.log(`[Scoring] Mapped score result:`, result)
        return result
      } catch (apiError) {
        console.debug(`[Scoring] Real API not available, using mock data`)

        const mockScore: ScoreResponse = {
          candidate_id: candidateId,
          version: version,
          breakdown: {
            skills: [
              { skill: 'JavaScript', score: 88, relevance: 0.9 },
              { skill: 'React', score: 90, relevance: 0.95 },
              { skill: 'TypeScript', score: 85, relevance: 0.85 },
              { skill: 'Node.js', score: 82, relevance: 0.8 },
              { skill: 'Python', score: 78, relevance: 0.75 },
              { skill: 'AWS', score: 75, relevance: 0.7 },
            ],
            experience: 80,
            education: 85,
            projects: 88,
            soft_skills: 82,
            overall: 84.5,
          },
          explanation: 'Candidate shows strong technical skills with good experience and education background.',
          calculated_at: new Date().toISOString(),
        }

        console.log(`[Scoring] Mock ${version} score:`, mockScore)
        return mockScore
      }
    } catch (error) {
      console.error(`[Scoring] Get score error for candidate ${candidateId}:`, error)
      throw error
    }
  },

  enhanceScore: async (candidateId: string, candidateData?: any): Promise<ScoreResponse> => {
    try {
      console.log(`[Scoring] Enhancing score for candidate ${candidateId}`)

      try {
        const response = await apiClient.post<any>(`/candidates/${candidateId}/enhance`)
        console.log(`[Scoring] Real enhancement response:`, response.data)

        const d = response.data?.data || response.data

        return {
          candidate_id: d.candidate_id ?? candidateId,
          version: 'enhanced',
          breakdown: {
            skills: d.breakdown?.skills
              ? Object.entries(d.breakdown.skills).map(([skill, score]) => ({
                  skill,
                  score: Number(score),
                  relevance: 1,
                }))
              : [{ skill: 'Overall', score: d.skill_score ?? 0, relevance: 1 }],
            experience: d.experience_score ?? d.breakdown?.experience ?? 0,
            education: d.education_score ?? d.breakdown?.education ?? 0,
            projects: d.breakdown?.projects ?? 0,
            soft_skills: d.breakdown?.soft_skills ?? 0,
            overall: d.overall_score ?? 0,
          },
          explanation: d.explanation ?? d.bias_correction_applied ?? '',
          calculated_at: d.enhanced_at ?? d.created_at ?? new Date().toISOString(),
          ranking_percentile: d.ranking_percentile,
        }
      } catch (apiError) {
        console.debug(`[Scoring] Real API not available, using mock data`)
        const { createMockEnhancedScore } = await import('./tempMockEnhancement')
        const mockResponse = createMockEnhancedScore(candidateId, candidateData)
        console.log(`[Scoring] Mock enhancement response:`, mockResponse)
        return mockResponse
      }
    } catch (error) {
      console.error(`[Scoring] Enhancement error for candidate ${candidateId}:`, error)
      throw error
    }
  },
}