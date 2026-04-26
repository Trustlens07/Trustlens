import toast from 'react-hot-toast'

export const handleApiError = (error: any): string => {
  if (error.response) {
    const status = error.response.status
    const data = error.response.data

    switch (status) {
      case 400:
        return data.message || 'Invalid request. Please check your input.'
      case 401:
        return 'Authentication required. Please log in again.'
      case 403:
        return 'You do not have permission to perform this action.'
      case 404:
        return 'The requested resource was not found.'
      case 429:
        return 'Too many requests. Please try again later.'
      case 500:
        return 'Server error. Please try again later.'
      default:
        return data.message || 'An unexpected error occurred.'
    }
  } else if (error.request) {
    return 'Network error. Please check your connection.'
  } else {
    return error.message || 'An unexpected error occurred.'
  }
}

export const showErrorToast = (error: any): void => {
  const message = handleApiError(error)
  toast.error(message)
}

export const showSuccessToast = (message: string): void => {
  toast.success(message)
}

export const showInfoToast = (message: string): void => {
  toast(message)
}

export const logError = (error: any, context?: string): void => {
  console.error(`[Error${context ? ` - ${context}` : ''}]`, error)
}
