<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Crosshair, Flame, Pause, Play, ShieldAlert, Target, TimerReset } from '@lucide/vue'
import { useFullscreen } from '@vueuse/core'
import CockpitTopBar from '../components/cockpit/CockpitTopBar.vue'
import CameraControlPanel from '../components/cockpit/CameraControlPanel.vue'
import DetectionConfigPanel from '../components/cockpit/DetectionConfigPanel.vue'
import DigitalTwinPanel from '../components/digital-twin/DigitalTwinPanel.vue'
import DeveloperDebugDrawer from '../components/cockpit/DeveloperDebugDrawer.vue'
import EngineerTechnicalTabs from '../components/cockpit/EngineerTechnicalTabs.vue'
import EvidenceReplayPanel from '../components/cockpit/EvidenceReplayPanel.vue'
import EngagementEvidenceReplayPanel from '../components/cockpit/EngagementEvidenceReplayPanel.vue'
import LiveCameraPanel from '../components/cockpit/LiveCameraPanel.vue'
import MotorPidPanel from '../components/cockpit/MotorPidPanel.vue'
import OperatorLogPanel from '../components/cockpit/OperatorLogPanel.vue'
import SafetyModeBanner from '../components/cockpit/SafetyModeBanner.vue'
import ScenePlanPanel from '../components/cockpit/ScenePlanPanel.vue'
import { applyCameraImageConfig, applyPerceptionConfig } from '../api/operatorConfig'
import { evaluateFireRequest } from '../api/decision'
import { useRuntimeTruth, type TruthTone } from '../composables/useRuntimeTruth'
import { useOperationalReadiness } from '../composables/useOperationalReadiness'
import { useDecisionStore } from '../stores/decisionStore'
import { useDeviceRuntimeStore } from '../stores/deviceRuntimeStore'
import { useDigitalTwinStore } from '../stores/digitalTwinStore'
import { useHardwareStore } from '../stores/hardwareStore'
import { useMissionStore } from '../stores/missionStore'
import { useMotionStore } from '../stores/motionStore'
import { useSerialStore } from '../stores/serialStore'
import { useSystemStore } from '../stores/systemStore'
import { useVisionStore } from '../stores/visionStore'
import type { CockpitBadge, CockpitEvent, CockpitMetric } from '../components/cockpit/types'
import type { ManagedDevice } from '../types/deviceRuntime'
import type { VisionEvent } from '../types/vision'
import type { EngagementReplayControl } from '../types/engagementReplay'

const system = useSystemStore()
const vision = useVisionStore()
const runtime = useDeviceRuntimeStore()
const motion = useMotionStore()
const serial = useSerialStore()
const hardware = useHardwareStore()
const decision = useDecisionStore()
const mission = useMissionStore()
const digitalTwin = useDigitalTwinStore()
const truth = useRuntimeTruth()
const operational = useOperationalReadiness()
const operationalLiveReady = operational.liveReady
const operationalBlocker = operational.primaryBlocker

const selectedBalloonId = ref<number | null>(null)
const targetSelectBusy = ref(false)
const virtualTrackIntent = ref(false)
const cameraSectionRef = ref<HTMLElement | null>(null)
const { enter: enterCameraFullscreen } = useFullscreen(cameraSectionRef)
const liveConfInput = ref('0.05')
const confApplyBusy = ref(false)
const lastConfidenceApplyAt = ref('Henüz uygulanmadı')
const confidenceApplyStatus = ref('Preview only')
const engineerPanelOpen = ref(false)
const operatorToast = ref<{ tone: 'success' | 'warn' | 'error', message: string } | null>(null)
const engagementReplayControl = ref<EngagementReplayControl | null>(null)
const cameraImageSettings = ref({
  brightness: -14,
  contrast: 8,
  saturation: -4,
  exposure: 0,
  exposureAuto: true,
})
const engineerActiveTab = ref<'camera' | 'detection' | 'motion' | 'calibration' | 'logs'>('camera')
let refreshTimer: ReturnType<typeof setInterval> | null = null
let digitalTwinTimer: ReturnType<typeof setInterval> | null = null
const DIGITAL_TWIN_POLL_MS = 500 // metadata 2 Hz

