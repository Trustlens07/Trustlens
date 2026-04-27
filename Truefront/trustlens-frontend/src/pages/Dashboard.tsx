import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCandidates, useDeleteCandidate } from '../hooks/useCandidates'
import { CandidateStatusBadge } from '../components/common/CandidateStatusBadge'
import { Skeleton } from '../components/common/Skeleton'
import { Header } from '../components/common/Header'
import { Sidebar } from '../components/common/Sidebar'
import { EmptyState } from '../components/common/EmptyState'
import { useDebounce } from '../utils/debounce'
import { FilterParams } from '../types/api'
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
} from 'recharts'

const STATUS_COLORS: Record<string, string> = {
  completed: '#004ac6',
  processing: '#2563eb',
  pending: '#505f76',
  error: '#ba1a1a',
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchInput, setSearchInput] = useState('')
  const debouncedSearch = useDebounce(searchInput, 300)
  const deleteCandidate = useDeleteCandidate()

  const params: FilterParams = {
    status: statusFilter || undefined,
    search: debouncedSearch || undefined,
    skip: 0,
    limit: 50,
  }

  const { data, isLoading, error } = useCandidates(params)

  const filteredCandidates = data?.candidates || []

  // Status distribution for pie chart
  const statusCounts = filteredCandidates.reduce((acc, c) => {
    acc[c.status] = (acc[c.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const statusPieData = Object.entries(statusCounts).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
  }))

  // Job role distribution for bar chart
  const roleCounts = filteredCandidates.reduce((acc, c) => {
    acc[c.job_role] = (acc[c.job_role] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const roleBarData = Object.entries(roleCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([role, count]) => ({
      name: role.length > 15 ? role.slice(0, 15) + '...' : role,
      count,
    }))

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this candidate?')) {
      await deleteCandidate.mutateAsync(id)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />

      {/* Main Layout */}
      <div className="flex">
        <Sidebar />
        <main className="main-content">
          <div className="container-fluid py-lg">
            {/* Dashboard Header */}
            <div className="flex items-center justify-between mb-lg">
              <div>
                <h2 className="text-heading-xl text-on-surface mb-xs">Candidate Dashboard</h2>
                <p className="text-body text-on-surface-variant">Manage and view your candidate pool</p>
              </div>
              <button
                onClick={() => navigate('/reports')}
                className="btn btn-primary"
              >
                View Reports
              </button>
            </div>

            {/* Filters */}
            <div className="card mb-lg">
              <div className="flex flex-col sm:flex-row gap-md">
                <div className="flex-1">
                  <input
                    type="text"
                    placeholder="Search candidates..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    className="input w-full"
                  />
                </div>
                <div className="sm:w-48">
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="input w-full"
                  >
                    <option value="">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="completed">Completed</option>
                    <option value="error">Error</option>
                  </select>
                </div>
                <button
                  onClick={() => navigate('/upload')}
                  className="btn-primary whitespace-nowrap"
                >
                  Upload Candidate
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-md mb-lg">
              <div className="card">
                <p className="text-label text-on-surface-variant uppercase tracking-wide">Total Candidates</p>
                <p className="text-metric-lg text-primary font-bold mt-sm">{data?.total || 0}</p>
              </div>
              <div className="card">
                <p className="text-label text-on-surface-variant uppercase tracking-wide">Completed</p>
                <p className="text-metric-lg text-primary font-bold mt-sm">
                  {filteredCandidates.filter(c => c.status === 'completed').length}
                </p>
              </div>
              <div className="card">
                <p className="text-label text-on-surface-variant uppercase tracking-wide">Processing</p>
                <p className="text-metric-lg text-primary font-bold mt-sm">
                  {filteredCandidates.filter(c => c.status === 'processing').length}
                </p>
              </div>
              <div className="card">
                <p className="text-label text-on-surface-variant uppercase tracking-wide">Pending</p>
                <p className="text-metric-lg text-primary font-bold mt-sm">
                  {filteredCandidates.filter(c => c.status === 'pending').length}
                </p>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-lg mb-lg">
              {/* Status Distribution */}
              <div className="card">
                <h3 className="text-heading-md text-on-surface mb-md">Status Distribution</h3>
                {statusPieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={statusPieData}
                        cx="50%"
                        cy="50%"
                        outerRadius={70}
                        dataKey="value"
                        label={({ name, percent = 0 }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        labelLine={{ stroke: '#c3c6d7' }}
                      >
                        {statusPieData.map((entry, index) => (
                          <Cell
                            key={index}
                            fill={STATUS_COLORS[entry.name.toLowerCase()] || '#505f76'}
                          />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-on-surface-variant text-center py-xl text-body">No data available</p>
                )}
              </div>

              {/* Job Role Distribution */}
              <div className="card">
                <h3 className="text-heading-md text-on-surface mb-md">Candidates by Role</h3>
                {roleBarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={roleBarData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e1e2ed" />
                      <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#434655' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#434655' }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="#004ac6" radius={[4, 4, 0, 0]} barSize={24} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <p className="text-on-surface-variant text-center py-xl text-body">No data available</p>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-md mb-lg">
              <button
                onClick={() => navigate('/upload')}
                className="card hover:shadow-mid transition-all cursor-pointer hover:bg-primary-fixed"
              >
                <p className="text-heading-sm text-primary font-semibold">Upload Resumes</p>
                <p className="text-body text-on-surface-variant text-sm mt-sm">Add new candidates to the pipeline</p>
              </button>
              <button
                onClick={() => navigate('/upload')}
                className="card hover:shadow-mid transition-all cursor-pointer hover:bg-secondary-fixed"
              >
                <p className="text-heading-sm text-secondary font-semibold">Upload & Screen</p>
                <p className="text-body text-on-surface-variant text-sm mt-sm">Manage resume upload and screening in one place</p>
              </button>
              <button
                onClick={() => navigate('/bias-analysis')}
                className="card hover:shadow-mid transition-all cursor-pointer hover:bg-tertiary-fixed"
              >
                <p className="text-heading-sm text-tertiary font-semibold">Analyze Bias</p>
                <p className="text-body text-on-surface-variant text-sm mt-sm">Review demographic disparities</p>
              </button>
            </div>

            {/* Candidates Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          {isLoading ? (
            <div className="p-8 space-y-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : error ? (
            <EmptyState
              title="Failed to Load Candidates"
              description="We encountered an error while loading candidates. Please try again."
              action={{
                label: 'Retry',
                onClick: () => window.location.reload(),
              }}
            />
          ) : filteredCandidates.length === 0 ? (
            <EmptyState
              title="No Candidates Yet"
              description="Upload your first resume to get started with the fair hiring process."
              action={{
                label: 'Upload Candidate',
                onClick: () => navigate('/upload'),
              }}
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Name</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Email</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Job Role</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Skills</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((candidate) => (
                    <tr key={candidate.id} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-3 px-4 text-sm font-medium text-gray-900">
                        {candidate.name}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-600">{candidate.email}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">{candidate.job_role}</td>
                      <td className="py-3 px-4 text-sm text-gray-600">
                        <div className="flex flex-wrap gap-1">
                          {candidate.skills && Array.isArray(candidate.skills) ? (
                            <>
                              {candidate.skills.slice(0, 3).map((skill, i) => (
                                <span
                                  key={i}
                                  className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded text-xs"
                                >
                                  {skill}
                                </span>
                              ))}
                              {candidate.skills.length > 3 && (
                                <span className="text-xs text-gray-500">
                                  +{candidate.skills.length - 3}
                                </span>
                              )}
                            </>
                          ) : (
                            <span className="text-xs text-gray-400">No skills</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <CandidateStatusBadge status={candidate.status} />
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => navigate(`/candidate/${candidate.id}`)}
                            className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleDelete(candidate.id)}
                            className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          </div>
          </div>
        </main>
      </div>
    </div>
  )
}
