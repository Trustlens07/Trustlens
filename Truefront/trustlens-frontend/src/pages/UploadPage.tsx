import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { candidateService } from '../services/candidateService'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const navigate = useNavigate()
  // const { user, loading: authLoading } = useAuth()
  const [isBatch, setIsBatch] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [skills, setSkills] = useState('')
  const [jobRole, setJobRole] = useState('')
  const [resume, setResume] = useState<File | null>(null)
  const [batchFiles, setBatchFiles] = useState<File[]>([])
  const [isLoading, setIsLoading] = useState(false)

  // if (authLoading) {
  //   return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  // }

  // if (!user) {
  //   navigate('/login')
  //   return null
  // }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: isBatch ? 10 : 1,
    onDrop: (acceptedFiles) => {
      if (isBatch) {
        setBatchFiles(acceptedFiles)
      } else {
        setResume(acceptedFiles[0] || null)
      }
    },
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    let loadingToastId: string | undefined = undefined
    let timeoutId: number | undefined

    try {
      if (isBatch) {
        if (batchFiles.length === 0) {
          toast.error('Please select at least one resume')
          setIsLoading(false)
          return
        }
        
        // Call batch upload API with timeout
        loadingToastId = toast.loading(`Uploading ${batchFiles.length} resumes... This may take a moment while the backend processes them.`)
        
        // Set a timeout to warn user if it's taking too long
        timeoutId = window.setTimeout(() => {
          if (loadingToastId) {
            toast.loading('Still processing... The backend is analyzing the resumes.', { id: loadingToastId })
          }
        }, 15000)
        
        const uploadedCandidates = await candidateService.batchUploadCandidates({
          candidates: batchFiles.map((file, index) => ({
            name: name || `Candidate ${index + 1}`,
            email: email || `candidate${index + 1}@example.com`,
            skills: skills ? skills.split(',').map(s => s.trim()) : [],
            job_role: jobRole || 'Unknown Role',
            resume: file,
          })),
        })
        console.log('[Upload] Batch upload response:', uploadedCandidates)
        toast.success(`Batch uploaded successfully! ${uploadedCandidates.length} candidates added`)
        
        // Navigate to candidate list (Dashboard) to show uploaded candidates
        console.log('[Upload] Candidates uploaded successfully, redirecting to candidate list')
        setTimeout(() => navigate('/'), 1000)
      } else {
        if (!resume) {
          toast.error('Please select a resume file')
          setIsLoading(false)
          return
        }
        if (!name || !email || !skills || !jobRole) {
          toast.error('Please fill in all required fields')
          setIsLoading(false)
          return
        }
        
        // Call single upload API with timeout
        loadingToastId = toast.loading('Uploading resume... This may take a moment while the backend processes the resume.')
        
        // Set a timeout to warn user if it's taking too long
        timeoutId = window.setTimeout(() => {
          if (loadingToastId) {
            toast.loading('Still processing... The backend is analyzing the resume.', { id: loadingToastId })
          }
        }, 15000)
        
        const uploadedCandidate = await candidateService.uploadCandidate({
          name,
          email,
          skills: skills.split(',').map(s => s.trim()),
          job_role: jobRole,
          resume,
        })
        console.log('[Upload] Single upload response:', uploadedCandidate)
        toast.success(`${uploadedCandidate.name} uploaded successfully!`)
        
        // Navigate to candidate list (Dashboard) to show uploaded candidate
        console.log('[Upload] Candidate uploaded successfully, redirecting to candidate list')
        setTimeout(() => navigate('/'), 1000)
      }
      
      // Reset form
      setName('')
      setEmail('')
      setSkills('')
      setJobRole('')
      setResume(null)
      setBatchFiles([])
      
      // Fallback redirect to candidate list if specific redirect didn't work
      setTimeout(() => {
        console.log('[Upload] Fallback redirect to candidate list')
        navigate('/')
      }, 2000)
    } catch (error: any) {
      let errorMsg = 'Upload failed'
      
      if (error.code === 'ECONNABORTED') {
        errorMsg = 'Upload timed out. The backend may be overloaded. Please try again.'
      } else if (error.response?.status === 422) {
        // Validation error - show detailed info
        const detail = error.response?.data?.detail
        if (Array.isArray(detail)) {
          errorMsg = detail.map((err: any) => `${err.loc?.join('.')}: ${err.msg}`).join(', ')
        } else if (typeof detail === 'string') {
          errorMsg = detail
        } else {
          errorMsg = 'Invalid input. Please check all fields are filled correctly.'
        }
      } else if (error.response?.data?.detail) {
        errorMsg = error.response.data.detail
      } else if (error.response?.status === 404) {
        errorMsg = 'Backend API endpoint not found. Please check the backend is running.'
      } else if (error.message) {
        errorMsg = error.message
      }
      
      toast.error(errorMsg)
      console.error('Upload error:', {
        message: error.message,
        code: error.code,
        status: error.response?.status,
        data: error.response?.data,
      })
    } finally {
      if (timeoutId) {
        clearTimeout(timeoutId)
      }
      if (loadingToastId) {
        toast.dismiss(loadingToastId)
      }
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TrustLens</h1>
              <p className="text-sm text-gray-600">Fair AI Recruitment Platform</p>
            </div>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload Resume</h2>

          {/* Batch Toggle */}
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setIsBatch(false)}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                !isBatch ? 'bg-white text-gray-900 shadow' : 'text-gray-600'
              }`}
            >
              Single Upload
            </button>
            <button
              onClick={() => setIsBatch(true)}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-colors ${
                isBatch ? 'bg-white text-gray-900 shadow' : 'text-gray-600'
              }`}
            >
              Batch Upload
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input {...getInputProps()} />
              <div className="text-gray-600">
                {isDragActive ? (
                  <p>Drop the files here...</p>
                ) : (
                  <>
                    <p className="text-lg font-medium mb-2">
                      {isBatch ? 'Drag & drop multiple resumes' : 'Drag & drop a resume'}
                    </p>
                    <p className="text-sm">or click to browse (PDF, DOC, DOCX)</p>
                  </>
                )}
              </div>
              {isBatch && batchFiles.length > 0 && (
                <div className="mt-4 text-sm text-gray-700">
                  {batchFiles.length} file(s) selected
                </div>
              )}
              {!isBatch && resume && (
                <div className="mt-4 text-sm text-gray-700">{resume.name}</div>
              )}
            </div>

            {/* Form Fields */}
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Name {isBatch && '(Optional - will use default if not provided)'}
                </label>
                <input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required={!isBatch}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="John Doe"
                />
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  Email {isBatch && '(Optional - will use default if not provided)'}
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required={!isBatch}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="john@example.com"
                />
              </div>

              <div>
                <label htmlFor="jobRole" className="block text-sm font-medium text-gray-700 mb-1">
                  Job Role {isBatch && '(Optional - will use default if not provided)'}
                </label>
                <input
                  id="jobRole"
                  type="text"
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  required={!isBatch}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Software Engineer"
                />
              </div>

              <div>
                <label htmlFor="skills" className="block text-sm font-medium text-gray-700 mb-1">
                  Skills {isBatch && '(Optional - will use default if not provided)'}
                </label>
                <input
                  id="skills"
                  type="text"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  required={!isBatch}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="React, TypeScript, Node.js (comma-separated)"
                />
                <p className="text-xs text-gray-500 mt-1">Separate skills with commas</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {isLoading
                ? 'Uploading...'
                : isBatch
                ? 'Upload Batch'
                : 'Upload Candidate'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
