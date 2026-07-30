import type { HardwareCapabilities, HardwareConnectResult, HardwareSerialPort, HardwareStatus, HardwareTelemetry } from '../types/hardware'

export interface HardwareMotionTestResult {
  accepted: boolean
  message: string
  command: string | null
  command_sent: boolean
  pico_response: string | null
  driver_ack: string | null
  safe_stop_response: string | null
  reason_codes: string[]
}

export interface PicoDiscoveryResult {
  found: boolean
  port: string | null
  baudrate: number
  reason_code: string
  detail: string
}

function apiBaseUrl(): string {
  const configured = import.meta.env.VITE_BACKEND_API_URL as string | undefined
  if (configured) return configured.replace(/\/$/, '')
  if (window.location.port && window.location.port !== '5173') return window.location.origin
  return `${window.location.protocol}//${window.location.hostname}:8000`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBaseUrl()}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
    ...init,
  })
  const body = await response.json()
  if (!response.ok) throw new Error(JSON.stringify(body))
  return body as T
}

export function fetchHardwarePorts(): Promise<HardwareSerialPort[]> {
  return request<HardwareSerialPort[]>('/api/hardware/serial/ports')
}

export function fetchHardwareStatus(): Promise<HardwareStatus> {
  return request<HardwareStatus>('/api/hardware/status')
}

export function fetchHardwareCapabilities(): Promise<HardwareCapabilities> {
  return request<HardwareCapabilities>('/api/hardware/capabilities')
}

export function connectHardwareReadonly(port: string, baudrate: number): Promise<HardwareConnectResult> {
  return request<HardwareConnectResult>('/api/hardware/connect-readonly', {
    method: 'POST',
    body: JSON.stringify({ port, baudrate }),
  })
}

export function disconnectHardware(): Promise<HardwareConnectResult> {
  return request<HardwareConnectResult>('/api/hardware/disconnect', { method: 'POST' })
}

export function fetchHardwareTelemetry(): Promise<HardwareTelemetry> {
  return request<HardwareTelemetry>('/api/hardware/telemetry')
}

export function discoverPico(): Promise<PicoDiscoveryResult> {
  return request<PicoDiscoveryResult>('/api/hardware/discover-pico', { method: 'POST' })
}

export function testHardwareJog(payload: { speed_x: number, speed_y: number, duration_ms: number }): Promise<HardwareMotionTestResult> {
  return request<HardwareMotionTestResult>('/api/hardware/test-jog', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function stopHardwareMotion(): Promise<HardwareMotionTestResult> {
  return request<HardwareMotionTestResult>('/api/hardware/manual-stop', { method: 'POST' })
}

export function testHardwareTrigger(): Promise<HardwareMotionTestResult> {
  return request<HardwareMotionTestResult>('/api/hardware/test-trigger', { method: 'POST' })
}

export function testServoTune(payload: { release_deg: number, fire_deg: number, pulse_s: number }): Promise<HardwareMotionTestResult> {
  return request<HardwareMotionTestResult>('/api/hardware/test-servo-tune', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
