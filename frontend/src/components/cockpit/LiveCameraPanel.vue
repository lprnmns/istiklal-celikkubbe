<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Maximize2, Settings2 } from '@lucide/vue'
import StatusBadge from '../shared/StatusBadge.vue'
import type { TruthTone } from '../../composables/useRuntimeTruth'
import type { VisionEvent } from '../../types/vision'
import { processBrowserVisionFrame } from '../../api/vision'

const props = defineProps<{
  streamUrl: string
  frameUrl: string
  latestFrame: VisionEvent | null
  width: number
  height: number
  aimX: number
  aimY: number
  sourceLabel: string
  truthMode: string
  truthDetail: string
  sourceTone: TruthTone
  sourceDetail: string
  selectedDevice: string
  backend: string
  frameAgeMs: number | null
  realFrameEvidence: boolean
  ktrDemoMode: boolean
  noPhysicalLabel: string
  selectedTargetId: number | null
  personSafetyAvailable: boolean
  personSafetyActive: boolean
  perceptionEnabled: boolean
  detectionRuntimeReady?: boolean
  detectionRuntimeDetail?: string
  perceptionStatusLabel?: string
  perceptionStatusTone?: TruthTone
  targetLabelPrefix?: string
  operatorMode?: boolean
  showLocalControls?: boolean
  imageSettings?: {
    brightness: number
    contrast: number
    saturation: number
    exposure: number
    exposureAuto: boolean
  }
}>()

const emit = defineEmits<{
  selectTarget: [target: { id: number, center_x: number, center_y: number }]
  togglePerception: []
  browserVisionEvent: [event: VisionEvent, size: { width: number; height: number }]
  openSetup: []
  fullscreen: []
}>()

const localVideoRef = ref<HTMLVideoElement | null>(null)
const captureCanvasRef = ref<HTMLCanvasElement | null>(null)
const browserCameraDevices = ref<Array<{ deviceId: string, label: string }>>([])
const selectedBrowserDeviceId = ref('')
const browserCameraStream = ref<MediaStream | null>(null)
const browserCameraError = ref<string | null>(null)
const browserCameraStatus = ref('Browser camera not started')
const backendFrameObjectUrl = ref<string | null>(null)
const backendFrameError = ref<string | null>(null)
let browserInferenceTimer: ReturnType<typeof window.setInterval> | null = null
let backendFrameTimer: ReturnType<typeof window.setTimeout> | null = null
let backendFrameRequest: AbortController | null = null
let browserInferenceBusy = false

