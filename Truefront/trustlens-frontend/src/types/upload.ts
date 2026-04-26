/**
 * Upload-related type definitions
 */

export interface UploadProgress {
  loaded: number
  total: number
  percentage: number
}

export interface BatchUploadFile {
  file: File
  candidateName: string
  candidateEmail: string
  requiredSkills: string[]
  jobRole: string
}

export interface UploadResponse {
  id: string
  name: string
  email: string
  job_role: string
  skills: string[]
  status: 'pending' | 'processing' | 'completed' | 'error'
  created_at: string
  file_url?: string
  file_name?: string
  file_size?: number
}

export interface BatchUploadResponse {
  total: number
  successful: number
  failed: number
  results: (UploadResponse | UploadError)[]
}

export interface UploadError {
  file_name: string
  error: string
  status_code: number
}

export interface FileValidationError {
  file: string
  message: string
  code: 'invalid_type' | 'invalid_size' | 'invalid_name'
}

export interface UploadMetadata {
  uploadedAt: Date
  uploadedBy?: string
  totalFiles: number
  successCount: number
  failureCount: number
  duration: number // in milliseconds
}
