import type { ArmDisarmResult, DecisionState, FireEvaluationResult } from '../types/decision'

function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_BACKEND_API_URL as string | undefined
  if (configured) return configured.replace(/\/$/, '')
  if (window.location.port && window.location.port !== '5173') return window.location.origin
  return `${window.location.protocol}//${window.location.hostname}:8000`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  const body = await response.json()
  if (!response.ok && response.status !== 403) throw new Error(JSON.stringify(body))
  return body as T
}

export function fetchDecisionState(): Promise<DecisionState> {
  return request<DecisionState>('/api/decision/state')
}

export function armSafety(): Promise<ArmDisarmResult> {
  return request<ArmDisarmResult>('/api/safety/arm', { method: 'POST' })
}

export function disarmSafety(): Promise<ArmDisarmResult> {
  return request<ArmDisarmResult>('/api/safety/disarm', { method: 'POST' })
}

export function evaluateFireRequest(operatorConfirmed: boolean): Promise<FireEvaluationResult> {
  return request<FireEvaluationResult>('/api/safety/fire-request', {
    method: 'POST',
    body: JSON.stringify({ operator_confirmed: operatorConfirmed }),
  })
}
