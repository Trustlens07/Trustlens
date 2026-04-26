import { useState } from 'react'
import { useScreenResumes, useScreeningResults, useFairnessReport } from '../hooks/useScreening'
import { useCandidates } from '../hooks/useCandidates'
import { FairnessMode } from '../types/screening'
import { Header } from '../components/common/Header'
import { FairnessReport } from '../components/screening/FairnessReport'
import toast from 'react-hot-toast'

export default function ScreeningPage() {
  const [jobRole, setJobRole] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [fairnessMode, setFairnessMode] = useState<FairnessMode>('standard')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [selectedCandidates, setSelectedCandidates] = useState<string[]>([])

  const { data: candidates } = useCandidates({ limit: 100 })
  const screenResumes = useScreenResumes()
  const { data: results, isLoading: resultsLoading } = useScreeningResults(sessionId || '')
  const { data: fairnessReport } = useFairnessReport(sessionId || '')

  const handleScreen = async () => {
    if (!jobRole || !jobDescription || selectedCandidates.length === 0) {
      toast.error('Please fill in all fields and select at least one candidate')
      return
    }

    const selectedCandidateData = candidates?.candidates
      .filter(c => selectedCandidates.includes(c.id))
      .map(c => ({
        candidate_id: c.id,
        name: c.name,
        email: c.email,
        skills: c.skills,
      })) || []

    const result = await screenResumes.mutateAsync({
      job_role: jobRole,
      job_description: jobDescription,
      fairness_mode: fairnessMode,
      resumes: selectedCandidateData,
    })

    setSessionId(result.session_id)
  }

  const handleExportCSV = () => {
    if (!results) return

    const headers = ['Name', 'Email', 'Original Score', 'Enhanced Score', 'Fairness Score', 'Recommended', 'Bias Flags']
    const rows = results.results.map(r => [
      r.name,
      r.email,
      r.original_score.toFixed(2),
      r.enhanced_score.toFixed(2),
      r.fairness_adjusted_score.toFixed(2),
      r.recommended ? 'Yes' : 'No',
      r.bias_flags.join(', '),
    ])

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `screening-results-${sessionId}.csv`
    a.click()
  }

  const handleExportJSON = () => {
    if (!results) return

    const jsonContent = JSON.stringify(results, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `screening-results-${sessionId}.json`
    a.click()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!sessionId ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">Batch Screening</h2>

            <div className="space-y-6">
              <div>
                <label htmlFor="jobRole" className="block text-sm font-medium text-gray-700 mb-1">
                  Job Role
                </label>
                <input
                  id="jobRole"
                  type="text"
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Software Engineer"
                />
              </div>

              <div>
                <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-700 mb-1">
                  Job Description
                </label>
                <textarea
                  id="jobDescription"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  placeholder="Describe the job requirements..."
                />
              </div>

              <div>
                <label htmlFor="fairnessMode" className="block text-sm font-medium text-gray-700 mb-1">
                  Fairness Mode
                </label>
                <select
                  id="fairnessMode"
                  value={fairnessMode}
                  onChange={(e) => setFairnessMode(e.target.value as FairnessMode)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="standard">Standard</option>
                  <option value="aggressive">Aggressive (More Bias Mitigation)</option>
                  <option value="conservative">Conservative (Less Bias Mitigation)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Candidates ({selectedCandidates.length} selected)
                </label>
                <div className="max-h-64 overflow-y-auto border border-gray-300 rounded-lg p-4">
                  {candidates?.candidates.map((candidate) => (
                    <label key={candidate.id} className="flex items-center gap-2 py-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={selectedCandidates.includes(candidate.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedCandidates([...selectedCandidates, candidate.id])
                          } else {
                            setSelectedCandidates(selectedCandidates.filter(id => id !== candidate.id))
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{candidate.name}</span>
                      <span className="text-xs text-gray-500">({candidate.email})</span>
                    </label>
                  ))}
                </div>
              </div>

              <button
                onClick={handleScreen}
                disabled={screenResumes.isPending}
                className="w-full py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {screenResumes.isPending ? 'Screening...' : 'Start Screening'}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Screening Results</h2>
                <div className="flex gap-2">
                  <button
                    onClick={handleExportCSV}
                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={handleExportJSON}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
                  >
                    Export JSON
                  </button>
                  <button
                    onClick={() => setSessionId(null)}
                    className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 text-sm font-medium"
                  >
                    New Screening
                  </button>
                </div>
              </div>

              {resultsLoading ? (
                <div className="text-center py-8 text-gray-500">Loading results...</div>
              ) : results && results.results.length > 0 ? (
                <>
                  {/* Summary */}
                  <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600">Total Candidates</p>
                      <p className="text-2xl font-bold text-gray-900">{results.summary.total_candidates}</p>
                    </div>
                    <div className="bg-green-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600">Recommended</p>
                      <p className="text-2xl font-bold text-green-600">{results.summary.recommended_count}</p>
                    </div>
                    <div className="bg-blue-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600">Avg Original Score</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {results.summary.average_original_score.toFixed(1)}
                      </p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600">Avg Fairness Score</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {results.summary.average_fairness_score.toFixed(1)}
                      </p>
                    </div>
                  </div>

                  {/* Table */}
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50 border-b border-gray-200">
                        <tr>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Name</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Email</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Original</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Enhanced</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Fairness</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Recommended</th>
                          <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Bias Flags</th>
                        </tr>
                      </thead>
                      <tbody>
                        {results.results.map((result) => (
                          <tr key={result.candidate_id} className="border-b border-gray-100 hover:bg-gray-50">
                            <td className="py-3 px-4 text-sm font-medium text-gray-900">{result.name}</td>
                            <td className="py-3 px-4 text-sm text-gray-600">{result.email}</td>
                            <td className="py-3 px-4 text-sm text-gray-900">{result.original_score.toFixed(1)}</td>
                            <td className="py-3 px-4 text-sm text-gray-900">{result.enhanced_score.toFixed(1)}</td>
                            <td className="py-3 px-4 text-sm text-gray-900 font-medium">
                              {result.fairness_adjusted_score.toFixed(1)}
                            </td>
                            <td className="py-3 px-4">
                              <span
                                className={`px-2 py-1 rounded-full text-xs font-medium ${
                                  result.recommended
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-red-100 text-red-800'
                                }`}
                              >
                                {result.recommended ? 'Yes' : 'No'}
                              </span>
                            </td>
                            <td className="py-3 px-4 text-sm text-gray-600">
                              {result.bias_flags.length > 0 ? (
                                <div className="flex flex-wrap gap-1">
                                  {result.bias_flags.map((flag, i) => (
                                    <span key={i} className="px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded text-xs">
                                      {flag}
                                    </span>
                                  ))}
                                </div>
                              ) : (
                                <span className="text-gray-400">None</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-gray-500">No results yet. Screening in progress...</div>
              )}
            </div>

            {/* Fairness Report */}
            {fairnessReport && (
              <FairnessReport report={fairnessReport} />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