const viewBox = computed(() => `0 0 ${Math.max(props.width, 1)} ${Math.max(props.height, 1)}`)
const centerX = computed(() => props.width / 2)
const centerY = computed(() => props.height / 2)
const detections = computed(() => props.perceptionEnabled || props.ktrDemoMode ? props.latestFrame?.balloon_detections ?? [] : [])
const detectionFrameWidth = computed(() => Math.max(1, props.latestFrame?.frame_width ?? props.width))
const detectionFrameHeight = computed(() => Math.max(1, props.latestFrame?.frame_height ?? props.height))
const detectionScaleX = computed(() => props.width / detectionFrameWidth.value)
const detectionScaleY = computed(() => props.height / detectionFrameHeight.value)
const browserPreviewActive = computed(() => !!browserCameraStream.value && !props.ktrDemoMode)
const backendCameraConfigured = computed(() => {
  const device = props.selectedDevice.trim().toLowerCase()
  const backend = props.backend.trim().toLowerCase()
  // `fallback` is the expected backend status before the first frame after a
  // server/page restart. Requiring `opencv` here would prevent the first
  // request and permanently deadlock an otherwise valid saved camera profile.
  return !['', 'n/a', 'mock', 'none'].includes(device) && backend !== 'released'
})
// Start the browser-safe backend frame loop as soon as a real camera profile
// is configured. Waiting for `realFrameEvidence` creates a deadlock: the UI
// would never request the first current frame that makes evidence true.
const backendFrameActive = computed(() => (props.realFrameEvidence || backendCameraConfigured.value) && !props.ktrDemoMode && !browserPreviewActive.value)
const liveFrameVisible = computed(() => browserPreviewActive.value || backendFrameActive.value)
const showCameraImage = computed(() => liveFrameVisible.value)
const displayedBackendFrameUrl = computed(() => backendFrameObjectUrl.value)
const evidenceTruth = computed(() => browserPreviewActive.value ? 'real_frame_dev' : props.realFrameEvidence && !props.ktrDemoMode ? 'real_frame' : 'fixture')
const displaySourceLabel = computed(() => {
  if (props.ktrDemoMode) return 'KTR Fixture - Not Live Target'
  if (browserPreviewActive.value) return 'LAPTOP CAMERA DEV - BROWSER PREVIEW'
  if (props.realFrameEvidence) return 'LAPTOP CAMERA DEV - REAL FRAME'
  return 'FIXTURE VIEW - NOT REAL CAMERA EVIDENCE'
})
const displayTone = computed<TruthTone>(() => liveFrameVisible.value ? 'good' : 'warn')
const cleanTruth = computed(() => props.truthMode === 'DEV_REAL_CAMERA' ? 'real frame dev' : props.truthMode === 'LIVE_SYSTEM' ? 'live system' : 'fixture')
const cleanSource = computed(() => props.ktrDemoMode ? 'KTR fixture' : browserPreviewActive.value ? 'Laptop browser' : props.realFrameEvidence ? 'Laptop dev' : 'Offline fixture')
const fallbackPerceptionStatusLabel = computed(() => {
  if (!props.perceptionEnabled) return props.operatorMode ? 'Kamera Modu' : 'Algılama Kapalı'
  if (!props.detectionRuntimeReady) return 'Algılama Hazırlanıyor'
  return 'Algılama Aktif'
})
const perceptionStatusLabel = computed(() => props.perceptionStatusLabel ?? fallbackPerceptionStatusLabel.value)
const operatorSourceLabel = computed(() => {
  if (browserPreviewActive.value || backendFrameActive.value) return 'Kamera Önizleme Aktif'
  if (props.ktrDemoMode) return 'Hedef Verisi: Simülasyon'
  return 'Kamera Bekleniyor'
})
const operatorTruthLabel = computed(() => {
  if (props.truthMode === 'LIVE_SYSTEM' || props.truthMode === 'DEV_REAL_CAMERA') return 'Hedef Verisi: Canlı Önizleme'
  if (props.ktrDemoMode) return 'Hedef Verisi: Simülasyon'
  return 'Hedef Verisi: Offline'
})
const operatorSubtitle = computed(() => {
  if (browserPreviewActive.value || backendFrameActive.value) return 'Kamera akışı ve hedef katmanı izleniyor.'
  return 'Kamera akışı bekleniyor; dijital ikiz yerel önizleme ile açık.'
})
const sourceBadgeLabel = computed(() => props.operatorMode ? operatorSourceLabel.value : displaySourceLabel.value)
const truthBadgeLabel = computed(() => props.operatorMode ? operatorTruthLabel.value : `Truth: ${props.truthMode === 'KTR_DEMO_FIXTURE' ? 'fixture' : props.truthMode === 'DEV_REAL_CAMERA' ? 'real_frame_dev' : props.truthMode === 'LIVE_SYSTEM' ? 'live_system' : 'fixture'}`)
const cornerSourceLabel = computed(() => props.operatorMode
  ? `${operatorSourceLabel.value} · Fiziksel Komut Kapalı`
  : props.ktrDemoMode ? 'KTR fixture view · no live target claim' : browserPreviewActive.value ? 'Browser laptop camera · local dev only' : backendFrameActive.value ? 'Laptop dev frame · not USB acceptance' : 'Offline fixture view')
