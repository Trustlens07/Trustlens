export const queryKeys = {
  candidates: {
    all: ['candidates'] as const,
    lists: () => [...queryKeys.candidates.all, 'list'] as const,
    list: (filters: any) => [...queryKeys.candidates.lists(), filters] as const,
    details: () => [...queryKeys.candidates.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.candidates.details(), id] as const,
    status: (id: string) => [...queryKeys.candidates.detail(id), 'status'] as const,
  },
  scores: {
    all: ['scores'] as const,
    candidate: (id: string, version: string) =>
      [...queryKeys.scores.all, 'candidate', id, version] as const,
    history: (id: string) =>
      [...queryKeys.scores.all, 'history', id] as const,
  },
  bias: {
    all: ['bias'] as const,
    metrics: (id: string, version: string) => 
      [...queryKeys.bias.all, 'metrics', id, version] as const,
  },
  screening: {
    all: ['screening'] as const,
    results: (sessionId: string) => 
      [...queryKeys.screening.all, 'results', sessionId] as const,
    report: (sessionId: string) => 
      [...queryKeys.screening.all, 'report', sessionId] as const,
  },
  feedback: {
    all: ['feedback'] as const,
    candidate: (id: string) => 
      [...queryKeys.feedback.all, 'candidate', id] as const,
  },
} as const
