import apiClient from './api'
import { screeningService } from './screeningService'
import {
  Candidate,
  CandidateListResponse,
  CandidateDetail,
  UploadCandidateRequest,
  BatchUploadRequest,
  ProcessCandidateResponse,
  DeleteCandidateResponse,
} from '../types/candidate'
import { CandidateStatusWithScore } from '../types/score'
import { FilterParams } from '../types/api'

export const candidateService = {
  // Get all candidates with optional filters
  getCandidates: async (params: FilterParams = {}): Promise<CandidateListResponse> => {
    try {
      const response = await apiClient.get<any>('/candidates', { params })
      const data = response.data
      
      if (Array.isArray(data)) {
        return { candidates: data, total: data.length, skip: 0, limit: 10 }
      }
      return data
    } catch (error) {
      console.error('[Candidates] Get candidates error:', error)
      throw error
    }
  },

  // Get single candidate details
  getCandidate: async (id: string): Promise<CandidateDetail> => {
    try {
      const response = await apiClient.get<CandidateDetail>(`/candidates/${id}`)
      return response.data
    } catch (error) {
      console.error(`[Candidates] Get candidate ${id} error:`, error)
      throw error
    }
  },

  // Get candidate status with score
  getCandidateStatus: async (id: string): Promise<CandidateStatusWithScore> => {
    try {
      const response = await apiClient.get<CandidateStatusWithScore>(`/candidates/${id}/status`)
      return response.data
    } catch (error) {
      console.error(`[Candidates] Get candidate status ${id} error:`, error)
      throw error
    }
  },

  // Upload single candidate
  uploadCandidate: async (data: UploadCandidateRequest): Promise<Candidate> => {
    try {
      const formData = new FormData()
      formData.append('name', data.name)
      formData.append('email', data.email)
      formData.append('skills', data.skills.join(','))
      formData.append('job_role', data.job_role)
      formData.append('file', data.resume)

      console.log('[Upload] Uploading candidate:', {
        name: data.name,
        email: data.email,
        skills: data.skills,
        job_role: data.job_role,
        fileName: data.resume.name,
      })

      const response = await apiClient.post<Candidate>('/upload', formData)
      console.log('[Upload] Success:', response.data)
      return response.data
    } catch (error) {
      console.error('[Upload] Error:', error)
      throw error
    }
  },

  // Batch upload candidates
  batchUploadCandidates: async (data: BatchUploadRequest): Promise<Candidate[]> => {
    try {
      const formData = new FormData()
      const candidatesMetadata = data.candidates.map(c => ({
        name: c.name,
        email: c.email,
        skills: c.skills.join(','),
        job_role: c.job_role,
      }))
      
      formData.append('candidates', JSON.stringify(candidatesMetadata))
      
      data.candidates.forEach(c => {
        formData.append('files', c.resume)
      })

      console.log('[Batch Upload] Uploading candidates:', {
        count: data.candidates.length,
        candidates: candidatesMetadata,
      })

      const response = await apiClient.post<Candidate[]>('/upload/batch', formData)
      console.log('[Batch Upload] Success:', response.data)
      return response.data
    } catch (error) {
      console.error('[Batch Upload] Error:', error)
      throw error
    }
  },

  // Screen candidates after upload
  screenCandidates: async (candidates: Candidate[], jobRole: string, jobDescription: string) => {
    try {
      console.log('[Screening] Starting screening for', candidates.length, 'candidates')
      
      const session = await screeningService.screenResumes({
        job_role: jobRole,
        job_description: jobDescription,
        fairness_mode: 'standard',
        resumes: candidates.map(c => ({
          candidate_id: c.id,
          name: c.name,
          email: c.email,
          skills: Array.isArray(c.skills) ? c.skills : [],
        })),
      })

      console.log('[Screening] Session created:', session)
      return session
    } catch (error) {
      console.error('[Screening] Error:', error)
      throw error
    }
  },

  // Process candidate (trigger ML)
  processCandidate: async (id: string): Promise<ProcessCandidateResponse> => {
    try {
      const response = await apiClient.post<ProcessCandidateResponse>(`/candidates/${id}/process`)
      return response.data
    } catch (error) {
      console.error(`[Candidates] Process candidate ${id} error:`, error)
      throw error
    }
  },

  // Delete candidate
  deleteCandidate: async (id: string): Promise<DeleteCandidateResponse> => {
    try {
      const response = await apiClient.delete<DeleteCandidateResponse>(`/candidates/${id}`)
      return response.data
    } catch (error) {
      console.error(`[Candidates] Delete candidate ${id} error:`, error)
      throw error
    }
  },

  // Enhance candidate with AI bias correction
  enhanceCandidate: async (id: string): Promise<any> => {
    try {
      const response = await apiClient.post(`/candidates/${id}/enhance`)
      return response.data
    } catch (error) {
      console.error(`[Candidates] Enhance candidate ${id} error:`, error)
      throw error
    }
  },
}