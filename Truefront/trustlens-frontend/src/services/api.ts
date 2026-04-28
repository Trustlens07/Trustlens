import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { getAuthToken } from './firebaseConfig'

// ==================== TYPES ====================

export interface Candidate {
  id: string
  name?: string
  email?: string
  file_name: string
  file_url: string
  file_size: number
  file_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  phone?: string
  application_id?: string
  required_skills?: string[]
  job_role?: string
  parsed_data?: Record<string, unknown>
  error_message?: string
}

export interface CandidateCreateRequest {
  name?: string
  email?: string
  file_id?: string
  storage_url?: string
}

export interface CandidateCreateResponse {
  id: string
  name?: string
  email?: string
  file_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
}

export interface UploadResumeRequest {
  file: File
  candidate_name?: string
  candidate_email?: string
  required_skills?: string
  job_role?: string
}

export interface UploadResumeResponse {
  candidate_id: string
  application_id: string
  file_id: string
  filename: string
  size_bytes: number
  storage_url: string
  required_skills?: string[]
  job_role?: string
  uploaded_at: string
}

export interface BatchUploadRequest {
  files: File[]
  job_role?: string
}

export interface BatchUploadResponse {
  uploaded: UploadResumeResponse[]
  failed: { filename: string; error: string }[]
}

export interface UpdateSkillsRequest {
  required_skills: string[]
}

export interface ResumeInput {
  filename: string
  content: string
  file_type?: string
  name?: string
  email?: string
}

export type FairnessMode = 'balanced' | 'strict' | 'minimal'

export interface BatchScreeningRequest {
  job_role: string
  job_description: string
  fairness_mode?: FairnessMode
  resumes: ResumeInput[]
}

export interface ScreeningResult {
  application_id: string
  name?: string
  email?: string
  skills: string[]
  score: number
  status: 'shortlisted' | 'rejected'
  reason: string
}

export interface BatchScreeningResponse {
  session_id: string
  total: number
  shortlisted: number
  results: ScreeningResult[]
}

export type DecisionType = 'accepted' | 'rejected'

export interface UpdateDecisionRequest {
  decision: DecisionType
  notes?: string
}

export interface ExportResultsRequest {
  session_id: string
  format?: 'csv' | 'json'
}

export interface CandidateScore {
  candidate_id: string
  overall_score: number
  skill_score: number
  experience_score: number
  education_score: number
  breakdown: Record<string, unknown>
  version: number
}

export interface CandidateWithScore extends Candidate {
  score?: CandidateScore
}

export interface ApiError {
  detail: string
}

// Use environment variable or default to deployed backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://resume-backend-948277799081.us-central1.run.app'

console.log('[API] === CONFIG v3.0 ===')
console.log('[API] Environment:', import.meta.env.MODE)
console.log('[API] Base URL:', `${API_BASE_URL}/api/v1`)
console.log('[API] Timestamp:', new Date().toISOString())

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 second timeout
  withCredentials: false, // Don't send credentials for CORS
})

