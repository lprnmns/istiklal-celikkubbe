import { computed, ref } from 'vue'
import { fetchCommandProfile, type GatewayPreflightResult } from '../api/safety'
import { useDeviceRuntimeStore } from '../stores/deviceRuntimeStore'
import { useMotionStore } from '../stores/motionStore'
import { useSystemStore } from '../stores/systemStore'

export type ReadinessState = 'READY' | 'BLOCKED' | 'DEGRADED' | 'UNKNOWN'
export type ReadinessAction = 'refresh' | 'setup-camera' | 'setup-pico' | 'setup-preflight'

export interface OperationalReadinessItem {
  key: 'backend' | 'camera' | 'pico_estop' | 'motion_actuator'
  title: string
  state: ReadinessState
  message: string
  reasonCode: string | null
  action: ReadinessAction
  requiredFor: 'DRY_RUN' | 'LIVE_MOTION' | 'LIVE_FIRE'
}

function gate(preflight: GatewayPreflightResult | null, code: string) {
  return preflight?.gates.find((item) => item.code === code)
}

/**
 * Read-only view model composed from authoritative runtime and CommandGateway
 * APIs. It deliberately never infers that a fixture/mock device is live.
 */
export function useOperationalReadiness() {
  const system = useSystemStore()
  const runtime = useDeviceRuntimeStore()
  const motion = useMotionStore()
  const preflight = ref<GatewayPreflightResult | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const observedAt = ref<number>(0)
  const selectedCamera = computed(() => runtime.inventory.cameras.find((item) => item.device_id === runtime.cameraStatus.selected_device)
    ?? runtime.inventory.cameras.find((item) => item.device_path === runtime.cameraStatus.profile.device_path)
    ?? null)
  const cameraLabel = computed(() => selectedCamera.value?.name
    || selectedCamera.value?.description
    || runtime.cameraStatus.selected_camera
    || 'kamera seçilmedi')

  async function refresh(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await Promise.all([runtime.refresh(), motion.refresh(), fetchCommandProfile().then((value) => { preflight.value = value })])
      observedAt.value = Date.now()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'Readiness bilgisi alınamadı.'
    } finally {
      loading.value = false
    }
  }

  const items = computed<OperationalReadinessItem[]>(() => {
    const backendReady = system.connectionStatus === 'connected'
    const cameraGate = gate(preflight.value, 'CAMERA_FRESH')
    const cameraReal = runtime.cameraStatus.is_real_camera_evidence && runtime.cameraStatus.running
    const cameraFresh = runtime.cameraStatus.last_frame_age_ms !== null && runtime.cameraStatus.last_frame_age_ms < 1200
    const picoGate = gate(preflight.value, 'PICO_HANDSHAKE_OK')
    const estopGate = gate(preflight.value, 'ESTOP_RELEASED')
    const motionGate = gate(preflight.value, 'MOTION_LIMITS_OK')
    const armGate = gate(preflight.value, 'ACTUATOR_ARMED')

    return [
      {
        key: 'backend', title: 'Merkez sistem', requiredFor: 'DRY_RUN', action: 'refresh',
        state: backendReady ? 'READY' : 'BLOCKED',
        message: backendReady ? 'Canlı durum bağlantısı açık.' : 'Merkez sistem bağlantısı kurulamadı.',
        reasonCode: backendReady ? null : 'BACKEND_DISCONNECTED',
      },
      {
        key: 'camera', title: 'Kamera', requiredFor: 'LIVE_FIRE', action: 'setup-camera',
        state: cameraGate?.ready || (cameraReal && cameraFresh) ? 'READY' : runtime.inventory.cameras.length ? 'DEGRADED' : 'BLOCKED',
        message: cameraGate?.ready || (cameraReal && cameraFresh)
          ? `Canlı görüntü: ${cameraLabel.value}.`
          : runtime.inventory.cameras.length ? `Seçili kamera: ${cameraLabel.value}; canlı frame/uygulama bekleniyor.` : 'Kamera bulunamadı.',
        reasonCode: cameraGate?.ready || (cameraReal && cameraFresh) ? null : cameraGate?.code ?? (runtime.inventory.cameras.length ? 'CAMERA_STALE' : 'CAMERA_NOT_FOUND'),
      },
      {
        key: 'pico_estop', title: 'Pico + Acil durdurma', requiredFor: 'LIVE_MOTION', action: 'setup-pico',
        state: picoGate?.ready && estopGate?.ready ? 'READY' : preflight.value ? 'BLOCKED' : 'UNKNOWN',
        message: picoGate?.ready && estopGate?.ready ? 'Pico bağlı, acil durdurma bırakılmış.' : estopGate?.code === 'ESTOP_ACTIVE' ? 'Acil durdurma aktif.' : 'Pico bağlantı doğrulaması bekleniyor.',
        reasonCode: estopGate?.code === 'ESTOP_ACTIVE' ? 'ESTOP_ACTIVE' : picoGate?.code ?? estopGate?.code ?? 'PICO_HANDSHAKE_FAILED',
      },
      {
        key: 'motion_actuator', title: 'Hareket + Tetik', requiredFor: 'LIVE_FIRE', action: 'setup-preflight',
        state: motionGate?.ready && armGate?.ready ? 'READY' : preflight.value?.profile === 'DRY_RUN' ? 'DEGRADED' : 'BLOCKED',
        message: motionGate?.ready && armGate?.ready ? 'Hareket sınırları uygun, tetik hazır.' : preflight.value?.profile === 'DRY_RUN' ? 'Test veya Canlı Sistem henüz hazırlanmadı.' : 'Hareket veya tetik ön kontrolü bekleniyor.',
        reasonCode: motionGate?.ready && armGate?.ready ? null : preflight.value?.profile === 'DRY_RUN' ? 'START_MODE_NOT_SELECTED' : motionGate?.code ?? armGate?.code ?? 'ACTUATOR_NOT_ARMED',
      },
    ]
  })

  const liveReady = computed(() => Boolean(preflight.value?.ready && preflight.value.physical_motion_enabled && preflight.value.physical_fire_enabled))
  const primaryBlocker = computed(() => items.value.find((item) => item.state === 'BLOCKED') ?? items.value.find((item) => item.state === 'DEGRADED') ?? null)

  return { preflight, loading, error, observedAt, items, liveReady, primaryBlocker, refresh }
}
