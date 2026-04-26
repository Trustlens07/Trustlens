// import { useState } from 'react'
import { useCandidates } from '../hooks/useCandidates'
import { Header } from '../components/common/Header'
import { LoadingSpinner } from '../components/common/LoadingSpinner'
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from 'recharts'

const STATUS_COLORS: Record<string, string> = {
  completed: '#10b981',
  processing: '#3b82f6',
  pending: '#6b7280',
  error: '#ef4444',
}

export default function ReportsPage() {
  const { data: candidates, isLoading } = useCandidates({ limit: 100 })

  const candidateList = candidates?.candidates || []

  // Status distribution
  const statusCounts = candidateList.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const statusPieData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
  }))

  // Skills frequency
  const skillCounts = candidateList.reduce((acc, c) => {
    c.skills.forEach(skill => {
      acc[skill] = (acc[skill] || 0) + 1
    })
    return acc
  }, {} as Record<string, number>)

  const topSkills = Object.entries(skillCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([skill, count]) => ({ name: skill, count }))

  // Role distribution
  const roleCounts = candidateList.reduce((acc, c) => {
    acc[c.job_role] = (acc[c.job_role] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const roleData = Object.entries(roleCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([role, count]) => ({
      name: role.length > 15 ? role.slice(0, 15) + '...' : role,
      count,
    }))

  const handleExportCandidatesCSV = () => {
    const headers = ['Name', 'Email', 'Job Role', 'Status', 'Skills', 'Created At']
    const rows = candidateList.map(c => [
      c.name,
      c.email,
      c.job_role,
      c.status,
      c.skills.join('; '),
      new Date(c.created_at).toLocaleDateString(),
    ])
    const csvContent = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n')
    downloadFile(csvContent, 'candidates-report.csv', 'text/csv')
  }

  const handleExportCandidatesJSON = () => {
    const jsonContent = JSON.stringify(candidateList, null, 2)
    downloadFile(jsonContent, 'candidates-report.json', 'application/json')
  }

  const handleExportSummaryJSON = () => {
    const summary = {
      total_candidates: candidates?.total || 0,
      status_distribution: statusCounts,
      top_skills: Object.fromEntries(topSkills.map(s => [s.name, s.count])),
      role_distribution: Object.fromEntries(roleData.map(r => [r.name, r.count])),
      generated_at: new Date().toISOString(),
    }
    const jsonContent = JSON.stringify(summary, null, 2)
    downloadFile(jsonContent, 'summary-report.json', 'application/json')
  }

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Reports</h2>
            <p className="text-gray-600">Generate and export reports from your candidate data.</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExportCandidatesCSV}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm font-medium"
            >
              Export CSV
            </button>
            <button
              onClick={handleExportCandidatesJSON}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              Export JSON
            </button>
            <button
              onClick={handleExportSummaryJSON}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm font-medium"
            >
              Export Summary
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : candidateList.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            <p className="text-gray-500">No candidates available to generate reports.</p>
          </div>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-600">Total Candidates</p>
                <p className="text-2xl font-bold text-gray-900">{candidates?.total || 0}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-2xl font-bold text-green-600">{statusCounts.completed || 0}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-600">Unique Skills</p>
                <p className="text-2xl font-bold text-blue-600">{Object.keys(skillCounts).length}</p>
              </div>
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <p className="text-sm text-gray-600">Job Roles</p>
                <p className="text-2xl font-bold text-purple-600">{Object.keys(roleCounts).length}</p>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
              {/* Status Distribution */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Status Distribution</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={statusPieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                      labelLine={{ stroke: '#9ca3af' }}
                    >
                      {statusPieData.map((entry, index) => (
                        <Cell key={index} fill={STATUS_COLORS[entry.name.toLowerCase()] || '#6b7280'} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Candidates by Role */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Candidates by Role</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={roleData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8b5cf6" radius={[4, 4, 0, 0]} barSize={24} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top Skills */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Skills</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={topSkills} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis type="number" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Candidate Table */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Candidate Details</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Name</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Email</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Job Role</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Skills</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {candidateList.map((candidate) => (
                      <tr key={candidate.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4 text-sm font-medium text-gray-900">{candidate.name}</td>
                        <td className="py-3 px-4 text-sm text-gray-600">{candidate.email}</td>
                        <td className="py-3 px-4 text-sm text-gray-600">{candidate.job_role}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              candidate.status === 'completed'
                                ? 'bg-green-100 text-green-800'
                                : candidate.status === 'processing'
                                ? 'bg-blue-100 text-blue-800'
                                : candidate.status === 'error'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {candidate.status}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {candidate.skills.slice(0, 3).join(', ')}
                          {candidate.skills.length > 3 && ` +${candidate.skills.length - 3}`}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-500">
                          {new Date(candidate.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
