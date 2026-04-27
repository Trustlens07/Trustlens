// Comprehensive Mock Backend - covers all services
import {
  Candidate,
  CandidateListResponse,
  CandidateDetail,
  ProcessCandidateResponse,
} from '../types/candidate'
import { BiasMetricsResponse } from '../types/bias'
import { CandidateStatusWithScore } from '../types/score'
import { FeedbackResponse } from '../types/feedback'

// In-memory data store
const mockCandidates = new Map<string, Candidate>()
const mockCandidateDetails = new Map<string, CandidateDetail>()

// Initialize with some mock data
const initializeMockData = () => {
  const mockCandidatesList: Candidate[] = [
    {
      candidate_id: 'cand_1',
      name: 'John Doe',
      email: 'john@example.com',
      job_role: 'Software Engineer',
      skills: ['JavaScript', 'React', 'Node.js'],
      original_score: 85,
      enhanced_score: 87,
      fairness_adjusted_score: 88,
      status: 'recommended',
      resume_url: 'https://example.com/resume1.pdf',
      created_at: new Date().toISOString(),
    },
    {
      candidate_id: 'cand_2',
      name: 'Jane Smith',
      email: 'jane@example.com',
      job_role: 'Software Engineer',
      skills: ['Python', 'Django', 'PostgreSQL'],
      original_score: 82,
      enhanced_score: 85,
      fairness_adjusted_score: 86,
      status: 'recommended',
      resume_url: 'https://example.com/resume2.pdf',
      created_at: new Date().toISOString(),
    },
    {
      candidate_id: 'cand_3',
      name: 'Mike Johnson',
      email: 'mike@example.com',
      job_role: 'Software Engineer',
      skills: ['Java', 'Spring Boot', 'MySQL'],
      original_score: 78,
      enhanced_score: 80,
      fairness_adjusted_score: 82,
      status: 'under_review',
      resume_url: 'https://example.com/resume3.pdf',
      created_at: new Date().toISOString(),
    },
  ]

  mockCandidatesList.forEach(candidate => {
    mockCandidates.set(candidate.candidate_id, candidate)
    mockCandidateDetails.set(candidate.candidate_id, {
      ...candidate,
      feedback: [],
      bias_flags: [],
      enhancement_suggestions: [],
    })
  })
}

initializeMockData()

export const completeMockBackendService = {
  // Candidate Service
  getCandidates: async (params: any = {}): Promise<CandidateListResponse> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    const candidates = Array.from(mockCandidates.values())
    
    let filtered = candidates
    if (params.job_role) {
      filtered = filtered.filter((c: Candidate) => c.job_role === params.job_role)
    }
    if (params.status) {
      filtered = filtered.filter((c: Candidate) => c.status === params.status)
    }

    return {
      candidates: filtered,
      total: filtered.length,
      page: params.page || 1,
      limit: params.limit || 10,
    }
  },

  getCandidate: async (id: string): Promise<CandidateDetail> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    const candidate = mockCandidateDetails.get(id)
    if (!candidate) throw new Error(`Candidate ${id} not found`)
    return candidate
  },

  getCandidateStatus: async (id: string): Promise<CandidateStatusWithScore> => {
    await new Promise(resolve => setTimeout(resolve, 200))
    const candidate = mockCandidates.get(id)
    if (!candidate) throw new Error(`Candidate ${id} not found`)
    
    return {
      candidate_id: id,
      status: candidate.status,
      original_score: candidate.original_score,
      enhanced_score: candidate.enhanced_score,
      fairness_adjusted_score: candidate.fairness_adjusted_score,
    }
  },

  uploadCandidate: async (data: any): Promise<Candidate> => {
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const newCandidate: Candidate = {
      candidate_id: `cand_${Date.now()}`,
      name: data.name,
      email: data.email,
      job_role: data.job_role,
      skills: data.skills,
      original_score: Math.random() * 100,
      enhanced_score: Math.random() * 100,
      fairness_adjusted_score: Math.random() * 100,
      status: 'under_review',
      resume_url: `https://example.com/resume_${Date.now()}.pdf`,
      created_at: new Date().toISOString(),
    }

    mockCandidates.set(newCandidate.candidate_id, newCandidate)
    mockCandidateDetails.set(newCandidate.candidate_id, {
      ...newCandidate,
      feedback: [],
      bias_flags: [],
      enhancement_suggestions: [],
    })

    return newCandidate
  },

  deleteCandidate: async (id: string): Promise<void> => {
    await new Promise(resolve => setTimeout(resolve, 200))
    mockCandidates.delete(id)
    mockCandidateDetails.delete(id)
  },

  // Bias Service
  getBiasMetrics: async (candidateId: string, version = 'original'): Promise<BiasMetricsResponse> => {
    await new Promise(resolve => setTimeout(resolve, 400))
    
    return {
      candidate_id: candidateId,
      version,
      demographic_parity: {
        gender: Math.random() * 20 - 10,
        race: Math.random() * 20 - 10,
        age: Math.random() * 20 - 10,
      },
      equalized_odds: {
        true_positive_rate_diff: Math.random() * 15,
        false_positive_rate_diff: Math.random() * 15,
      },
      calibration: {
        prediction_accuracy: 0.85 + Math.random() * 0.1,
        fairness_score: 0.75 + Math.random() * 0.15,
      },
      bias_flags: Math.random() > 0.7 ? ['potential-gender-bias'] : [],
    }
  },

  analyzeBias: async (data: any): Promise<any> => {
    await new Promise(resolve => setTimeout(resolve, 600))
    
    return {
      analysis_id: `analysis_${Date.now()}`,
      timestamp: new Date().toISOString(),
      overall_bias_score: Math.random() * 100,
      recommendations: [
        'Review scoring criteria for consistency',
        'Monitor demographic distribution in hiring decisions',
        'Consider additional fairness constraints',
      ],
    }
  },

  // Scoring Service
  getScores: async (candidateId: string): Promise<any> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    return {
      candidate_id: candidateId,
      original_score: Math.random() * 100,
      enhanced_score: Math.random() * 100,
      fairness_adjusted_score: Math.random() * 100,
      score_breakdown: {
        technical_skills: Math.random() * 100,
        experience: Math.random() * 100,
        cultural_fit: Math.random() * 100,
      },
    }
  },

  // Feedback Service
  submitFeedback: async (data: any): Promise<FeedbackResponse> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    return {
      feedback_id: `feedback_${Date.now()}`,
      candidate_id: data.candidate_id,
      rating: data.rating,
      comment: data.comment,
      created_at: new Date().toISOString(),
    }
  },

  getFeedback: async (candidateId: string): Promise<any> => {
    await new Promise(resolve => setTimeout(resolve, 300))
    
    return {
      candidate_id: candidateId,
      feedback: [
        {
          feedback_id: 'fb_1',
          rating: 4,
          comment: 'Great technical skills',
          created_at: new Date().toISOString(),
        },
      ],
    }
  },
}
