export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export const validatePhone = (phone: string): boolean => {
  const phoneRegex = /^\+?[\d\s-()]+$/
  return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10
}

export const validateUrl = (url: string): boolean => {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export const validateFile = (file: File, maxSizeMB: number = 10, allowedTypes: string[] = ['application/pdf']): { valid: boolean; error?: string } => {
  if (!file) {
    return { valid: false, error: 'No file provided' }
  }

  if (!allowedTypes.includes(file.type)) {
    return { valid: false, error: `File type must be ${allowedTypes.join(', ')}` }
  }

  const maxSizeBytes = maxSizeMB * 1024 * 1024
  if (file.size > maxSizeBytes) {
    return { valid: false, error: `File size must be less than ${maxSizeMB}MB` }
  }

  return { valid: true }
}

export const validateSkills = (skills: string[]): { valid: boolean; error?: string } => {
  if (!Array.isArray(skills)) {
    return { valid: false, error: 'Skills must be an array' }
  }

  if (skills.length === 0) {
    return { valid: false, error: 'At least one skill is required' }
  }

  if (skills.some((skill) => skill.trim().length === 0)) {
    return { valid: false, error: 'Skills cannot be empty' }
  }

  return { valid: true }
}

export const validateJobRole = (jobRole: string): { valid: boolean; error?: string } => {
  if (!jobRole || jobRole.trim().length === 0) {
    return { valid: false, error: 'Job role is required' }
  }

  if (jobRole.length < 3) {
    return { valid: false, error: 'Job role must be at least 3 characters' }
  }

  return { valid: true }
}

export const validateJobDescription = (description: string): { valid: boolean; error?: string } => {
  if (!description || description.trim().length === 0) {
    return { valid: false, error: 'Job description is required' }
  }

  if (description.length < 50) {
    return { valid: false, error: 'Job description must be at least 50 characters' }
  }

  return { valid: true }
}

export const validateRating = (rating: number): { valid: boolean; error?: string } => {
  if (rating < 1 || rating > 5) {
    return { valid: false, error: 'Rating must be between 1 and 5' }
  }

  if (!Number.isInteger(rating)) {
    return { valid: false, error: 'Rating must be a whole number' }
  }

  return { valid: true }
}
