export interface ApiResponse<T> {
  data: T
  message?: string
  error?: string
}

export interface ApiError {
  detail: string
  status: number
}

export interface PaginatedParams {
  skip?: number
  limit?: number
}

export interface FilterParams extends PaginatedParams {
  status?: string
  search?: string
}
