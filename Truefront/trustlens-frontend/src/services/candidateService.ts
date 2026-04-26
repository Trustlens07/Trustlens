import apiClient from './api'
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
    const response = await apiClient.get<CandidateListResponse>('/candidates', { params })
    return response.data
  },

  // Get single candidate details
  getCandidate: async (id: string): Promise<CandidateDetail> => {
    const response = await apiClient.get<CandidateDetail>(`/candidates/${id}`)
    return response.data
  },

  // Get candidate status with score
  getCandidateStatus: async (id: string): Promise<CandidateStatusWithScore> => {
    const response = await apiClient.get<CandidateStatusWithScore>(`/candidates/${id}/status`)
    return response.data
  },

  // Upload single candidate
  uploadCandidate: async (data: UploadCandidateRequest): Promise<Candidate> => {
    const formData = new FormData()
    formData.append('name', data.name)
    formData.append('email', data.email)
    // Send skills as comma-separated string instead of JSON
    formData.append('skills', data.skills.join(','))
    formData.append('job_role', data.job_role)
    // Backend expects the file field
    formData.append('file', data.resume)

    console.log('[Upload] Sending candidate:', {
      name: data.name,
      email: data.email,
      skills: data.skills,
      job_role: data.job_role,
      resumeField: 'resume',
      fileName: data.resume.name,
      fileSize: data.resume.size,
    })

    try {
      const response = await apiClient.post<Candidate>('/upload', formData)
      console.log('[Upload] Success:', response.data)
      return response.data
    } catch (error: any) {
      console.error('[Upload] Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        headers: error.response?.headers,
      })
      throw error
    }
  },

  // Batch upload candidates
  batchUploadCandidates: async (data: BatchUploadRequest): Promise<Candidate[]> => {
    const formData = new FormData()
    
    // Create candidate metadata array
    const candidatesMetadata = data.candidates.map(c => ({
      name: c.name,
      email: c.email,
      skills: c.skills.join(','), // Send as comma-separated string
      job_role: c.job_role,
    }))
    
    formData.append('candidates', JSON.stringify(candidatesMetadata))
    
    // Append each resume file - backend expects 'files' field
    data.candidates.forEach((c) => {
      formData.append('files', c.resume)
    })

    console.log('[Batch Upload] Sending candidates:', {
      count: data.candidates.length,
      candidates: candidatesMetadata,
      resumeFiles: data.candidates.map(c => ({ name: c.resume.name, size: c.resume.size })),
    })

    try {
      const response = await apiClient.post<Candidate[]>('/upload/batch', formData)
      console.log('[Batch Upload] Success:', response.data)
      return response.data
    } catch (error: any) {
      console.error('[Batch Upload] Error details:', {
        status: error.response?.status,
        data: error.response?.data,
        headers: error.response?.headers,
      })
      throw error
    }
  },

  // Process candidate (trigger ML)
  processCandidate: async (id: string): Promise<ProcessCandidateResponse> => {
    const response = await apiClient.post<ProcessCandidateResponse>(`/candidates/${id}/process`)
    return response.data
  },

  // Delete candidate
  deleteCandidate: async (id: string): Promise<DeleteCandidateResponse> => {
    const response = await apiClient.delete<DeleteCandidateResponse>(`/candidates/${id}`)
    return response.data
  },

  // Enhance candidate with AI bias correction
  enhanceCandidate: async (id: string): Promise<any> => {
    const response = await apiClient.post(`/candidates/${id}/enhance`)
    return response.data
  },
}