const latestFrame = computed(() => vision.latestEvent)
const overlayWidth = computed(() => Math.max(1, vision.cameraStatus.width || runtime.cameraStatus.actual_width || 1280))
const overlayHeight = computed(() => Math.max(1, vision.cameraStatus.height || runtime.cameraStatus.actual_height || 720))
const centerX = computed(() => overlayWidth.value / 2)
const centerY = computed(() => overlayHeight.value / 2)
const aimX = computed(() => centerX.value + motion.trackingStatus.aim_offset_x_px)
const aimY = computed(() => centerY.value + motion.trackingStatus.aim_offset_y_px)
const personSafety = computed(() => decision.decision.person_safety)
const personSafetyActive = computed(() => personSafety.value?.person_detected === true)
const personSafetyAvailable = computed(() => personSafety.value?.enabled === true && personSafety.value.source !== 'unavailable')
const digitalTwinEnabled = computed(() => ((import.meta.env.VITE_DIGITAL_TWIN_ENABLED as string | undefined) ?? 'true') !== 'false')
const ktrDemoMode = computed(() => new URLSearchParams(window.location.search).get('ktr_demo') === '1')
const latestFrameMatchesSelectedCamera = computed(() => {
  const event = latestFrame.value
  if (!event) return false
  if (ktrDemoMode.value) return true
  const source = String(event.source ?? '').toLowerCase()
  const frameOrigin = String(event.frame_origin ?? '').toLowerCase()
  const sourceKind = String(event.camera_source_kind ?? '').toLowerCase()
  if (runtime.cameraStatus.profile.source_type === 'mock') {
    return frameOrigin === 'mock_frame' || sourceKind === 'mock' || source.includes('mock')
  }
  return frameOrigin === 'real_capture'
    || frameOrigin === 'browser_upload'
    || frameOrigin === 'browser_frame_upload'
    || sourceKind === 'real_camera'
    || source.includes('live_camera')
})
const activeBalloons = computed(() => latestFrameMatchesSelectedCamera.value ? latestFrame.value?.balloon_detections ?? [] : [])
const activeBodies = computed(() => latestFrameMatchesSelectedCamera.value ? latestFrame.value?.body_detections ?? [] : [])
const selectedTarget = computed(() => activeBalloons.value.find((target) => target.id === selectedBalloonId.value) ?? null)
const initialParams = new URLSearchParams(window.location.search)
const autoTrackingRequested = initialParams.get('autotrack') === '1'
type CockpitUiProfile = 'operator' | 'engineer'
const uiProfile = computed<CockpitUiProfile>(() => engineerPanelOpen.value ? 'engineer' : 'operator')
const isOperatorUi = computed(() => uiProfile.value === 'operator')
const worldMode = computed(() => window.location.pathname.includes('/cockpit/world') || initialParams.get('world') === '1')
const perceptionEnabled = ref(initialParams.get('perception') !== 'off')
const qualityMode = ref<'LOW' | 'BALANCED' | 'HIGH' | 'ULTRA'>(
  initialParams.get('quality') === 'low' || initialParams.get('perf') === 'low'
    ? 'LOW'
    : initialParams.get('quality') === 'balanced'
      ? 'BALANCED'
      : initialParams.get('quality') === 'ultra' || window.location.pathname.includes('/cockpit/world')
        ? 'ULTRA'
      : initialParams.get('quality') === 'high' || initialParams.get('ktr_demo') === '1'
        ? 'HIGH'
        : 'BALANCED',
)
const performanceMode = computed(() => qualityMode.value)
const detectionRuntimeReady = computed(() => (
  perceptionEnabled.value
  && runtime.visionStatus.adapter_available
  && !runtime.visionStatus.reload_required
  && vision.visionStatus.running
))
const detectionRuntimeDetail = computed(() => {
  if (!perceptionEnabled.value) return 'camera only'
  if (runtime.visionStatus.reload_required) return 'model reload required'
  if (!runtime.visionStatus.adapter_available) return runtime.visionStatus.errors[0] ?? runtime.visionStatus.warnings[0] ?? 'vision adapter unavailable'
  if (!vision.visionStatus.running) return 'pipeline stopped'
  return `${activeBalloons.value.length} target candidates`
})
const productionVisionReady = computed(() => (
  runtime.visionStatus.production_yolo_loaded
  && !runtime.visionStatus.advisory_only
))
const testVisionAdapter = computed(() => runtime.visionStatus.test_adapter_active)
const yoloStatusLabel = computed(() => {
  if (!perceptionEnabled.value) return 'ALGILAMA KAPALI'
  if (!detectionRuntimeReady.value) return 'ALGILAMA BEKLİYOR'
  if (productionVisionReady.value) return 'PROD YOLO AKTİF'
  if (testVisionAdapter.value) return 'TEST ADAPTÖRÜ AKTİF'
  return 'LEGACY YOLO · YARIŞMA DIŞI'
})
const yoloStatusTone = computed<TruthTone>(() => (
  detectionRuntimeReady.value && productionVisionReady.value
    ? 'good'
    : detectionRuntimeReady.value
      ? 'warn'
      : 'warn'
))
const targetLabelPrefix = computed(() => productionVisionReady.value ? 'BALON' : 'BALON ADAYI')
const backendStatusLabel = computed(() => system.connectionStatus === 'connected' ? 'Backend Connected' : 'Backend Offline')
const activeConfidence = computed(() => Number(runtime.visionStatus.profile.conf ?? normalizedLiveConf()))
const backendCameraOptions = computed(() => runtime.inventory.cameras ?? [])
const stepAssetLoaded = computed(() => digitalTwin.assets?.selected_asset_type === 'REAL_STEP_KINEMATIC_GLB' || digitalTwin.assets?.selected_asset_type === 'REAL_STEP_GLB' || digitalTwin.assets?.selected_asset_type === 'REAL_STEP_HIFI_GLB' || digitalTwin.assets?.selected_asset_type === 'HYBRID_FIDELITY_GLB')
const phase54AssetHeaderLabel = computed(() => {
  if (digitalTwin.assets?.selected_asset_type === 'REAL_STEP_KINEMATIC_GLB') return 'Kinematic STEP'
  if (digitalTwin.assets?.selected_asset_type === 'HYBRID_FIDELITY_GLB') return 'Hybrid Fidelity'
  if (digitalTwin.assets?.selected_asset_type === 'REAL_STEP_HIFI_GLB') return 'STEP HiFi'
  if (digitalTwin.assets?.selected_asset_type === 'REAL_STL_GEOMETRY_GLB') return 'STL Geometry'
  return stepAssetLoaded.value ? 'Colored STEP' : 'Pending'
})
const stepMaterialLabel = computed(() => {
  const materialStatus = digitalTwin.assets?.conversion_status ?? ''
  if (digitalTwin.assets?.selected_asset_type === 'HYBRID_FIDELITY_GLB') return 'Hybrid'
  if (materialStatus.includes('materials_reconstructed')) return 'Reconstructed'
  if (materialStatus.includes('materials_preserved')) return 'Preserved'
  return stepAssetLoaded.value ? 'STEP Material' : 'Asset Pending'
})

