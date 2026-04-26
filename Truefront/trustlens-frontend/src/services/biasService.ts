import apiClient from './api'
import { BiasMetricsResponse } from '../types/bias'
import { ScoreVersion } from '../types/score'

export const biasService = {
  // Get bias metrics for a candidate
  getBiasMetrics: async (
    candidateId: string,
    version: ScoreVersion = 'original'
  ): Promise<BiasMetricsResponse> => {
    const response = await apiClient.get<BiasMetricsResponse>('/bias/metrics', {
      params: {
        candidate_id: candidateId,
        version,
      },
    })
    return response.data
  },

  // Analyze bias for multiple candidates
  analyzeBias: async (data: {
    candidates: Array<{ candidate_id: string; score: number; attributes: Record<string, any> }>
  }): Promise<any> => {
    const response = await apiClient.post('/bias/analyze', data)
    return response.data
  },
}
