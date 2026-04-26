import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { lazy, Suspense } from 'react'
import { LoadingSpinner } from './components/common/LoadingSpinner'
import { PrivateRoute } from './components/common/PrivateRoute'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Login = lazy(() => import('./pages/Login'))
const UploadPage = lazy(() => import('./pages/UploadPage'))
const CandidateDetailPage = lazy(() => import('./pages/CandidateDetailPage'))
const BiasAnalysisPage = lazy(() => import('./pages/BiasAnalysisPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const CandidatesPage = lazy(() => import('./pages/CandidatesPage'))
const SettingsPage = lazy(() => import('./pages/SettingsPage'))

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Suspense fallback={<LoadingSpinner size="lg" />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/upload" element={<PrivateRoute><UploadPage /></PrivateRoute>} />
            <Route path="/candidate/:id" element={<PrivateRoute><CandidateDetailPage /></PrivateRoute>} />
            <Route path="/screening" element={<Navigate to="/upload" replace />} />
            <Route path="/bias-analysis" element={<PrivateRoute><BiasAnalysisPage /></PrivateRoute>} />
            <Route path="/reports" element={<PrivateRoute><ReportsPage /></PrivateRoute>} />
            <Route path="/candidates" element={<PrivateRoute><CandidatesPage /></PrivateRoute>} />
            <Route path="/settings" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
          </Routes>
        </Suspense>
      </Router>
      <Toaster position="top-right" />
    </QueryClientProvider>
  )
}

export default App
