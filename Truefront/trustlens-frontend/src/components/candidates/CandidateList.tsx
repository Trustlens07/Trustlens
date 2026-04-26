import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Candidate } from '../../types/candidate'
import { CandidateCard } from './CandidateCard'
import { LoadingSpinner } from '../common/LoadingSpinner'
import { EmptyState } from '../common/EmptyState'

interface CandidateListProps {
  candidates: Candidate[]
  isLoading?: boolean
}

export const CandidateList: React.FC<CandidateListProps> = ({
  candidates,
  isLoading = false,
}) => {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (candidates.length === 0) {
    return (
      <EmptyState
        title="No Candidates Yet"
        description="Get started by uploading your first resume to begin the fair hiring process."
        action={{
          label: 'Upload Candidate',
          onClick: () => navigate('/upload'),
        }}
      />
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {candidates.map((candidate) => (
        <CandidateCard key={candidate.id} candidate={candidate} />
      ))}
    </div>
  )
}
