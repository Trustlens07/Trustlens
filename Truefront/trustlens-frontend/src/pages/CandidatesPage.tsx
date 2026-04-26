import React from 'react'
import { CandidateList } from '../components/candidates/CandidateList'
import { useCandidates } from '../hooks/useCandidates'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import { Header } from '../components/common/Header'
import { Sidebar } from '../components/common/Sidebar'

const CandidatesPage: React.FC = () => {
  const { data, isLoading } = useCandidates()

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex">
        <Sidebar />
        <div className="main-content">
          <div className="container-fluid py-lg">
            <h1 className="text-heading-lg text-on-surface mb-lg">Candidates</h1>
            {isLoading ? (
              <LoadingSpinner size="lg" />
            ) : (
              <CandidateList
                candidates={data?.candidates || []}
                isLoading={isLoading}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CandidatesPage