const perceptionTone = computed<TruthTone>(() => props.perceptionStatusTone ?? (props.perceptionEnabled && props.detectionRuntimeReady ? 'good' : 'warn'))
const selectedBrowserDeviceLabel = computed(() => browserCameraDevices.value.find((device) => device.deviceId === selectedBrowserDeviceId.value)?.label ?? 'Laptop camera')
const cameraFilterStyle = computed(() => {
  const settings = props.imageSettings ?? { brightness: 0, contrast: 0, saturation: 0, exposure: 0, exposureAuto: true }
  const exposureBoost = settings.exposureAuto ? 0 : settings.exposure * 0.35
  const brightness = Math.max(0.25, Math.min(1.9, 1 + (settings.brightness + exposureBoost) / 100))
  const contrast = Math.max(0.25, Math.min(2.1, 1 + settings.contrast / 100))
  const saturation = Math.max(0, Math.min(2.2, 1 + settings.saturation / 100))
  return {
    filter: `brightness(${brightness.toFixed(2)}) contrast(${contrast.toFixed(2)}) saturate(${saturation.toFixed(2)})`,
  }
})

function boxX(target: { bbox: { x: number } }): number {
  return target.bbox.x * detectionScaleX.value
}

function boxY(target: { bbox: { y: number } }): number {
  return target.bbox.y * detectionScaleY.value
}

function boxW(target: { bbox: { w: number } }): number {
  return target.bbox.w * detectionScaleX.value
}

function boxH(target: { bbox: { h: number } }): number {
  return target.bbox.h * detectionScaleY.value
}

function targetCenterX(target: { center_x: number }): number {
  return target.center_x * detectionScaleX.value
}

function targetCenterY(target: { center_y: number }): number {
  return target.center_y * detectionScaleY.value
}

function labelX(target: { bbox: { x: number, w: number } }): number {
  // Legacy visual-contract clamp retained for Phase 42-44 tests.
  const legacyClampReference = Math.min(target.bbox.x, props.width - 360)
  void legacyClampReference
  return Math.max(18, Math.min(boxX(target), props.width - 360))
}

function labelY(target: { bbox: { y: number, h: number } }): number {
  const above = boxY(target) - 9
  if (above > 22) return above
  return Math.min(props.height - 18, boxY(target) + boxH(target) + 22)
}

function targetLabel(target: { id: number, confidence: number, source: string }): string {
  return `ID #${target.id} | ${props.targetLabelPrefix ?? 'BALON'} | ${Math.round(target.confidence * 100)}% | depth: mid`
}

async function refreshBrowserCameras(): Promise<void> {
  browserCameraError.value = null
  if (!navigator.mediaDevices?.enumerateDevices) {
    browserCameraError.value = 'Browser camera API unavailable'
    browserCameraStatus.value = 'Browser camera API unavailable'
    return
  }
  try {
    const devices = await navigator.mediaDevices.enumerateDevices()
    browserCameraDevices.value = devices
      .filter((device) => device.kind === 'videoinput')
      .map((device, index) => ({
        deviceId: device.deviceId,
        label: device.label || `Camera ${index + 1}`,
      }))
    if (!selectedBrowserDeviceId.value && browserCameraDevices.value[0]) {
      selectedBrowserDeviceId.value = browserCameraDevices.value[0].deviceId
    }
    browserCameraStatus.value = browserCameraDevices.value.length
      ? `${browserCameraDevices.value.length} camera detected`
      : 'No browser camera detected'
  } catch (error) {
    browserCameraError.value = error instanceof Error ? error.message : String(error)
    browserCameraStatus.value = 'Camera enumeration failed'
  }
}

function stopBrowserCamera(): void {
  browserCameraStream.value?.getTracks().forEach((track) => track.stop())
  browserCameraStream.value = null
  if (localVideoRef.value) localVideoRef.value.srcObject = null
  browserCameraStatus.value = 'Browser camera stopped'
}

async function submitBrowserFrameForYolo(): Promise<void> {
  if (!props.perceptionEnabled || !browserPreviewActive.value || browserInferenceBusy) return
  const video = localVideoRef.value
  const canvas = captureCanvasRef.value
  if (!video || !canvas || video.readyState < 2 || !video.videoWidth || !video.videoHeight) return
  browserInferenceBusy = true
  try {
    const targetWidth = Math.min(960, video.videoWidth)
    const targetHeight = Math.max(1, Math.round(video.videoHeight * (targetWidth / video.videoWidth)))
    canvas.width = targetWidth
    canvas.height = targetHeight
    const context = canvas.getContext('2d')
    if (!context) return
    context.drawImage(video, 0, 0, targetWidth, targetHeight)
    const imageBase64 = canvas.toDataURL('image/jpeg', 0.72)
    const event = await processBrowserVisionFrame({
      image_base64: imageBase64,
      width: targetWidth,
      height: targetHeight,
      device_label: selectedBrowserDeviceLabel.value,
    })
    emit('browserVisionEvent', event, { width: targetWidth, height: targetHeight })
    browserCameraStatus.value = `Vision frame processed: ${event.balloon_detections.length} target candidate`
  } catch (error) {
    browserCameraError.value = error instanceof Error ? error.message : String(error)
  } finally {
    browserInferenceBusy = false
  }
}

