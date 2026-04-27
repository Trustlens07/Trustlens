import { ScoreBreakdown } from '../../types/score'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend,
  Cell,
} from 'recharts'

interface ScoreChartProps {
  breakdown: ScoreBreakdown
  type?: 'bar' | 'radar'
  comparison?: ScoreBreakdown
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

export function ScoreChart({ breakdown, type = 'bar', comparison }: ScoreChartProps) {
  // Add null checks for breakdown properties
  const skills = breakdown?.skills || []
  const skillsAvg = skills.length > 0 ? skills.reduce((acc, s) => acc + (s?.score || 0), 0) / skills.length : 0
  
  const barData = [
    { name: 'Skills', score: skillsAvg, fullMark: 100 },
    { name: 'Experience', score: breakdown?.experience || 0, fullMark: 100 },
    { name: 'Education', score: breakdown?.education || 0, fullMark: 100 },
    { name: 'Projects', score: breakdown?.projects || 0, fullMark: 100 },
    { name: 'Soft Skills', score: breakdown?.soft_skills || 0, fullMark: 100 },
  ]

  const radarData: any[] = [
    { subject: 'Skills', A: skillsAvg, fullMark: 100 },
    { subject: 'Experience', A: breakdown?.experience || 0, fullMark: 100 },
    { subject: 'Education', A: breakdown?.education || 0, fullMark: 100 },
    { subject: 'Projects', A: breakdown?.projects || 0, fullMark: 100 },
    { subject: 'Soft Skills', A: breakdown?.soft_skills || 0, fullMark: 100 },
  ]

  if (comparison) {
    const compSkills = comparison?.skills || []
    const compSkillsAvg = compSkills.length > 0 ? compSkills.reduce((acc, s) => acc + (s?.score || 0), 0) / compSkills.length : 0
    
    const compData = [
      compSkillsAvg,
      comparison?.experience || 0,
      comparison?.education || 0,
      comparison?.projects || 0,
      comparison?.soft_skills || 0,
    ]
    radarData.forEach((item, index) => {
      item.B = compData[index]
    })
    barData.forEach((item, index) => {
      (item as any).enhanced = compData[index]
    })
  }

  if (type === 'radar') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="80%">
          <PolarGrid strokeDasharray="3 3" />
          <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
          <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
          <Radar name="Original" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} strokeWidth={2} />
          {comparison && (
            <Radar name="Enhanced" dataKey="B" stroke="#10b981" fill="#10b981" fillOpacity={0.3} strokeWidth={2} />
          )}
          <Legend />
          <Tooltip />
        </RadarChart>
      </ResponsiveContainer>
    )
  }

  // Comparison bar chart
  if (comparison) {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={barData} barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="name" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
            formatter={(value: any) => [value ? Number(value).toFixed(1) : '0', '']}
          />
          <Bar dataKey="score" name="Original" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={24} />
          <Bar dataKey="enhanced" name="Enhanced" fill="#10b981" radius={[4, 4, 0, 0]} barSize={24} />
          <Legend />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={barData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
        <Tooltip
          contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
          formatter={(value: any) => [value ? Number(value).toFixed(1) : '0', 'Score']}
        />
        <Bar dataKey="score" radius={[4, 4, 0, 0]} barSize={32}>
          {barData.map((_, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
