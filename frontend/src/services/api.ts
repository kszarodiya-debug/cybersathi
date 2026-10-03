export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const API_REQUEST_TIMEOUT_MS = 15_000

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function errorMessage(payload: unknown): string {
  if (typeof payload === 'object' && payload !== null && 'detail' in payload) {
    const detail = (payload as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return 'Please check the submitted fields.'
  }
  return 'The request could not be completed.'
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), API_REQUEST_TIMEOUT_MS)
  const abortExternalRequest = () => controller.abort()
  init.signal?.addEventListener('abort', abortExternalRequest, { once: true })

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      credentials: 'omit',
      signal: controller.signal,
    })
  } catch (error) {
    const errorName = error instanceof Error
      ? error.name
      : typeof error === 'object' && error !== null && 'name' in error
        ? String((error as { name: unknown }).name)
        : undefined
    if (errorName === 'AbortError') {
      throw new ApiError(504, 'The service took too long to respond. Please try again.')
    }
    if (error instanceof TypeError || errorName === 'TypeError') {
      throw new ApiError(0, 'The service is unavailable. Please try again.')
    }
    throw error
  } finally {
    clearTimeout(timeoutId)
    init.signal?.removeEventListener('abort', abortExternalRequest)
  }

  const contentType = response.headers.get('content-type') ?? ''
  const payload: unknown = contentType.includes('application/json')
    ? await response.json()
    : undefined

  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(payload))
  }

  return payload as T
}