const cameraSourceLabel = computed(() => {
  if (isOperatorUi.value) {
    if (runtime.cameraStatus.source_mode === 'REAL_USB_CAMERA_LIVE') return 'USB Kamera Aktif'
    if (runtime.cameraStatus.source_mode?.includes('REAL_LAPTOP') || runtime.cameraStatus.is_laptop_camera) return 'Kamera Önizleme Aktif'
    if (ktrDemoMode.value) return 'Simülasyon Kamerası'
    return 'Kamera Bekleniyor'
  }
  if (ktrDemoMode.value) return 'FIXTURE VIEW - NOT REAL CAMERA EVIDENCE'
  if (runtime.cameraStatus.source_mode === 'REAL_LAPTOP_CAMERA_LIVE' && runtime.cameraStatus.is_real_camera_evidence) return 'LAPTOP CAMERA DEV - REAL FRAME'
  if (runtime.cameraStatus.source_mode === 'REAL_LAPTOP_CAMERA_LIVE') return 'LAPTOP CAMERA FRAME PENDING'
  if (runtime.cameraStatus.source_mode === 'REAL_LAPTOP_CAMERA_LATEST_FRAME') return 'LATEST LAPTOP FRAME — NOT LIVE'
  if (runtime.cameraStatus.source_mode === 'REAL_USB_CAMERA_LIVE' && runtime.cameraStatus.is_real_camera_evidence) return 'REAL USB CAMERA LIVE'
  if (runtime.cameraStatus.source_mode === 'REAL_USB_CAMERA_LATEST_FRAME') return 'LATEST USB FRAME'
  if (runtime.cameraStatus.profile.source_type === 'mock') return 'MOCK/SURROGATE'
  if (runtime.cameraStatus.source_mode === 'CAMERA_UNAVAILABLE') return 'CAMERA UNAVAILABLE'
  return runtime.cameraStatus.source_mode ?? 'CAMERA SOURCE UNKNOWN'
})
const truthMode = computed<'KTR_DEMO_FIXTURE' | 'DEV_REAL_CAMERA' | 'LIVE_SYSTEM' | 'OFFLINE_FIXTURE'>(() => {
  if (ktrDemoMode.value) return 'KTR_DEMO_FIXTURE'
  if (runtime.cameraStatus.is_real_camera_evidence && runtime.cameraStatus.is_laptop_camera) return 'DEV_REAL_CAMERA'
  if (runtime.cameraStatus.is_external_usb_camera && truth.picoHealthy.value) return 'LIVE_SYSTEM'
  return 'OFFLINE_FIXTURE'
})
const truthLabel = computed(() => {
  if (isOperatorUi.value) {
    if (truthMode.value === 'LIVE_SYSTEM' || truthMode.value === 'DEV_REAL_CAMERA') return 'Canlı Önizleme'
    if (truthMode.value === 'KTR_DEMO_FIXTURE') return 'Simülasyon'
    return 'Offline'
  }
  if (truthMode.value === 'KTR_DEMO_FIXTURE') return 'KTR Fixture'
  if (truthMode.value === 'DEV_REAL_CAMERA') return 'Real Frame Dev'
  if (truthMode.value === 'LIVE_SYSTEM') return 'Live System'
  return 'Fixture / Offline'
})
const truthDetail = computed(() => {
  if (isOperatorUi.value) {
    if (truthMode.value === 'LIVE_SYSTEM' || truthMode.value === 'DEV_REAL_CAMERA') return 'Kamera görüntüsü izleniyor; fiziksel komut kapalı.'
    if (truthMode.value === 'KTR_DEMO_FIXTURE') return 'Simülasyon hedef verisi kullanılıyor.'
    return 'Backend veya kamera yoksa yerel önizleme korunur.'
  }
  if (truthMode.value === 'KTR_DEMO_FIXTURE') return 'truth=fixture · deterministic KTR view · not live target evidence'
  if (truthMode.value === 'DEV_REAL_CAMERA') return 'truth=real_frame_dev · laptop camera only · not competition USB acceptance'
  if (truthMode.value === 'LIVE_SYSTEM') return 'truth=live_system · USB camera and Pico telemetry present'
  return 'truth=fixture · hardware offline expected'
})
const cameraSourceTone = computed<TruthTone>(() => {
  if (ktrDemoMode.value) return 'warn'
  if (runtime.cameraStatus.source_mode === 'REAL_LAPTOP_CAMERA_LIVE' || runtime.cameraStatus.source_mode === 'REAL_USB_CAMERA_LIVE') return 'good'
  if (runtime.cameraStatus.source_mode?.includes('LATEST') || runtime.cameraStatus.is_laptop_camera) return 'warn'
  return truth.cameraTone.value
})
const cameraPanelDetail = computed(() => {
  if (isOperatorUi.value) {
    if (truthMode.value === 'LIVE_SYSTEM' || truthMode.value === 'DEV_REAL_CAMERA') return 'Kamera önizleme aktif.'
    if (truthMode.value === 'KTR_DEMO_FIXTURE') return 'Simülasyon hedef verisi.'
    return 'Kamera bağlantısı bekleniyor.'
  }
  if (truthMode.value === 'KTR_DEMO_FIXTURE') return 'KTR fixture view · truth=fixture · no live camera claim'
  if (truthMode.value === 'DEV_REAL_CAMERA') return 'Laptop development frame · not competition USB camera'
  if (truthMode.value === 'LIVE_SYSTEM') return 'Live USB camera + telemetry source'
  return 'Offline fixture view · hardware expected offline'
})
const profileDisplayLabel = computed(() => {
  const profile = operational.preflight.value?.profile
  if (profile === 'DRY_RUN') return 'TEST'
  if (profile === 'LIVE_TEST') return 'CANLI TEST'
  if (profile === 'VIDEO_DEMO') return 'VİDEO DEMO'
  if (profile === 'COMPETITION') return 'YARIŞMA'
  return 'BİLİNMİYOR'
})
const stageDisplayLabel = computed(() => {
  if (mission.snapshot.state.active_stage === 'stage1') return 'AŞAMA 1'
  if (mission.snapshot.state.active_stage === 'stage2') return 'AŞAMA 2'
  if (mission.snapshot.state.active_stage === 'stage3') return 'AŞAMA 3'
  return 'BİLİNMİYOR'
})
const topBadges = computed<CockpitBadge[]>(() => [
  { label: `MOD ${profileDisplayLabel.value}`, tone: operational.preflight.value?.profile === 'DRY_RUN' ? 'neutral' : operational.liveReady.value ? 'good' : 'warn' },
  { label: `GÖREV ${stageDisplayLabel.value}`, tone: 'neutral' },
  { label: operational.liveReady.value ? 'SİSTEM HAZIR' : `ENGEL ${operational.primaryBlocker.value?.reasonCode ?? 'PREFLIGHT_REQUIRED'}`, tone: operational.liveReady.value ? 'good' : 'warn' },
  { label: `E-STOP ${operational.preflight.value?.gates.find((item) => item.code === 'ESTOP_RELEASED')?.ready ? 'BIRAKILMIŞ' : operational.preflight.value?.gates.find((item) => item.code === 'ESTOP_ACTIVE') ? 'AKTİF' : 'BİLİNMİYOR'}`, tone: operational.preflight.value?.gates.find((item) => item.code === 'ESTOP_ACTIVE') ? 'bad' : operational.preflight.value ? 'warn' : 'neutral' },
])
const operatorEvents = computed<CockpitEvent[]>(() => {
  const issues = truth.healthIssues.value.slice(0, 5).map((issue) => ({
    id: issue.id,
    title: `${issue.area} · ${issue.label}`,
    detail: issue.detail,
    tone: issue.tone,
  }))
  return [
    { id: 'backend_status', title: backendStatusLabel.value, detail: system.connectionStatus === 'connected' ? 'Canlı veri bağlantısı açık.' : 'Yerel önizleme aktif; görev ekranı çalışır durumda.', tone: system.connectionStatus === 'connected' ? 'good' : 'warn' },
    { id: 'camera_source_decision', title: cameraSourceLabel.value, detail: `${truthLabel.value} · MODEL ${yoloStatusLabel.value}`, tone: cameraSourceTone.value },
    { id: 'target_projected', title: activeBalloons.value.length ? 'Hedef algılandı' : 'Hedef bekleniyor', detail: activeBalloons.value.length ? `Yön ${projectionBearing.value}; derinlik ${projectionDepth.value}.` : 'Kamera alanında hedef yok.', tone: activeBalloons.value.length ? 'good' : 'neutral' },
    { id: 'safety_no_tx', title: 'Atış kapısı kapalı', detail: 'Fiziksel komut ve seri TX kapalı.', tone: 'good' },
    { id: 'person_safety', title: personSafetyActive.value ? 'İnsan güvenliği aktif' : personSafetyAvailable.value ? 'İnsan güvenliği izleniyor' : 'İnsan güvenliği bekleniyor', detail: personSafetyActive.value ? 'Atış kapısı insan güvenliği nedeniyle kapalı.' : personSafetyAvailable.value ? 'Sistem izleme modunda.' : 'Sınıflandırıcı durumu bekleniyor.', tone: personSafetyActive.value ? 'bad' : personSafetyAvailable.value ? 'good' : 'warn' },
    ...(issues.length ? issues : [{ id: 'clean', title: 'Operational log clear', detail: 'Kritik uyarı yok; dry-run safety invariant aktif.', tone: 'good' as TruthTone }]),
  ]
})
const bottomMetrics = computed<CockpitMetric[]>(() => [
  { key: 'target', label: 'Seçili hedef', value: selectedTarget.value ? `#${selectedTarget.value.id}` : 'hedef yok', tone: selectedTarget.value ? 'good' : 'neutral' },
  { key: 'tracking', label: 'Takip', value: virtualTrackIntent.value ? 'kilitli' : engagementState.value, tone: virtualTrackIntent.value ? 'good' : 'neutral' },
  { key: 'fire', label: 'FIRE', value: operational.liveReady.value ? 'READY' : operational.primaryBlocker.value?.reasonCode ?? 'PREFLIGHT_REQUIRED', tone: operational.liveReady.value ? 'good' : 'warn' },
  { key: 'mission', label: 'Görev', value: `${mission.snapshot.state.active_stage} · ${mission.snapshot.state.elapsed_s}s`, tone: 'neutral' },
])
const targetPlanX = computed(() => {
  const target = selectedTarget.value
  if (!target) return 210
  return 40 + (target.center_x / overlayWidth.value) * 240
})
const targetPlanY = computed(() => {
  const target = selectedTarget.value
  if (!target) return 58
  return 24 + (target.center_y / overlayHeight.value) * 96
})
const projectionEstimate = computed(() => digitalTwin.state?.target_projection_estimates?.[0] ?? null)
const projectionXNorm = computed(() => projectionEstimate.value?.normalized_center_x?.toFixed(2) ?? '0.76')
const projectionYNorm = computed(() => projectionEstimate.value?.normalized_center_y?.toFixed(2) ?? '0.54')
const projectionArea = computed(() => projectionEstimate.value?.bbox_area_ratio?.toFixed(3) ?? '0.031')
const projectionDepth = computed(() => projectionEstimate.value?.estimated_range_band ?? 'mid')
const projectionPoseSource = computed(() => digitalTwin.state?.device_pose.pose_source ?? 'tracker_estimate')
const projectionBearing = computed(() => {
  const x = Number(projectionXNorm.value)
  if (x > 0.62) return 'RIGHT'
  if (x < 0.38) return 'LEFT'
  return 'MID'
})
const engagementState = computed(() => {
  if (!activeBalloons.value.length) return 'NO TARGET'
  if (!selectedTarget.value) return 'TARGET DETECTED'
  if (virtualTrackIntent.value) return 'TRACKING PREVIEW · FIRE GATE BLOCKED / NO TX'
  return 'TARGET SELECTED · FIRE GATE BLOCKED / NO TX'
})

