import type {
  AuthStatus,
  FetchRequest,
  FetchResponse,
  UploadElement,
  UploadResponse,
} from './types'

// Empty string = relative paths, i.e. same-origin requests through the Caddy
// proxy (the normal Docker setup). Override with VITE_API_BASE for standalone
// frontend dev against a backend on a different origin.
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`${response.status}: ${body}`)
  }
  return response.json()
}

export function fetchElements(req: FetchRequest): Promise<FetchResponse> {
  return request('/api/fetch', { method: 'POST', body: JSON.stringify(req) })
}

export function getAuthStatus(): Promise<AuthStatus> {
  return request('/api/auth/status')
}

export function loginUrl(): string {
  return `${API_BASE}/api/auth/login`
}

export async function logout(): Promise<void> {
  await request('/api/auth/logout', { method: 'POST' })
}

export function uploadChanges(
  comment: string,
  elements: UploadElement[],
): Promise<UploadResponse> {
  return request('/api/upload', { method: 'POST', body: JSON.stringify({ comment, elements }) })
}
