import apiClient from './api'
import { BiasMetricsResponse, BiasScoreVersion } from '../types/bias'
import { generateMockBiasAnalysis } from './mockBiasService'

export const biasService = {
  getBiasMetrics: async (
    candidateId: string,
    version: BiasScoreVersion = 'original'
  ): Promise<BiasMetricsResponse> => {
    try {
      console.log(`[BiasService] Getting bias metrics for candidate ${candidateId}, version: ${version}`)

      const response = await apiClient.get<any>('/bias/metrics', {
        params: { candidate_id: candidateId, version },  // ← pass version to backend
      })
      console.log(`[BiasService] Raw response:`, response.data)

      const biasData = response.data?.data || response.data
      console.log(`[BiasService] Extracted bias data:`, biasData)

      // Handle original vs enhanced response shapes
      let metrics = []
      if (version === 'original') {
        metrics = biasData?.metrics || []
      } else if (version === 'enhanced') {
        // Enhanced returns a single flat record, wrap it
        const enhancedMetrics = biasData?.enhanced_bias_metrics
        if (enhancedMetrics) {
          metrics = Array.isArray(enhancedMetrics)
            ? enhancedMetrics
            : Object.entries(enhancedMetrics).map(([key, val]: [string, any]) => ({
                metric_name: key,
                group_type: val.group_type ?? 'overall',
                group_name: val.group_name ?? 'overall',
                metric_value: val.metric_value ?? val.value ?? 0,
                is_biased: val.is_biased ?? 'no',
                details: val.details ?? {},
                calculated_at: biasData.bias_enhanced_at ?? new Date().toISOString(),
              }))
        } else {
          // Fallback: treat the flat record as a single metric
          metrics = [{
            metric_name: biasData.metric_name ?? 'bias_analysis',
            group_type: biasData.group_type ?? 'overall',
            group_name: biasData.group_name ?? 'overall',
            metric_value: biasData.metric_value ?? 0,
            is_biased: biasData.is_biased ?? 'no',
            details: {},
            calculated_at: biasData.bias_enhanced_at ?? new Date().toISOString(),
          }]
        }
      }

      // Derive overall_fairness_score from metrics since backend doesn't send it
      const fairnessScore = metrics.length > 0
        ? Math.round(
            (metrics.reduce((sum: number, m: any) => sum + (m.metric_value ?? 0), 0) / metrics.length) * 100
          )
        : 0

      const result: BiasMetricsResponse = {
        candidate_id: candidateId,
        version: version,
        metrics,
        overall_fairness_score: fairnessScore,
        demographic_breakdown: biasData?.demographic_breakdown ?? {},
        calculated_at: biasData?.calculated_at ?? biasData?.bias_enhanced_at ?? new Date().toISOString(),
      }

      console.log(`[BiasService] Final formatted result:`, result)
      return result
    } catch (error) {
      console.warn(`[BiasService] Failed to fetch bias metrics, using fallback`)
      console.error(`[BiasService] Error details:`, error)

      return {
        candidate_id: candidateId,
        version: version,
        metrics: [],
        overall_fairness_score: 0,
        demographic_breakdown: {},
        calculated_at: new Date().toISOString(),
      }
    }
  },

  analyzeBias: async (data: {
    candidates: Array<{ candidate_id: string; score: number; attributes: Record<string, any> }>
  }): Promise<any> => {
    console.log('[BiasService] Analyzing bias for candidates:', data.candidates.length)
    try {
      const response = await apiClient.post('/bias/analyze', data)
      const analysisData = response.data?.data || response.data
      console.log('[BiasService] Extracted analysis data:', analysisData)
      return analysisData
    } catch (error) {
      console.warn('[BiasService] Backend API failed, using mock analysis')
      return generateMockBiasAnalysis(data.candidates)
    }
  },
}