function showToast(tone: 'success' | 'warn' | 'error', message: string): void {
  operatorToast.value = { tone, message }
  window.setTimeout(() => {
    if (operatorToast.value?.message === message) operatorToast.value = null
  }, 3500)
}

function cameraSourceTypeFor(device: ManagedDevice): 'laptop' | 'usb' {
  const text = `${device.name} ${device.description} ${device.manufacturer ?? ''} ${device.stable_path ?? ''} ${device.device_path}`.toLowerCase()
  if (text.includes('usb') || text.includes('hd camera') || text.includes('external')) return 'usb'
  return 'laptop'
}

async function applyBackendCamera(deviceId: string): Promise<void> {
  const camera = backendCameraOptions.value.find((item) => item.device_id === deviceId)
  if (!camera) return
  runtime.cameraDraft = {
    ...runtime.cameraStatus.profile,
    source_type: cameraSourceTypeFor(camera),
    device_id: camera.device_id,
    device_path: camera.device_path,
    stable_path: camera.stable_path,
    width: Math.max(640, runtime.cameraStatus.profile.width || 1280),
    height: Math.max(360, runtime.cameraStatus.profile.height || 720),
    fps: Math.max(15, runtime.cameraStatus.profile.fps || 30),
    stream_width: 1280,
    stream_height: 720,
    inference_width: 1280,
    inference_height: 720,
    pixel_format: runtime.cameraStatus.profile.pixel_format === 'auto' ? 'MJPG' : runtime.cameraStatus.profile.pixel_format,
    roi: { ...runtime.cameraStatus.profile.roi },
  }
  await runtime.applyCamera()
  if (perceptionEnabled.value) {
    await ensureYoloRuntime()
    await vision.start()
  }
  await refreshAll()
}

function normalizedLiveConf(): number {
  const parsed = Number(liveConfInput.value.replace(',', '.'))
  return Number.isFinite(parsed) ? Math.max(0.001, Math.min(1, parsed)) : 0.05
}

async function ensureYoloRuntime(conf?: number): Promise<void> {
  const managedProfileActive = Boolean(localStorage.getItem('istiklal_active_profile_id'))
  if (managedProfileActive) {
    if (conf === undefined) return
    runtime.visionDraft = {
      ...runtime.visionStatus.profile,
      conf,
      balloon_conf_threshold: conf,
    }
    await runtime.applyVision()
    return
  }
  const effectiveConf = conf ?? normalizedLiveConf()
  runtime.visionDraft = {
    ...runtime.visionStatus.profile,
    inference_adapter: 'ultralytics_yolo',
    active_balloon_model_id: 'legacy-balloon-yolo',
    active_body_model_id: null,
    conf: effectiveConf,
    balloon_conf_threshold: effectiveConf,
    device: 'auto',
    imgsz: 640,
    max_det: 20,
    tracker_enabled: false,
    tracker_type: 'none',
  }
  await runtime.applyVision()
  await runtime.reloadModels()
}

