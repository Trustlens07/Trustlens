import React from 'react'

interface BatchScreeningFormProps {
  onSubmit: (data: { jobRole: string; jobDescription: string; fairnessMode: string }) => void
  isLoading?: boolean
}

export const BatchScreeningForm: React.FC<BatchScreeningFormProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    onSubmit({
      jobRole: formData.get('jobRole') as string,
      jobDescription: formData.get('jobDescription') as string,
      fairnessMode: formData.get('fairnessMode') as string,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Job Role</label>
        <input
          type="text"
          name="jobRole"
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="e.g., Software Engineer"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
        <textarea
          name="jobDescription"
          required
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
          placeholder="Describe the job requirements..."
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Fairness Mode</label>
        <select
          name="fairnessMode"
          className="w-full px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="balanced">Balanced</option>
          <option value="strict">Strict</option>
          <option value="lenient">Lenient</option>
        </select>
      </div>
      <button
        type="submit"
        disabled={isLoading}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
      >
        {isLoading ? 'Processing...' : 'Start Screening'}
      </button>
    </form>
  )
}