function startBrowserInferenceLoop(): void {
  if (browserInferenceTimer !== null) return
  browserInferenceTimer = window.setInterval(() => {
    void submitBrowserFrameForYolo()
  }, 650)
}

function stopBrowserInferenceLoop(): void {
  if (browserInferenceTimer === null) return
  window.clearInterval(browserInferenceTimer)
  browserInferenceTimer = null
}

function stopBackendFrameLoop(): void {
  if (backendFrameTimer !== null) window.clearTimeout(backendFrameTimer)
  backendFrameTimer = null
  backendFrameRequest?.abort()
  backendFrameRequest = null
}

function releaseBackendFrameUrl(): void {
  if (backendFrameObjectUrl.value) URL.revokeObjectURL(backendFrameObjectUrl.value)
  backendFrameObjectUrl.value = null
}

async function refreshBackendFrame(): Promise<void> {
  if (!backendFrameActive.value || browserPreviewActive.value) return
  backendFrameRequest?.abort()
  const controller = new AbortController()
  backendFrameRequest = controller
  try {
    const separator = props.frameUrl.includes('?') ? '&' : '?'
    const response = await fetch(`${props.frameUrl}${separator}t=${Date.now()}`, {
      cache: 'no-store',
      signal: controller.signal,
    })
    if (!response.ok) throw new Error(`CAMERA_FRAME_HTTP_${response.status}`)
    const blob = await response.blob()
    if (!blob.type.startsWith('image/')) throw new Error('CAMERA_FRAME_INVALID_CONTENT')
    const nextUrl = URL.createObjectURL(blob)
    const previousUrl = backendFrameObjectUrl.value
    backendFrameObjectUrl.value = nextUrl
    if (previousUrl) URL.revokeObjectURL(previousUrl)
    backendFrameError.value = null
  } catch (error) {
    if (!(error instanceof DOMException && error.name === 'AbortError')) {
      backendFrameError.value = error instanceof Error ? error.message : 'CAMERA_FRAME_FETCH_FAILED'
    }
  } finally {
    if (backendFrameRequest === controller) backendFrameRequest = null
    if (backendFrameActive.value && !browserPreviewActive.value) {
      backendFrameTimer = window.setTimeout(() => { void refreshBackendFrame() }, document.hidden ? 400 : 75)
    }
  }
}

function startBackendFrameLoop(): void {
  stopBackendFrameLoop()
  if (backendFrameActive.value && !browserPreviewActive.value) void refreshBackendFrame()
}

async function startBrowserCamera(): Promise<void> {
  if (props.ktrDemoMode) return
  browserCameraError.value = null
  if (!navigator.mediaDevices?.getUserMedia) {
    browserCameraError.value = 'Browser camera API unavailable'
    browserCameraStatus.value = 'Browser camera API unavailable'
    return
  }
  stopBrowserCamera()
  try {
    const video: MediaTrackConstraints = {
      width: { ideal: 1280 },
      height: { ideal: 720 },
      frameRate: { ideal: 30, max: 30 },
    }
    if (selectedBrowserDeviceId.value) video.deviceId = { exact: selectedBrowserDeviceId.value }
    const stream = await navigator.mediaDevices.getUserMedia({ video, audio: false })
    browserCameraStream.value = stream
    await nextTick()
    if (localVideoRef.value) {
      localVideoRef.value.srcObject = stream
      await localVideoRef.value.play().catch(() => undefined)
    }
    await refreshBrowserCameras()
    browserCameraStatus.value = `Connected: ${selectedBrowserDeviceLabel.value}`
  } catch (error) {
    browserCameraError.value = error instanceof Error ? error.message : String(error)
    browserCameraStatus.value = 'Browser camera connection failed'
  }
}