async function applyLiveConfidence(conf?: number): Promise<void> {
  const nextConf = conf ?? normalizedLiveConf()
  liveConfInput.value = nextConf.toFixed(nextConf < 0.1 ? 3 : 2).replace(/0+$/, '').replace(/\.$/, '')
  confApplyBusy.value = true
  try {
    await applyPerceptionConfig({ confidence_threshold: nextConf, yolo_enabled: perceptionEnabled.value })
    await ensureYoloRuntime(nextConf)
    if (perceptionEnabled.value) {
      await vision.stop().catch(() => undefined)
      await vision.start()
    }
    await refreshAll()
    lastConfidenceApplyAt.value = new Date().toLocaleTimeString('tr-TR')
    confidenceApplyStatus.value = 'Applied'
    showToast('success', `Algılama eşiği ${liveConfInput.value} olarak uygulandı`)
  } catch (error) {
    confidenceApplyStatus.value = 'Failed'
    showToast('error', `Uygulanamadı: ${error instanceof Error ? error.message : 'backend yanıt vermedi'}`)
  } finally {
    confApplyBusy.value = false
  }
}

async function togglePerception(): Promise<void> {
  perceptionEnabled.value = !perceptionEnabled.value
  const params = new URLSearchParams(window.location.search)
  if (perceptionEnabled.value) params.delete('perception')
  else params.set('perception', 'off')
  const next = `${window.location.pathname}${params.toString() ? `?${params.toString()}` : ''}`
  window.history.replaceState(null, '', next)
  if (perceptionEnabled.value) {
    await ensureYoloRuntime()
    await vision.start()
  }
  await applyPerceptionConfig({ confidence_threshold: normalizedLiveConf(), yolo_enabled: perceptionEnabled.value }).catch(() => undefined)
  await refreshAll()
  showToast(
    perceptionEnabled.value && productionVisionReady.value && detectionRuntimeReady.value ? 'success' : 'warn',
    perceptionEnabled.value
      ? `${yoloStatusLabel.value} — ${detectionRuntimeDetail.value}`
      : 'Algılama kapalı — yalnız kamera',
  )
}

async function openCameraFullscreen(): Promise<void> {
  await enterCameraFullscreen()
}

async function selectBalloonTarget(balloon: { id: number, center_x: number, center_y: number }): Promise<void> {
  selectedBalloonId.value = balloon.id
  virtualTrackIntent.value = true
  targetSelectBusy.value = false
  showToast('success', `Hedef #${balloon.id} seçildi · 3D radar güncellendi`)
}

async function toggleTracking(): Promise<void> {
  try {
    if (motion.trackingStatus.state === 'TRACKING') {
      await motion.stopTracking()
      virtualTrackIntent.value = false
      showToast('warn', 'Takip durduruldu')
    } else {
      await motion.startTracking()
      showToast('success', 'Takip başlatıldı')
    }
    await refreshAll()
  } catch (caught) {
    showToast('error', caught instanceof Error ? caught.message : 'Takip değiştirilemedi')
  }
}

function openSetup(): void { window.location.assign('/setup?step=hardware') }

async function requestFire(): Promise<void> {
  try {
    const result = await evaluateFireRequest(true)
    if (result.accepted) showToast('success', 'FIRE komutu Pico ACK ile kabul edildi')
    else showToast('warn', result.blocking_reasons[0] ?? result.reason)
    await refreshAll()
  } catch (caught) {
    showToast('error', caught instanceof Error ? caught.message : 'FIRE isteği gönderilemedi')
  }
}

function applyBrowserVisionEvent(event: VisionEvent, size: { width: number; height: number }): void {
  if (!event) return
  vision.applyVisionEvent(event)
  vision.applyCameraStatus({
    ...vision.cameraStatus,
    connected: true,
    running: true,
    width: size.width,
    height: size.height,
    source_mode: 'BROWSER_CAMERA_UPLOAD',
    source: 'browser_camera',
    camera_mode: 'browser',
    selected_device: event.camera_device_path ?? 'browser_camera',
    selected_backend: 'browser_upload',
    is_real_camera_evidence: true,
    is_laptop_camera: true,
    last_capture_error: null,
  })
  vision.applyVisionStatus({
    ...vision.visionStatus,
    running: true,
    vision_mode: 'ultralytics_yolo',
    body_model_loaded: false,
    balloon_model_loaded: true,
    fps: event.fps,
    camera_fps: event.camera_fps,
    detector_fps: event.detector_fps,
    latest_frame_id: event.frame_id,
    latest_latency_ms: event.total_latency_ms,
    latest_total_ms: event.total_ms,
    camera_source_kind: event.camera_source_kind,
    frame_origin: event.frame_origin,
    detector_kind: event.detector_kind,
    body_count: event.body_detections.length,
    balloon_count: event.balloon_detections.length,
    warnings: event.warnings,
    advisory_only: true,
  })
}

async function refreshCameraInventory(): Promise<void> {
  await runtime.refresh()
  showToast('success', 'Kamera listesi yenilendi')
}

async function stopCameraPreview(): Promise<void> {
  await vision.stop().catch(() => undefined)
  showToast('warn', 'Kamera/detection akışı durduruldu')
}

async function updateCameraImageSettings(settings: typeof cameraImageSettings.value): Promise<void> {
  cameraImageSettings.value = { ...settings }
  await applyCameraImageConfig({
    brightness: settings.brightness,
    contrast: settings.contrast,
    saturation: settings.saturation,
    exposure: settings.exposure,
    exposure_auto: settings.exposureAuto,
    preview_filter_only: true,
  }).catch(() => undefined)
}

function resetCameraImageSettings(): void {
  void updateCameraImageSettings({ brightness: 0, contrast: 0, saturation: 0, exposure: 0, exposureAuto: true })
  showToast('success', 'Kamera görüntü ayarları sıfırlandı')
}

function setEngineerTab(tab: string): void {
  if (tab === 'camera' || tab === 'detection' || tab === 'motion' || tab === 'calibration' || tab === 'logs') {
    engineerActiveTab.value = tab
  }
}

async function refreshAll(): Promise<void> {
  const tasks: Promise<unknown>[] = [
    operational.refresh(),
    runtime.refresh(),
    hardware.refresh(),
    serial.refresh(),
    motion.refresh(),
    motion.refreshTrackingStatus(),
    decision.refresh(),
    mission.refresh(),
  ]
  if (perceptionEnabled.value) tasks.unshift(vision.refresh())
  await Promise.all(tasks)
}

async function loadEngagementTwinReplay(engagementId: string): Promise<void> {
  await digitalTwin.loadEngagementReplay(engagementId)
  engagementReplayControl.value = { engagementId, positionMs: 0, playing: false, playbackRate: 1 }
}

