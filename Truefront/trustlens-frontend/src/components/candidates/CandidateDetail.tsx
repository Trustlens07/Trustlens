import React from 'react'
import { CandidateDetail as CandidateDetailType } from '../../types/candidate'
import { formatDate } from '../../utils/dates'

interface CandidateDetailProps {
  candidate: CandidateDetailType
}

export const CandidateDetail: React.FC<CandidateDetailProps> = ({ candidate }) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900">{candidate.name}</h2>
        <p className="text-gray-600">{candidate.email}</p>
        <p className="text-sm text-gray-500 mt-1">{candidate.job_role}</p>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Status</h3>
          <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
            {candidate.status}
          </span>
        </div>
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Created</h3>
          <p className="text-sm text-gray-600">{formatDate(candidate.created_at)}</p>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Skills</h3>
        <div className="flex flex-wrap gap-2">
          {candidate.skills.map((skill, index) => (
            <span
              key={index}
              className="inline-block px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs"
            >
              {skill}
            </span>
          ))}
        </div>
      </div>

    </div>
  )
}