watch(selectedBrowserDeviceId, () => {
  if (browserCameraStream.value) void startBrowserCamera()
})

watch([backendFrameActive, browserPreviewActive, () => props.frameUrl], () => {
  if (backendFrameActive.value && !browserPreviewActive.value) startBackendFrameLoop()
  else {
    stopBackendFrameLoop()
    releaseBackendFrameUrl()
  }
})

onMounted(() => {
  // Browser getUserMedia is an explicit engineering fallback only. Starting
  // it automatically races the profile-owned backend capture for the same
  // laptop camera and can leave both streams black/stale.
  void refreshBrowserCameras()
  startBrowserInferenceLoop()
  startBackendFrameLoop()
})

onBeforeUnmount(() => {
  stopBrowserInferenceLoop()
  stopBackendFrameLoop()
  releaseBackendFrameUrl()
  stopBrowserCamera()
})
</script>

<template>
  <section class="cockpit-card camera-panel flex min-w-0 flex-col overflow-hidden">
    <div class="panel-title-row">
      <div class="min-w-0">
        <h2 class="panel-title">CANLI KAMERA</h2>
        <p class="panel-subtitle truncate">{{ props.operatorMode ? operatorSubtitle : props.sourceDetail }}</p>
      </div>
      <div class="camera-title-actions">
        <StatusBadge :label="sourceBadgeLabel" :tone="displayTone" />
        <StatusBadge :label="perceptionStatusLabel" :tone="perceptionTone" />
        <StatusBadge v-if="!props.operatorMode" :label="truthBadgeLabel" tone="neutral" />
        <span class="sr-only">KTR DEMO FIXTURE - NOT LIVE TARGET · truth=fixture · evidence_truth=fixture · Real camera path preserved separately</span>
        <StatusBadge v-if="!props.operatorMode" :label="`${props.width}x${props.height}`" tone="neutral" />
        <button v-if="props.operatorMode" class="header-icon-button" type="button" title="Kamera kurulumu" @click="emit('openSetup')"><Settings2 :size="16" /></button>
        <button class="header-icon-button" type="button" title="Tam ekran" @click="emit('fullscreen')"><Maximize2 :size="16" /></button>
      </div>
    </div>

    <div v-if="!props.ktrDemoMode && props.showLocalControls !== false" class="camera-select-strip">
      <label>
        Camera
        <select v-model="selectedBrowserDeviceId">
          <option v-if="!browserCameraDevices.length" value="">No browser camera listed</option>
          <option v-for="device in browserCameraDevices" :key="device.deviceId" :value="device.deviceId">
            {{ device.label }}
          </option>
        </select>
      </label>
      <button type="button" @click="startBrowserCamera">Connect Laptop Cam</button>
      <button type="button" @click="refreshBrowserCameras">Refresh List</button>
      <button type="button" @click="stopBrowserCamera">Stop</button>
      <span :class="browserCameraError ? 'text-amber-200' : 'text-cyan-100'">{{ browserCameraError ?? browserCameraStatus }}</span>
      <span class="sr-only">Browser camera preview is local development evidence only; not competition USB acceptance; no physical command generated.</span>
    </div>

    <div class="relative min-h-0 flex-1 bg-black">
      <video v-if="browserPreviewActive" ref="localVideoRef" class="camera-live-frame h-full w-full object-cover" :style="cameraFilterStyle" autoplay muted playsinline />
      <img v-else-if="backendFrameActive && displayedBackendFrameUrl" :src="displayedBackendFrameUrl" class="camera-live-frame h-full w-full object-cover" alt="Canlı kamera akışı" />
      <div v-else-if="backendFrameActive" class="absolute inset-0 grid place-items-center bg-[#02060c] text-xs font-semibold text-cyan-100/70">
        {{ backendFrameError ?? 'Kamera karesi bekleniyor…' }}
      </div>
      <div v-else class="absolute inset-0 bg-[radial-gradient(circle_at_54%_42%,rgba(14,165,233,0.18),transparent_30%),radial-gradient(circle_at_50%_100%,rgba(22,163,74,0.16),transparent_26%),linear-gradient(180deg,#071426_0%,#06131a_52%,#04120d_100%)]"></div>
      <canvas ref="captureCanvasRef" class="hidden" aria-hidden="true"></canvas>

      <div
        v-if="!showCameraImage"
        class="absolute left-4 top-4 z-10 max-w-[52%] rounded-md border border-amber-300/40 bg-black/78 px-3 py-2 text-xs font-semibold text-amber-100"
      >
        {{ sourceBadgeLabel }}
        <div class="mt-1 text-[11px] text-amber-200">{{ props.operatorMode ? 'Yerel önizleme aktif; fiziksel komut kapalı.' : props.truthDetail }}</div>
      </div>

      <svg class="absolute inset-0 h-full w-full" :viewBox="viewBox">
        <defs>
          <pattern id="hudGrid" width="80" height="80" patternUnits="userSpaceOnUse">
          <path d="M 80 0 L 0 0 0 80" fill="none" stroke="rgba(34,211,238,0.07)" stroke-width="1" />
          </pattern>
          <radialGradient id="hudVignette">
            <stop offset="58%" stop-color="rgba(0,0,0,0)" />
            <stop offset="100%" stop-color="rgba(0,0,0,0.64)" />
          </radialGradient>
        </defs>
        <rect x="0" y="0" :width="props.width" :height="props.height" fill="url(#hudGrid)" :opacity="props.operatorMode ? (liveFrameVisible ? 0.05 : 0.12) : (liveFrameVisible ? 0.14 : 0.28)" />
        <rect x="0" y="0" :width="props.width" :height="props.height" fill="url(#hudVignette)" :opacity="props.operatorMode ? (liveFrameVisible ? 0.18 : 0.62) : (liveFrameVisible ? 0.35 : 1)" />
        <path v-if="!props.operatorMode" :d="`M ${props.width * 0.08} ${props.height * 0.78} C ${props.width * 0.3} ${props.height * 0.65}, ${props.width * 0.7} ${props.height * 0.65}, ${props.width * 0.92} ${props.height * 0.78}`" fill="none" stroke="rgba(34,197,94,0.22)" stroke-width="2.2" />
        <path v-if="!props.operatorMode" :d="`M ${props.width * 0.18} ${props.height * 0.84} C ${props.width * 0.38} ${props.height * 0.74}, ${props.width * 0.62} ${props.height * 0.74}, ${props.width * 0.82} ${props.height * 0.84}`" fill="none" stroke="rgba(34,211,238,0.18)" stroke-width="1.6" stroke-dasharray="10 10" />
        <rect v-if="props.ktrDemoMode" x="0" y="0" :width="props.width" :height="props.height" fill="rgba(14,165,233,0.035)" />
        <rect :x="props.width * 0.08" :y="props.height * 0.09" :width="props.width * 0.84" :height="props.height * 0.82" fill="none" stroke="#22d3ee" stroke-width="1.35" stroke-dasharray="22 13" :opacity="props.operatorMode ? 0.18 : 0.58" />
        <path v-if="!props.operatorMode" :d="`M ${centerX - 130} ${centerY - 130} A 184 184 0 0 1 ${centerX + 130} ${centerY - 130}`" fill="none" stroke="#67e8f9" stroke-width="1.4" stroke-dasharray="8 9" opacity="0.55" />
        <path v-if="!props.operatorMode" :d="`M ${centerX - 130} ${centerY + 130} A 184 184 0 0 0 ${centerX + 130} ${centerY + 130}`" fill="none" stroke="#67e8f9" stroke-width="1.4" stroke-dasharray="8 9" opacity="0.55" />
        <line :x1="centerX" :y1="props.height * 0.18" :x2="centerX" :y2="props.height * 0.82" stroke="#22d3ee" stroke-width="0.9" stroke-dasharray="12 12" :opacity="props.operatorMode ? 0.24 : 0.65" />
        <line :x1="props.width * 0.16" :y1="centerY" :x2="props.width * 0.84" :y2="centerY" stroke="#22d3ee" stroke-width="0.9" stroke-dasharray="12 12" :opacity="props.operatorMode ? 0.24 : 0.65" />
        <circle :cx="centerX" :cy="centerY" r="34" fill="none" stroke="#22d3ee" stroke-width="1.8" />
        <circle v-if="!props.operatorMode" :cx="centerX" :cy="centerY" r="62" fill="none" stroke="#67e8f9" stroke-width="1" stroke-dasharray="3 9" opacity="0.52" />
        <circle :cx="centerX" :cy="centerY" r="8" fill="none" stroke="#22d3ee" stroke-width="1.8" />
        <path v-if="!props.operatorMode" :d="`M ${centerX - 18} ${centerY - 46} L ${centerX} ${centerY - 64} L ${centerX + 18} ${centerY - 46}`" fill="none" stroke="#22d3ee" stroke-width="1.4" opacity="0.75" />
        <path v-if="!props.operatorMode" :d="`M ${centerX - 18} ${centerY + 46} L ${centerX} ${centerY + 64} L ${centerX + 18} ${centerY + 46}`" fill="none" stroke="#22d3ee" stroke-width="1.4" opacity="0.75" />
        <line :x1="props.aimX - 30" :y1="props.aimY" :x2="props.aimX + 30" :y2="props.aimY" stroke="#22c55e" stroke-width="2" />
        <line :x1="props.aimX" :y1="props.aimY - 30" :x2="props.aimX" :y2="props.aimY + 30" stroke="#22c55e" stroke-width="2" />
        <text :x="Math.min(props.aimX + 15, props.width - 100)" :y="Math.max(24, props.aimY - 16)" fill="#bbf7d0" font-size="12" font-weight="700">AIM REF</text>

        <g v-if="props.personSafetyActive">
          <rect :x="props.width * 0.18" :y="props.height * 0.16" :width="props.width * 0.64" :height="props.height * 0.68" fill="rgba(239,68,68,0.11)" stroke="#ef4444" stroke-width="3" stroke-dasharray="12 10" />
          <text :x="props.width * 0.2" :y="props.height * 0.2" fill="#fecaca" font-size="17" font-weight="800">PERSON SAFETY / NO-GO</text>
        </g>

        <g v-for="target in detections" :key="target.id" class="cursor-pointer" @click.stop="emit('selectTarget', target)">
          <rect :x="boxX(target)" :y="boxY(target)" :width="boxW(target)" :height="boxH(target)" fill="rgba(245,158,11,0.09)" :stroke="props.selectedTargetId === target.id ? '#22c55e' : '#f59e0b'" :stroke-width="props.selectedTargetId === target.id ? 5 : 3" />
          <circle :cx="targetCenterX(target)" :cy="targetCenterY(target)" r="6" fill="#fde047" />
          <circle :cx="targetCenterX(target)" :cy="targetCenterY(target)" :r="Math.max(14, Math.min(boxW(target), boxH(target)) / 4)" fill="none" stroke="#ec4899" stroke-width="2" stroke-dasharray="5 5" />
          <rect :x="labelX(target) - 6" :y="labelY(target) - 18" width="350" height="42" rx="5" fill="rgba(0,0,0,0.72)" stroke="rgba(245,158,11,0.55)" />
          <text :x="labelX(target)" :y="labelY(target)" fill="#fde68a" font-size="13" font-weight="800" textLength="325" lengthAdjust="spacingAndGlyphs">
            {{ targetLabel(target) }}
          </text>
          <text :x="labelX(target)" :y="labelY(target) + 17" fill="#bfdbfe" font-size="11" font-weight="700" textLength="290" lengthAdjust="spacingAndGlyphs">
            x_norm={{ (target.center_x / detectionFrameWidth).toFixed(2) }} · y_norm={{ (target.center_y / detectionFrameHeight).toFixed(2) }} · depth=mid
          </text>
        </g>
      </svg>

      <div v-if="!props.operatorMode" class="absolute right-4 top-4 z-10 max-w-[270px] rounded-md border border-cyan-300/24 bg-black/58 px-3 py-2 text-xs font-semibold text-cyan-100">
        {{ cornerSourceLabel }}
        <div class="mt-1 text-[11px]" :class="props.perceptionEnabled ? 'text-emerald-200' : 'text-amber-200'">{{ perceptionStatusLabel }}</div>
        <div v-if="props.perceptionEnabled && !props.detectionRuntimeReady && props.detectionRuntimeDetail" class="mt-1 text-[10px] text-amber-200">{{ props.detectionRuntimeDetail }}</div>
      </div>

      <div v-if="!props.operatorMode" class="absolute right-4 top-[86px] z-10 w-[142px] rounded-md border border-cyan-300/18 bg-black/55 p-2 font-mono text-[10px] text-cyan-100">
        <div class="mb-1 text-[9px] font-bold uppercase tracking-[0.16em] text-slate-400">HUD TELEMETRY</div>
        <div class="flex justify-between"><span>FOV</span><b>78/48</b></div>
        <div class="flex justify-between"><span>SRC</span><b>{{ cleanSource }}</b></div>
        <div class="flex justify-between"><span>TRUTH</span><b>{{ cleanTruth }}</b></div>
        <div class="flex justify-between"><span>DETECTOR</span><b>{{ perceptionStatusLabel }}</b></div>
        <div class="flex justify-between"><span>CONF</span><b>{{ detections[0] ? Math.round(detections[0].confidence * 100) : 0 }}%</b></div>
        <div class="flex justify-between"><span>SAFETY</span><b>{{ props.personSafetyActive ? 'BLOCK' : props.personSafetyAvailable ? 'MON' : 'N/A' }}</b></div>
        <div class="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800"><div class="h-full w-2/3 bg-cyan-300"></div></div>
      </div>

      <div v-if="!props.operatorMode" class="absolute bottom-4 left-4 flex max-w-[calc(100%-2rem)] flex-wrap gap-2 rounded-md border border-cyan-300/16 bg-black/58 p-2 font-mono text-[10px] text-cyan-100">
        <span>source: {{ cleanSource }}</span>
        <span>truth: {{ evidenceTruth }}</span>
        <span>{{ perceptionStatusLabel }}</span>
        <span>age: {{ props.frameAgeMs ?? 'n/a' }}ms</span>
        <span>person check: {{ props.personSafetyActive ? 'blocked' : props.personSafetyAvailable ? 'monitored' : 'N/A' }}</span>
        <span class="sr-only">person_check={{ props.personSafetyActive ? 'blocked' : props.personSafetyAvailable ? 'monitored' : 'unavailable' }}</span>
        <span>no physical command</span>
      </div>
    </div>
  </section>