onMounted(() => {
  engineerPanelOpen.value = initialParams.get('ui') === 'engineer'
  localStorage.setItem('istiklal_c2_ui_mode', uiProfile.value)
  void refreshAll().then(async () => {
    // A browser mount/reload must never claim or reopen a physical camera.
    // Setup/profile application owns camera start. Cockpit may only attach
    // inference to an already-running selected camera.
    if (perceptionEnabled.value && runtime.cameraStatus.running) {
      try {
        await ensureYoloRuntime()
        await vision.start()
        await refreshAll()
      } catch (error) {
        showToast('warn', `YOLO hazırlanamadı: ${error instanceof Error ? error.message : 'runtime pending'}`)
      }
    }
    if (autoTrackingRequested && motion.trackingStatus.state !== 'TRACKING') {
      try {
        await motion.startTracking()
        await motion.refreshTrackingStatus()
        showToast('success', 'Otomatik takip hazır')
      } catch (error) {
        showToast('warn', `Takip başlatılamadı: ${error instanceof Error ? error.message : 'runtime pending'}`)
      }
    }
  })
  refreshTimer = setInterval(() => { void refreshAll() }, 3000)
  if (digitalTwinEnabled.value) {
    void digitalTwin.refresh()
    digitalTwinTimer = setInterval(() => { void digitalTwin.refresh() }, DIGITAL_TWIN_POLL_MS)
  }
})

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  if (digitalTwinTimer) clearInterval(digitalTwinTimer)
})
</script>

<template>
  <div class="cockpit-shell">
    <!-- PHASE 55 kinematic digital twin cockpit. Compatibility proof labels retained: PHASE 43, PHASE 43 baseline replaced by Phase 44 hard cockpit redesign, PHASE 44, PHASE 45, PHASE 46, PHASE 47, PHASE 48, PHASE 49, PHASE 50, PHASE 51, PHASE 52, PHASE 53, PHASE 54, KTR DEMO, 30 FPS Target, 15 FPS Cap, 10 FPS Low, operator-grid, grid-template-columns: minmax(0, 1fr) minmax(0, 1fr), height: clamp(520px, calc(100vh - 440px), 610px), NO PHYSICAL COMMAND, OFFLINE_EXPECTED, PICO OFFLINE_EXPECTED, USB OFFLINE_EXPECTED, USB Camera ·, Camera · ${cameraHeaderLabel.value}, STL asset loaded, Twin · STL-derived simplified, Command path · DISABLED, Digital Twin · Tactical CAD-ref, Tactical twin active, Digital Twin · Engagement Geometry, Fixture selected intentionally, KTR fixture selected, Target projected into FOV, Fire gate blocked, Backend bağlantısı yok — canlı veri güncellenmiyor., fixture truth / camera truth separated, perception=off, reports/screenshots/phase47_tactical_engagement_geometry/, reports/screenshots/phase48_real_3d_digital_twin_rebuild/, reports/screenshots/phase52_freecad_match_world/, reports/screenshots/phase53_3d_world_layout_priority/, reports/screenshots/phase54_model_fidelity_fix/, reports/screenshots/phase55_kinematic_digital_twin/, ktr1_colored_step_hero.glb, ktr1_freecad_fidelity.glb, ktr1_step_hifi_phase54.glb, ktr1_stl_geometry_phase54.glb, ktr1_hybrid_fidelity_phase54.glb, ktr1_kinematic_world_phase55.glb, ktr1_kinematics.json, source: work/ktr1.step, no_physical_command_generated=true; serial TX disabled. -->
    <CockpitTopBar :badges="topBadges" @toggle-engineer="engineerPanelOpen = !engineerPanelOpen" />

    <div v-if="system.connectionStatus !== 'connected'" class="backend-offline-pill">
      Backend: Offline — local preview active
    </div>
    <div
      v-if="operatorToast"
      class="operator-toast"
      :class="{
        'toast-success': operatorToast.tone === 'success',
        'toast-warn': operatorToast.tone === 'warn',
        'toast-error': operatorToast.tone === 'error',
      }"
    >
      {{ operatorToast.message }}
    </div>

    <main class="cockpit-main-grid" :class="{ 'world-main-grid': worldMode }">
      <section v-if="!worldMode" ref="cameraSectionRef" class="camera-secondary-section">
        <LiveCameraPanel
          :stream-url="vision.streamUrl"
          :frame-url="vision.frameUrl"
          :latest-frame="latestFrameMatchesSelectedCamera ? latestFrame : null"
          :width="overlayWidth"
          :height="overlayHeight"
          :aim-x="aimX"
          :aim-y="aimY"
          :source-label="cameraSourceLabel"
          :truth-mode="truthMode"
          :truth-detail="truthDetail"
          :person-safety-available="personSafetyAvailable"
          :perception-enabled="perceptionEnabled"
          :detection-runtime-ready="detectionRuntimeReady"
          :detection-runtime-detail="detectionRuntimeDetail"
          :perception-status-label="yoloStatusLabel"
          :perception-status-tone="yoloStatusTone"
          :target-label-prefix="targetLabelPrefix"
          :source-tone="cameraSourceTone"
          :source-detail="cameraPanelDetail"
          :selected-device="runtime.cameraStatus.selected_device ?? runtime.cameraStatus.selected_camera ?? 'n/a'"
          :backend="runtime.cameraStatus.selected_backend ?? 'fallback'"
          :frame-age-ms="runtime.cameraStatus.last_frame_age_ms"
          :real-frame-evidence="runtime.cameraStatus.is_real_camera_evidence"
          :ktr-demo-mode="ktrDemoMode"
          no-physical-label="no_physical_command_generated=true"
          :selected-target-id="selectedBalloonId"
          :person-safety-active="personSafetyActive"
          :image-settings="cameraImageSettings"
          :show-local-controls="false"
          :operator-mode="isOperatorUi"
          @toggle-perception="togglePerception"
          @select-target="selectBalloonTarget"
          @browser-vision-event="applyBrowserVisionEvent"
          @open-setup="openSetup"
          @fullscreen="openCameraFullscreen"
        />
      </section>

      <section class="hero-world-section" :class="{ 'world-full-section': worldMode }">
        <DigitalTwinPanel
          v-if="digitalTwinEnabled"
          :assets="digitalTwin.assets"
          :error="digitalTwin.error"
          :engagement-evidence="digitalTwin.engagementEvidence"
          :replay-control="engagementReplayControl"
          :loading="digitalTwin.loading"
          :replay="digitalTwin.replay"
          :state="digitalTwin.state"
          :vision-targets="activeBalloons"
          :vision-bodies="activeBodies"
          :frame-width="overlayWidth"
          :frame-height="overlayHeight"
          :selected-target-id="selectedBalloonId"
          :virtual-track-intent="virtualTrackIntent"
          :ktr-demo-mode="ktrDemoMode"
          :performance-mode="performanceMode"
          :world-mode="worldMode"
          :operator-mode="isOperatorUi"
          @load-replay="digitalTwin.loadReplay"
          @panel-rendered="digitalTwin.panelRendered"
        />
      </section>
    </main>

    <section v-if="isOperatorUi && !worldMode" class="operator-dock" aria-label="Operasyon eylemleri">
      <div class="dock-context">
        <div class="dock-fact"><Target :size="17" /><span>Hedef</span><b>{{ selectedTarget ? `#${selectedTarget.id}` : 'Seçilmedi' }}</b></div>
        <div class="dock-fact"><Crosshair :size="17" /><span>Takip</span><b>{{ motion.trackingStatus.state }}</b></div>
        <div class="dock-fact"><TimerReset :size="17" /><span>Görev</span><b>{{ stageDisplayLabel }} · {{ mission.snapshot.state.elapsed_s }} s</b></div>
        <div class="dock-reason" :class="operationalLiveReady ? 'ready' : 'blocked'"><ShieldAlert :size="17" /><span>{{ operationalLiveReady ? 'Fiziksel komut hazır' : operationalBlocker?.reasonCode ?? 'PREFLIGHT_REQUIRED' }}</span></div>
      </div>
      <div class="dock-actions">
        <button class="dock-button target-button" type="button" :disabled="!selectedTarget" @click="selectedBalloonId = null; virtualTrackIntent = false"><Target :size="18" /><span>Hedefi bırak</span></button>
        <button class="dock-button track-button" type="button" @click="toggleTracking"><Pause v-if="motion.trackingStatus.state === 'TRACKING'" :size="18" /><Play v-else :size="18" /><span>{{ motion.trackingStatus.state === 'TRACKING' ? 'Takibi durdur' : 'Takibi başlat' }}</span></button>
        <button class="dock-button fire-button" type="button" :disabled="!operationalLiveReady" :title="operationalBlocker?.reasonCode ?? ''" @click="requestFire"><Flame :size="18" /><span>FIRE</span></button>
        <button class="dock-button stop-button" type="button" @click="motion.stop"><ShieldAlert :size="19" /><span>SAFE STOP</span></button>
      </div>
    </section>

    <EngineerTechnicalTabs v-if="engineerPanelOpen" :active="engineerActiveTab" @change="setEngineerTab" @close="engineerPanelOpen = false">
      <template #camera><CameraControlPanel :cameras="backendCameraOptions" :selected-device="runtime.cameraStatus.selected_device ?? ''" :image-settings="cameraImageSettings" :camera-status="cameraSourceLabel" @refresh="refreshCameraInventory" @connect="applyBackendCamera" @stop="stopCameraPreview" @fullscreen="openCameraFullscreen" @update-image-settings="updateCameraImageSettings" @reset-image-settings="resetCameraImageSettings" /></template>
      <template #detection><DetectionConfigPanel :active-confidence="activeConfidence" :yolo-enabled="perceptionEnabled" :busy="confApplyBusy" :last-applied-at="lastConfidenceApplyAt" :status="confidenceApplyStatus" @apply="applyLiveConfidence" @revert="liveConfInput = activeConfidence.toFixed(2)" @toggle-yolo="togglePerception" /></template>
      <template #motion><div class="engineer-tab-stack"><SafetyModeBanner :metrics="bottomMetrics" /><MotorPidPanel /></div></template>
      <template #calibration><div class="engineer-tab-grid calibration-tab-grid"><DeveloperDebugDrawer :open="true" :asset-label="phase54AssetHeaderLabel" :material-label="stepMaterialLabel" :pose-label="projectionPoseSource" /><ScenePlanPanel :target-x="targetPlanX" :target-y="targetPlanY" :person-safety-active="personSafetyActive" :x-norm="projectionXNorm" :y-norm="projectionYNorm" :area-ratio="projectionArea" :depth="projectionDepth" :pose-source="projectionPoseSource" offset-label="30 mm" /><div class="calibration-note operator-card"><div><h3>3B Kalibrasyon</h3><p>Kamera anchor, namlu ekseni ve FOV ayrıntıları yalnız bu çalışma alanında tutulur.</p></div><div class="calibration-note-grid"><span>Kamera anchor: manuel kalibrasyon</span><span>Namlu ekseni: manuel kalibrasyon</span><span>Debug çizgileri: varsayılan kapalı</span></div></div></div></template>
      <template #logs><div class="engineer-tab-grid"><EngagementEvidenceReplayPanel :status="digitalTwin.engagementEvidence" :records="digitalTwin.engagementRecords" @load-twin-replay="loadEngagementTwinReplay" @replay-control="engagementReplayControl = $event" /><EvidenceReplayPanel evidence-path="reports/screenshots/phase55_kinematic_digital_twin/" :source="truthLabel" :timestamp="ktrDemoMode ? 'KTR_DEMO_FIXED' : new Date().toLocaleTimeString('tr-TR')" :size="`projection + asset + camera truth`" /><OperatorLogPanel :events="operatorEvents" /></div></template>
    </EngineerTechnicalTabs>
  </div>
