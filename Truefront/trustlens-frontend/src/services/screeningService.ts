import apiClient from './api'
import {
  ScreeningRequest,
  ScreeningSession,
  ScreeningResultsResponse,
  FairnessReport,
} from '../types/screening'

export const screeningService = {
  // Start batch screening
  screenResumes: async (data: ScreeningRequest): Promise<ScreeningSession> => {
    const response = await apiClient.post<ScreeningSession>('/screening/screen-resumes', data)
    return response.data
  },

  // Get screening results
  getScreeningResults: async (sessionId: string): Promise<ScreeningResultsResponse> => {
    const response = await apiClient.get<ScreeningResultsResponse>(`/screening/results/${sessionId}`)
    return response.data
  },

  // Get fairness report
  getFairnessReport: async (sessionId: string): Promise<FairnessReport> => {
    const response = await apiClient.get<FairnessReport>(`/screening/fairness-report/${sessionId}`)
    return response.data
  },
}
