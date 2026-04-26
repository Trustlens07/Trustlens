import React, { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { validateFile } from '../../utils/validation'

interface ResumeUploaderProps {
  onFileSelect: (file: File) => void
  maxSizeMB?: number
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({
  onFileSelect,
  maxSizeMB = 10,
}) => {
  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const file = acceptedFiles[0]
        const validation = validateFile(file, maxSizeMB, ['application/pdf'])
        if (validation.valid) {
          onFileSelect(file)
        } else {
          alert(validation.error)
        }
      }
    },
    [onFileSelect, maxSizeMB]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    maxSize: maxSizeMB * 1024 * 1024,
  })

  return (
    <div
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
        isDragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 hover:border-gray-400'
      }`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center space-y-2">
        <svg
          className="w-12 h-12 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>
        <p className="text-sm text-gray-600">
          {isDragActive
            ? 'Drop the PDF file here'
            : 'Drag & drop a PDF file, or click to select'}
        </p>
        <p className="text-xs text-gray-400">Max file size: {maxSizeMB}MB</p>
      </div>
    </div>
  )
}
