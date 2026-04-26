import { useState } from 'react'
import { useSubmitFeedback } from '../../hooks/useFeedback'
import { Star } from 'lucide-react'
import { cn } from '../../utils/cn'

interface FeedbackFormProps {
  candidateId: string
  onSubmit?: () => void
}

export function FeedbackForm({ candidateId, onSubmit }: FeedbackFormProps) {
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [comment, setComment] = useState('')
  const submitFeedback = useSubmitFeedback()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (rating === 0) {
      return
    }

    await submitFeedback.mutateAsync({
      candidate_id: candidateId,
      rating,
      comment,
    })

    setRating(0)
    setComment('')
    onSubmit?.()
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Submit Feedback</h3>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Rating</label>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              onMouseEnter={() => setHoveredRating(star)}
              onMouseLeave={() => setHoveredRating(0)}
              className="p-1"
            >
              <Star
                className={cn(
                  'h-6 w-6 transition-colors',
                  (hoveredRating || rating) >= star
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-gray-300'
                )}
              />
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4">
        <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-2">
          Comment
        </label>
        <textarea
          id="comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
          placeholder="Share your feedback about this candidate..."
        />
      </div>

      <button
        type="submit"
        disabled={rating === 0 || submitFeedback.isPending}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {submitFeedback.isPending ? 'Submitting...' : 'Submit Feedback'}
      </button>
    </form>
  )
}
