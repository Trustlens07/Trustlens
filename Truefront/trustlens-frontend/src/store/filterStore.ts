import { create } from 'zustand'

interface FilterState {
  status: string | null
  jobRole: string | null
  fairnessMode: string | null
  dateRange: { start: Date | null; end: Date | null }
  searchQuery: string
  setStatus: (status: string | null) => void
  setJobRole: (jobRole: string | null) => void
  setFairnessMode: (mode: string | null) => void
  setDateRange: (range: { start: Date | null; end: Date | null }) => void
  setSearchQuery: (query: string) => void
  resetFilters: () => void
}

export const useFilterStore = create<FilterState>((set) => ({
  status: null,
  jobRole: null,
  fairnessMode: null,
  dateRange: { start: null, end: null },
  searchQuery: '',
  setStatus: (status) => set({ status }),
  setJobRole: (jobRole) => set({ jobRole }),
  setFairnessMode: (mode) => set({ fairnessMode: mode }),
  setDateRange: (range) => set({ dateRange: range }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  resetFilters: () => set({
    status: null,
    jobRole: null,
    fairnessMode: null,
    dateRange: { start: null, end: null },
    searchQuery: '',
  }),
}))
