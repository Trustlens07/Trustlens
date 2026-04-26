import React from 'react'
import { useNavigate } from 'react-router-dom'
import { Candidate } from '../../types/candidate'
import { CandidateStatusBadge } from '../common/CandidateStatusBadge'
import { getInitials } from '../../utils/formatting'

interface CandidateCardProps {
  candidate: Candidate
}

export const CandidateCard: React.FC<CandidateCardProps> = ({ candidate }) => {
  const navigate = useNavigate()

  return (
    <div
      className="card hover:shadow-mid transition-all cursor-pointer"
      onClick={() => navigate(`/candidate/${candidate.id}`)}
    >
      <div className="flex items-start space-x-md">
        <div className="w-12 h-12 bg-primary-fixed rounded-full flex items-center justify-center text-primary font-semibold text-label">
          {getInitials(candidate.name)}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-body font-medium text-on-surface truncate">{candidate.name}</h3>
          <p className="text-label text-on-surface-variant truncate">{candidate.email}</p>
          <p className="text-label text-on-surface-variant mt-xs">{candidate.job_role}</p>
        </div>
        <CandidateStatusBadge status={candidate.status} />
      </div>
      <div className="mt-md flex items-center justify-between">
        <div className="text-label text-on-surface-variant">
          {candidate.skills.length} skill{candidate.skills.length !== 1 ? 's' : ''}
        </div>
        <div className="text-label text-on-surface-variant">
          {new Date(candidate.created_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  )
}
