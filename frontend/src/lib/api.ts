const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function api(path: string, options?: RequestInit) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options?.headers },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || err.detail || res.statusText)
  }
  return res.json()
}

export function getUserId(): string {
  if (typeof window === 'undefined') return ''
  let id = localStorage.getItem('stock_god_user_id')
  if (!id) {
    id = 'user_' + Math.random().toString(36).slice(2, 10)
    localStorage.setItem('stock_god_user_id', id)
  }
  return id
}
