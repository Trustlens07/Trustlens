export type BiasSeverity = 'low' | 'medium' | 'high'

export interface BiasMetric {
  category: string
  indicator: string
  value: number
  threshold: number
  severity: BiasSeverity
  description: string
}

export interface BiasMetricsResponse {
  candidate_id: string
  version: 'original' | 'enhanced'
  metrics: BiasMetric[]
  overall_fairness_score: number
  demographic_breakdown: {
    gender?: Record<string, number>
    race?: Record<string, number>
    age_group?: Record<string, number>
    education?: Record<string, number>
  }
  calculated_at: string
}

export interface DisparityIndicator {
  group: string
  score: number
  benchmark: number
  disparity: number
  severity: BiasSeverity
}

export interface DemographicBreakdown {
  category: string
  groups: Record<string, {
    count: number
    avg_score: number
    selection_rate: number
  }>
}
