import apiClient from './api'
import { ScoreResponse, ScoreVersion } from '../types/score'

export const scoringService = {
  // Get candidate score
  getScore: async (candidateId: string, version: ScoreVersion = 'original'): Promise<ScoreResponse> => {
    const response = await apiClient.get<ScoreResponse>(`/scores/candidate/${candidateId}`, {
      params: { version },
    })
    return response.data
  },

  // Enhance candidate score using Gemini
  enhanceScore: async (candidateId: string): Promise<ScoreResponse> => {
    const response = await apiClient.post<ScoreResponse>(`/candidates/${candidateId}/enhance`)
    return response.data
  },
}
