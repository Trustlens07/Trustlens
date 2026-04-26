import React from 'react'
import { getStatusColor, getStatusBgColor } from '../../utils/designSystem'

// Example component showing how to use design system tokens
export const DesignSystemExample: React.FC = () => {
  const statusExamples = ['success', 'warning', 'error'] as const

  return (
    <div className="card">
      <div className="card-header">
        <h3 className="text-heading-md text-on-surface">Design System Example</h3>
      </div>

      <div className="space-y-lg">
        {/* Typography Examples */}
        <div>
          <h4 className="text-heading-sm text-on-surface mb-md">Typography</h4>
          <div className="space-y-sm">
            <p className="text-metric-xl">Metric XL - Large numbers and scores</p>
            <p className="text-metric-lg">Metric LG - Secondary metrics</p>
            <p className="text-heading-lg">Heading LG - Main section headers</p>
            <p className="text-heading-md">Heading MD - Card headers</p>
            <p className="text-heading-sm">Heading SM - Subsection headers</p>
            <p className="text-body">Body - Regular content text</p>
            <p className="text-label">Label - Form labels and small text</p>
          </div>
        </div>

        {/* Color Examples */}
        <div>
          <h4 className="text-heading-sm text-on-surface mb-md">Status Colors</h4>
          <div className="flex gap-md">
            {statusExamples.map((status) => (
              <div
                key={status}
                className="chip"
                style={{
                  backgroundColor: getStatusBgColor(status),
                  color: getStatusColor(status),
                  borderColor: `${getStatusColor(status)}20`
                }}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </div>
            ))}
          </div>
        </div>

        {/* Button Examples */}
        <div>
          <h4 className="text-heading-sm text-on-surface mb-md">Buttons</h4>
          <div className="flex gap-md">
            <button className="btn-primary">Primary Button</button>
            <button className="btn-secondary">Secondary Button</button>
            <button className="btn-outline">Outline Button</button>
          </div>
        </div>

        {/* Form Elements */}
        <div>
          <h4 className="text-heading-sm text-on-surface mb-md">Form Elements</h4>
          <div className="space-y-md">
            <div>
              <label className="label">Email Address</label>
              <input
                type="email"
                className="input w-full"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="label">Message</label>
              <textarea
                className="input w-full"
                rows={3}
                placeholder="Enter your message..."
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}