// Add request interceptor to handle preflight requests
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    // For file uploads, don't set Content-Type - let browser set it with boundary
    if (config.data instanceof FormData && config.headers) {
      delete config.headers['Content-Type']
    }

    const token = await getAuthToken()
    if (token) {
      config.headers = config.headers ?? {}
      config.headers.Authorization = `Bearer ${token}`
    }
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`, { baseURL: API_BASE_URL })
    return config
  },
  (error: AxiosError) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.debug(`[API] Response: ${response.status}`, response.config.url)
    return response
  },
  async (error: AxiosError) => {
    const responseData = error.response?.data as any
    const errorMessage = responseData?.detail || error.message || 'Unknown error'
    const isError = error.response?.status && error.response.status >= 500
    const logMessage = '[API] Response error:'
    const logData = {
      status: error.response?.status,
      url: error.config?.url,
      message: errorMessage,
    }
    if (isError) {
      console.error(logMessage, logData)
    } else {
      console.debug(logMessage, logData)
    }

    if (error.response?.status === 401) {
      // Token expired, try to refresh
      const refreshToken = localStorage.getItem('firebase_refresh_token')
      if (refreshToken) {
        try {
          // In a real app, you'd call Firebase to refresh the token
          // For now, we'll just clear the tokens and redirect to login
          localStorage.removeItem('firebase_token')
          localStorage.removeItem('firebase_refresh_token')
          window.location.href = '/login'
        } catch (refreshError) {
          localStorage.removeItem('firebase_token')
          localStorage.removeItem('firebase_refresh_token')
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient

// ==================== API METHODS ====================

/**
 * Create a new candidate
 * POST /candidates
 * Requires: file_id OR storage_url
 */
export const createCandidate = async (
  data: CandidateCreateRequest
): Promise<CandidateCreateResponse> => {
  if (!data.file_id && !data.storage_url) {
    throw new Error('Either file_id or storage_url must be provided')
  }
  const response = await apiClient.post<CandidateCreateResponse>('/candidates', data)
  return response.data
}

/**
 * Upload a single resume file
 * POST /upload
 * Requires: file (binary)
 */
export const uploadResume = async (
  data: UploadResumeRequest
): Promise<UploadResumeResponse> => {
  const formData = new FormData()
  formData.append('file', data.file)
  if (data.candidate_name) formData.append('candidate_name', data.candidate_name)
  if (data.candidate_email) formData.append('candidate_email', data.candidate_email)
  if (data.required_skills) formData.append('required_skills', data.required_skills)
  if (data.job_role) formData.append('job_role', data.job_role)

  const response = await apiClient.post<UploadResumeResponse>('/upload', formData)
  return response.data
}

/**
 * Upload multiple resume files in batch
 * POST /upload/batch
 * Requires: files (list of binaries)
 */
export const uploadBatchResumes = async (
  data: BatchUploadRequest
): Promise<BatchUploadResponse> => {
  const formData = new FormData()
  data.files.forEach((file) => formData.append('files', file))
  if (data.job_role) formData.append('job_role', data.job_role)

  const response = await apiClient.post<BatchUploadResponse>('/upload/batch', formData)
  return response.data
}

/**
 * Update required skills for a candidate
 * PUT /candidates/{id}/skills
 * Requires: required_skills (array)
 */
export const updateCandidateSkills = async (
  id: string,
  data: UpdateSkillsRequest
): Promise<Candidate> => {
  const response = await apiClient.put<Candidate>(`/candidates/${id}/skills`, data)
  return response.data
}

/**
 * List all candidates with optional status filter
 * GET /candidates
 */
export const listCandidates = async (
  status?: Candidate['status']
): Promise<CandidateWithScore[]> => {
  const params = status ? { status } : {}
  const response = await apiClient.get<CandidateWithScore[]>('/candidates', { params })
  return response.data
}

/**
 * Get a single candidate by ID
 * GET /candidates/{id}
 */
export const getCandidate = async (id: string): Promise<CandidateWithScore> => {
  const response = await apiClient.get<CandidateWithScore>(`/candidates/${id}`)
  return response.data
}

/**
 * Delete a candidate by ID
 * DELETE /candidates/{id}
 */
export const deleteCandidate = async (id: string): Promise<void> => {
  await apiClient.delete(`/candidates/${id}`)
}

/**
 * Run batch screening on resumes
 * POST /screening/screen-resumes
 * Requires: job_role, job_description, resumes
 */
export const screenResumes = async (
  data: BatchScreeningRequest
): Promise<BatchScreeningResponse> => {
  const response = await apiClient.post<BatchScreeningResponse>('/screening/screen-resumes', {
    ...data,
    fairness_mode: data.fairness_mode || 'balanced',
  })
  return response.data
}

/**
 * Update screening decision for an application
 * PUT /screening/decisions/{application_id}
 * Requires: decision ("accepted" or "rejected")
 */
export const updateScreeningDecision = async (
  applicationId: string,
  data: UpdateDecisionRequest
): Promise<void> => {
  await apiClient.put(`/screening/decisions/${applicationId}`, data)
}

/**
 * Export screening results
 * POST /screening/export
 * Requires: session_id
 */
export const exportScreeningResults = async (
  data: ExportResultsRequest
): Promise<Blob> => {
  const response = await apiClient.post('/screening/export', {
    session_id: data.session_id,
    format: data.format || 'csv',
  }, {
    responseType: 'blob',
  })
  return response.data
}
