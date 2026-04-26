import React from 'react'
import toast, { ToastPosition } from 'react-hot-toast'

export const showToast = (
  message: string,
  type: 'success' | 'error' | 'info' = 'info',
  position: ToastPosition = 'top-right'
) => {
  switch (type) {
    case 'success':
      toast.success(message, { position })
      break
    case 'error':
      toast.error(message, { position })
      break
    case 'info':
    default:
      toast(message, { position })
      break
  }
}

export const Toast: React.FC = () => {
  return null
}
