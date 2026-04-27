import { CandidateStatus } from '../../types/candidate'
import { cn } from '../../utils/cn'

interface CandidateStatusBadgeProps {
  status: CandidateStatus
  className?: string
}

export function CandidateStatusBadge({ status, className }: CandidateStatusBadgeProps) {
  const statusConfig = {
    pending: {
      label: 'Pending',
      bgColor: 'bg-surface-container',
      textColor: 'text-on-surface-variant',
      borderColor: 'border-outline-variant',
      dotColor: 'bg-on-surface-variant',
    },
    processing: {
      label: 'Processing',
      bgColor: 'bg-primary-fixed',
      textColor: 'text-primary',
      borderColor: 'border-primary',
      dotColor: 'bg-primary',
    },
    completed: {
      label: 'Completed',
      bgColor: 'bg-secondary-fixed',
      textColor: 'text-secondary',
      borderColor: 'border-secondary',
      dotColor: 'bg-secondary',
    },
    error: {
      label: 'Error',
      bgColor: 'bg-error/10',
      textColor: 'text-error',
      borderColor: 'border-error',
      dotColor: 'bg-error',
    },
  }

  const config = statusConfig[status] || {
    label: status || 'Unknown',
    bgColor: 'bg-gray-100',
    textColor: 'text-gray-600',
    borderColor: 'border-gray-300',
    dotColor: 'bg-gray-400',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-xs px-sm py-xs rounded-full text-label font-medium border',
        config.bgColor,
        config.textColor,
        config.borderColor,
        className
      )}
    >
      <span className={cn('h-2 w-2 rounded-full', config.dotColor)} />
      {config.label}
    </span>
  )
}
