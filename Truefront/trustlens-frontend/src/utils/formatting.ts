export const formatScore = (score: number): string => {
  return score.toFixed(1)
}

export const formatPercentage = (value: number): string => {
  return `${(value * 100).toFixed(1)}%`
}

export const formatNumber = (num: number): string => {
  return new Intl.NumberFormat('en-US').format(num)
}

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

export const capitalizeFirst = (text: string): string => {
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase()
}

export const formatSnakeCase = (text: string): string => {
  return text
    .split('_')
    .map((word) => capitalizeFirst(word))
    .join(' ')
}

export const formatCamelCase = (text: string): string => {
  const result = text.replace(/([A-Z])/g, ' $1')
  return capitalizeFirst(result)
}

export const formatSkills = (skills: string[]): string => {
  if (skills.length === 0) return 'None'
  if (skills.length <= 3) return skills.join(', ')
  return `${skills.slice(0, 3).join(', ')} +${skills.length - 3} more`
}

export const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}