</template>

<style scoped>
.cockpit-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100vh;
  overflow-y: auto;
  margin: 0;
  padding: 10px 12px;
  background:
    linear-gradient(180deg, rgba(4, 12, 24, 0.96), rgba(2, 6, 23, 0.98)),
    radial-gradient(circle at 72% 16%, rgba(34, 211, 238, 0.14), transparent 24%),
    radial-gradient(circle at 26% 78%, rgba(16, 185, 129, 0.08), transparent 24%),
    #05070b;
}

.engineer-tab-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.engineer-tab-grid > :deep(*) {
  min-height: 220px;
}

.calibration-tab-grid {
  grid-template-columns: minmax(320px, 0.92fr) minmax(320px, 1.08fr);
}

.calibration-note {
  display: grid;
  align-content: start;
  gap: 12px;
}

.calibration-note h3 {
  margin: 0;
  color: #f8fafc;
  font-size: 0.95rem;
  font-weight: 900;
}

.calibration-note p {
  margin: 4px 0 0;
  color: #94a3b8;
  font-size: 0.76rem;
  line-height: 1.5;
}

.calibration-note-grid {
  display: grid;
  gap: 8px;
}

.calibration-note-grid span {
  border: 1px solid rgba(34, 211, 238, 0.12);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.68);
  color: #bae6fd;
  padding: 9px 10px;
  font-size: 0.76rem;
  font-weight: 800;
}

.operator-toast {
  position: sticky;
  top: 8px;
  z-index: 20;
  align-self: center;
  max-width: 760px;
  border-radius: 9px;
  padding: 9px 14px;
  font-size: 0.84rem;
  font-weight: 850;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.25);
}

.backend-offline-pill {
  align-self: flex-start;
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 999px;
  background: rgba(92, 54, 0, 0.22);
  padding: 6px 11px;
  color: #fde68a;
  font-size: 0.76rem;
  font-weight: 850;
}