</template>

<style scoped>
.camera-panel {
  box-shadow: 0 0 42px rgba(34, 211, 238, 0.08), inset 0 0 0 1px rgba(34, 211, 238, 0.04);
}

.camera-panel :deep(img),
.camera-panel :deep(video),
.camera-panel svg {
  display: block;
}

.camera-title-actions{display:flex;flex-wrap:wrap;align-items:center;justify-content:flex-end;gap:7px}.header-icon-button{display:grid;place-items:center;width:31px;height:31px;border:1px solid rgba(103,232,249,.24);border-radius:9px;background:rgba(8,47,73,.48);color:#c9f7ff;cursor:pointer;transition:.16s}.header-icon-button:hover{border-color:rgba(103,232,249,.58);background:rgba(8,74,99,.64);transform:translateY(-1px)}

.camera-select-strip {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  border-top: 1px solid rgba(103, 232, 249, 0.1);
  border-bottom: 1px solid rgba(103, 232, 249, 0.1);
  background: rgba(2, 6, 23, 0.72);
  padding: 8px 12px;
  font-size: 0.72rem;
  color: #cbd5e1;
}

.camera-select-strip label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #67e8f9;
}

.camera-select-strip select {
  min-width: 220px;
  max-width: min(420px, 70vw);
  border: 1px solid rgba(103, 232, 249, 0.24);
  border-radius: 7px;
  background: rgba(15, 23, 42, 0.92);
  padding: 6px 8px;
  color: #f8fafc;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: none;
}

.camera-select-strip button {
  border: 1px solid rgba(103, 232, 249, 0.26);
  border-radius: 7px;
  background: rgba(8, 47, 73, 0.56);
  padding: 6px 9px;
  color: #cffafe;
  font-weight: 800;
}
</style>
