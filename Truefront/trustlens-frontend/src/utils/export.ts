/**
 * File export utilities for CSV, JSON, and other formats
 */

export interface ExportOptions {
  filename: string
  format: 'csv' | 'json' | 'pdf'
}

export function exportAsCSV<T extends Record<string, any>>(
  data: T[],
  filename: string,
  headers?: string[]
): void {
  if (data.length === 0) return

  const keys = headers || Object.keys(data[0])
  const csvContent = [
    keys.map(key => `"${key}"`).join(','),
    ...data.map(row =>
      keys
        .map(key => {
          const value = row[key]
          if (value === null || value === undefined) return ''
          if (Array.isArray(value)) return `"${value.join('; ')}"`
          if (typeof value === 'object') return `"${JSON.stringify(value)}"`
          return `"${String(value).replace(/"/g, '""')}"`
        })
        .join(',')
    ),
  ].join('\n')

  downloadFile(csvContent, filename, 'text/csv')
}

export function exportAsJSON<T>(
  data: T,
  filename: string,
  pretty = true
): void {
  const content = JSON.stringify(data, null, pretty ? 2 : undefined)
  downloadFile(content, filename, 'application/json')
}

export function downloadFile(
  content: string | Blob,
  filename: string,
  mimeType: string
): void {
  const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function generateFileName(prefix: string, format: 'csv' | 'json' | 'pdf'): string {
  const timestamp = new Date().toISOString().split('T')[0]
  return `${prefix}-${timestamp}.${format}`
}