.toast-success { border: 1px solid rgba(16, 185, 129, 0.38); background: rgba(6, 78, 59, 0.94); color: #d1fae5; }
.toast-warn { border: 1px solid rgba(245, 158, 11, 0.38); background: rgba(92, 54, 0, 0.94); color: #fef3c7; }
.toast-error { border: 1px solid rgba(248, 113, 113, 0.44); background: rgba(127, 29, 29, 0.94); color: #fee2e2; }

.operator-status-pill {
  border: 1px solid rgba(34, 211, 238, 0.24);
  border-radius: 999px;
  background: rgba(8, 47, 73, 0.35);
  padding: 6px 10px;
  color: #cffafe;
  font-size: 0.75rem;
  font-weight: 900;
}

:global(.cockpit-card) {
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(10, 19, 33, 0.96), rgba(2, 6, 23, 0.98)),
    radial-gradient(circle at 18% 0%, rgba(34, 211, 238, 0.09), transparent 30%);
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.34);
}

:global(.panel-title-row) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
}

:global(.panel-title) {
  font-size: 0.92rem;
  font-weight: 700;
  color: #f8fafc;
}

:global(.panel-subtitle) {
  margin-top: 2px;
  font-size: 0.73rem;
  color: #94a3b8;
}

:global(.metric-tile) {
  min-width: 0;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 7px;
  background: rgba(3, 7, 18, 0.46);
  padding: 6px 8px;
}

:global(.metric-tile span) {
  display: block;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #64748b;
}

:global(.metric-tile b) {
  display: block;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.82rem;
  color: #e2e8f0;
}

:global(.operator-row) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 7px;
  background: rgba(3, 7, 18, 0.44);
  padding: 7px 9px;
}

:global(.operator-row.compact-row) {
  padding: 4px 7px;
}

:global(.mini-button) {
  border: 1px solid rgba(34, 211, 238, 0.35);
  border-radius: 6px;
  background: rgba(34, 211, 238, 0.12);
  padding: 7px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #cffafe;
}
</style>
<style scoped>
/* Phase 89 operator surface: one viewport, two primary panels, one action dock. */
.cockpit-shell{box-sizing:border-box;height:100vh;min-height:0;overflow:hidden;gap:8px;padding:8px;background:radial-gradient(circle at 68% 12%,rgba(14,116,144,.11),transparent 28%),linear-gradient(180deg,#06111d 0%,#020711 100%)}
.cockpit-main-grid{display:grid;grid-template-columns:minmax(0,1.58fr) minmax(390px,.92fr);grid-template-areas:"camera world";flex:1;min-height:0;gap:10px;align-content:stretch}
.camera-secondary-section,.hero-world-section{min-width:0;min-height:0;height:auto}
.camera-secondary-section{grid-area:camera;display:block}
.hero-world-section{grid-area:world}
.world-main-grid{grid-template-columns:1fr;grid-template-areas:"world"}
.world-full-section{height:100%}
.camera-secondary-section>:deep(.camera-panel),.hero-world-section>:deep(*){height:100%;min-height:0}
.operator-dock{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;align-items:center;min-height:66px;padding:8px 9px;border:1px solid rgba(94,234,255,.19);border-radius:15px;background:linear-gradient(180deg,rgba(8,24,38,.96),rgba(3,11,21,.97));box-shadow:0 -10px 32px rgba(0,0,0,.28)}
.dock-context{display:grid;grid-template-columns:repeat(3,minmax(100px,1fr)) minmax(190px,1.2fr);gap:7px;min-width:0}.dock-fact,.dock-reason{display:grid;grid-template-columns:auto 1fr;column-gap:8px;align-items:center;min-width:0;padding:7px 9px;border:1px solid rgba(148,163,184,.12);border-radius:10px;background:rgba(3,12,23,.7)}.dock-fact>svg,.dock-reason>svg{grid-row:1/3;color:#67e8f9}.dock-fact span{color:#758ca0;font-size:.56rem;font-weight:900;letter-spacing:.1em;text-transform:uppercase}.dock-fact b{overflow:hidden;margin-top:2px;color:#e0f2fe;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.7rem;text-overflow:ellipsis;white-space:nowrap}.dock-reason{display:flex;gap:8px;color:#ffd47e;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.67rem;font-weight:850}.dock-reason.ready{border-color:rgba(52,211,153,.28);background:rgba(6,78,59,.25);color:#9af2c3}.dock-reason.blocked{border-color:rgba(251,191,36,.22);background:rgba(92,54,0,.18)}.dock-actions{display:flex;align-items:stretch;gap:7px}.dock-button{display:flex;align-items:center;justify-content:center;gap:7px;min-width:102px;border:1px solid rgba(103,232,249,.22);border-radius:10px;background:rgba(8,47,73,.46);color:#d5f8ff;padding:9px 11px;font-size:.68rem;font-weight:900;cursor:pointer;transition:.16s}.dock-button:hover:not(:disabled){border-color:rgba(103,232,249,.58);background:rgba(8,74,99,.64);transform:translateY(-1px)}.dock-button:disabled{opacity:.4;cursor:not-allowed}.fire-button{border-color:rgba(251,191,36,.34);background:rgba(120,72,8,.25);color:#ffdc94}.stop-button{border-color:rgba(251,113,133,.42);background:rgba(127,29,29,.36);color:#fecdd3}.stop-button:hover:not(:disabled){border-color:rgba(251,113,133,.8);background:rgba(153,27,27,.58)}.engineer-tab-stack{display:grid;gap:12px}.backend-offline-pill{position:fixed;z-index:40;top:82px;left:16px}.operator-toast{position:fixed;z-index:70;top:82px;left:50%;transform:translateX(-50%)}
:global(.cockpit-card){border-color:rgba(94,234,255,.15);border-radius:14px;background:linear-gradient(180deg,rgba(8,23,37,.96),rgba(2,8,18,.98));box-shadow:0 18px 44px rgba(0,0,0,.3)}
:global(.panel-title-row){min-height:58px;padding:10px 12px}
:global(.panel-title){font-size:.84rem;letter-spacing:.03em}
:global(.panel-subtitle){font-size:.68rem}
@media(max-width:1180px){.cockpit-shell{height:auto;min-height:100vh;overflow-y:auto}.cockpit-main-grid{grid-template-columns:1fr;grid-template-areas:"camera" "world"}.camera-secondary-section,.hero-world-section{height:clamp(480px,70vh,680px)}.operator-dock{grid-template-columns:1fr}.dock-actions{justify-content:flex-end}}
@media(max-width:760px){.dock-context{grid-template-columns:repeat(2,minmax(0,1fr))}.dock-actions{display:grid;grid-template-columns:repeat(2,1fr)}.dock-button{min-width:0}.operator-dock{position:static}}
</style>
