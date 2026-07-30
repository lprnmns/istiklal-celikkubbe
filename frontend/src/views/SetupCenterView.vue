<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { connectGatewayPico, runCommandPreflight, selectCommandProfile, type CommandProfile } from '../api/safety'
import { discoverPico, stopHardwareMotion, testHardwareJog, testHardwareTrigger, testServoTune, type HardwareMotionTestResult } from '../api/hardware'
import { cameraOverlayStreamUrl, cameraStreamUrl, startCameraPreview, updateVisionConfig, uploadVisionModel } from '../api/vision'
import { resetSetupSession } from '../api/setupWizard'
import { applyVisionRuntimeSettings } from '../api/deviceRuntime'
import { saveDeviceProfile } from '../api/deviceProfiles'
import { useOperationalReadiness } from '../composables/useOperationalReadiness'
import { useDeviceRuntimeStore } from '../stores/deviceRuntimeStore'
import { useVisionStore } from '../stores/visionStore'
import type { ManagedDevice } from '../types/deviceRuntime'

type Step = 'hardware' | 'detection' | 'control'
const steps: Array<{ id: Step, title: string, subtitle: string }> = [
  { id: 'hardware', title: 'Donanım', subtitle: 'Kamera, Pico, E-Stop' },
  { id: 'detection', title: 'Algılama', subtitle: 'Kamera ve aktif model' },
  { id: 'control', title: 'Kontrol', subtitle: 'Yön ve tetik testi' },
]

const route = useRoute()
const router = useRouter()
const startupIntent = localStorage.getItem('istiklal_startup_intent') ?? localStorage.getItem('istiklal_c2_startup_intent')
const runtime = useDeviceRuntimeStore()
const vision = useVisionStore()
const readiness = useOperationalReadiness()
const readinessItems = readiness.items
const liveReady = readiness.liveReady
const activeStep = ref<Step>(
  route.query.step === 'detection'
    ? 'detection'
    : route.query.step === 'control' || route.query.step === 'preflight'
      ? 'control'
      : 'hardware',
)
const profile = ref<CommandProfile>(route.query.intent === 'live' || startupIntent === 'LIVE_HARDWARE' || startupIntent === 'TRACKING_TEST' ? 'LIVE_TEST' : 'DRY_RUN')
const requiresFireAuthority = computed(() => startupIntent === 'LIVE_HARDWARE')
const picoPort = ref('')
const baudrate = ref(460800)
const actuatorArm = ref(false)
const busy = ref(false)
const message = ref('')
const cameraDeviceId = ref('')
const motorTest = ref<HardwareMotionTestResult | null>(null)
const motorBusy = ref(false)
const triggerBusy = ref(false)
const triggerTest = ref<HardwareMotionTestResult | null>(null)
const picoScanBusy = ref(false)
const modelBusy = ref(false)
const modelConfig = reactive({
  balloonPath: '',
  balloonConfidence: 0.35,
  balloonEnabled: false,
  bodyPath: '',
  bodyConfidence: 0.35,
  bodyEnabled: false,
})
const modelMessage = ref('Model seçilmedi; kamera görüntüsü yine canlı kalır.')
const modelsInitialized = ref(false)
const servoConfig = reactive({ releaseDeg: 35, fireDeg: 175, pulseS: 1 })
const saveDialogOpen = ref(false)
const profileName = ref('')
const profileSaveBusy = ref(false)
const profileSaveError = ref('')

const currentIndex = computed(() => steps.findIndex((item) => item.id === activeStep.value))
const selectedCamera = computed(() => runtime.inventory.cameras.find((item) => item.device_id === cameraDeviceId.value) ?? null)
const isLive = computed(() => profile.value !== 'DRY_RUN')
const liveModelLabel = computed(() => {
  const active = [vision.visionStatus.balloon_model_loaded ? 'Balon modeli' : '', vision.visionStatus.body_model_loaded ? 'Hava aracı modeli' : ''].filter(Boolean)
  if (active.length) return `${active.join(' ve ')} yüklü ve etkin`
  return runtime.visionStatus.test_adapter_active ? 'Test algılayıcısı etkin' : 'Model yüklenmemiş'
})
const canContinue = computed(() => {
  if (activeStep.value === 'hardware') return !isLive.value || readinessItems.value.find((item) => item.key === 'pico_estop')?.state === 'READY'
  if (activeStep.value === 'detection') return !isLive.value || readinessItems.value.find((item) => item.key === 'camera')?.state === 'READY'
  return !isLive.value || (requiresFireAuthority.value ? liveReady.value : readiness.preflight.value?.physical_motion_enabled === true)
})
const blocker = computed(() => readiness.primaryBlocker.value)
const canPhysicalJog = computed(() => isLive.value && readiness.preflight.value?.physical_motion_enabled === true)
const canPhysicalTrigger = computed(() => isLive.value && readiness.preflight.value?.physical_fire_enabled === true)

async function withTimeout<T>(promise: Promise<T>, label: string, timeoutMs = 7000): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined
  try {
    return await Promise.race([
      promise,
      new Promise<T>((_, reject) => {
        timer = setTimeout(() => reject(new Error(`${label} ${Math.round(timeoutMs / 1000)} sn içinde yanıt vermedi.`)), timeoutMs)
      }),
    ])
  } finally {
    if (timer) clearTimeout(timer)
  }
}

function cameraSourceTypeFor(camera: ManagedDevice): 'laptop' | 'usb' {
  return /usb|external|hd camera/i.test(`${camera.name} ${camera.description} ${camera.device_path}`) ? 'usb' : 'laptop'
}
async function refresh(): Promise<void> {
  // Cihaz taraması runtime/vision ayarlarından bağımsızdır. Böylece ağır bir
  // model endpointi gecikse dahi bağlı kamera ve Pico listesi görünür kalır.
  await withTimeout(runtime.refreshInventory(), 'Cihaz taraması', 5000)
  void readiness.refresh().catch(() => undefined)
  // A fresh setup session intentionally makes no device choice for the user.
  if (!cameraDeviceId.value && runtime.cameraStatus.selected_device) cameraDeviceId.value = runtime.cameraStatus.selected_device
  if (!modelConfig.balloonPath) modelConfig.balloonPath = vision.visionStatus.balloon_model_path ?? ''
  if (!modelConfig.bodyPath) modelConfig.bodyPath = vision.visionStatus.body_model_path ?? ''
  if (!modelsInitialized.value) {
    modelConfig.balloonEnabled = Boolean(modelConfig.balloonPath)
    modelConfig.bodyEnabled = Boolean(modelConfig.bodyPath)
    modelsInitialized.value = true
  }
}
async function applyCamera(): Promise<void> {
  const camera = selectedCamera.value
  if (!camera) { message.value = 'Önce bir kamera seçin.'; return }
  busy.value = true; message.value = ''
  try {
    runtime.cameraDraft = { ...runtime.cameraStatus.profile, source_type: cameraSourceTypeFor(camera), device_id: camera.device_id, device_path: camera.device_path, stable_path: camera.stable_path, width: 640, height: 360, fps: 30, pixel_format: 'MJPG', stream_width: 640, stream_height: 360, inference_width: 640, inference_height: 360, roi: { ...runtime.cameraStatus.profile.roi } }
    await withTimeout(runtime.applyCamera(), 'Kamera uygulaması')
    await withTimeout(startCameraPreview(), 'Kamera önizlemesi başlatma', 5000)
    await runtime.refresh()
    // Force the browser to replace any stale MJPEG connection left by a
    // previous camera profile instead of retaining an empty stream frame.
    vision.streamUrl = `${cameraStreamUrl()}?session=${Date.now()}`
    message.value = 'Kamera önizlemesi hazır. Algılama, model etkinleştirildiğinde başlar.'
    void refresh().catch(() => undefined)
  } catch (caught) { message.value = caught instanceof Error ? caught.message : 'Kamera uygulanamadı.' } finally { busy.value = false }
}
async function connectPico(): Promise<void> {
  if (!picoPort.value) { message.value = 'Pico portu seçilmedi.'; return }
  busy.value = true; message.value = ''
  try {
    const result = await withTimeout(connectGatewayPico(picoPort.value, baudrate.value), 'Pico bağlantısı')
    readiness.preflight.value = result.preflight
    if (!result.connected) message.value = result.reason_code
    else { await runPreflight(false); message.value = 'Pico bağlandı; handshake ve E-Stop kontrol edildi.' }
    void refresh().catch(() => undefined)
  } catch (caught) { message.value = caught instanceof Error ? caught.message : 'Pico bağlantısı açılamadı.' } finally { busy.value = false }
}
async function findPico(): Promise<void> {
  picoScanBusy.value = true
  message.value = ''
  try {
    const result = await withTimeout(discoverPico(), 'Pico taraması', 5500)
    if (result.found && result.port) { picoPort.value = result.port; baudrate.value = result.baudrate; message.value = result.detail }
    else message.value = `${result.reason_code}: ${result.detail}`
  } catch (caught) { message.value = caught instanceof Error ? caught.message : 'Pico taraması yapılamadı.' } finally { picoScanBusy.value = false }
}
async function applyModels(): Promise<void> {
  modelBusy.value = true
  message.value = ''
  try {
    if (modelConfig.balloonEnabled && !modelConfig.balloonPath) throw new Error('BALLOON_MODEL_PATH_REQUIRED')
    if (modelConfig.bodyEnabled && !modelConfig.bodyPath) throw new Error('BODY_MODEL_PATH_REQUIRED')
    await withTimeout(updateVisionConfig({
      vision_mode: 'ultralytics_yolo',
      body_model_path: modelConfig.bodyEnabled && modelConfig.bodyPath ? modelConfig.bodyPath : null,
      balloon_model_path: modelConfig.balloonEnabled && modelConfig.balloonPath ? modelConfig.balloonPath : null,
      body_conf_threshold: modelConfig.bodyConfidence,
      balloon_conf_threshold: modelConfig.balloonConfidence,
    }), 'Model ayarı uygulama')
    const runtimeProfile = runtime.visionStatus.profile
    const runtimeResult = await withTimeout(applyVisionRuntimeSettings({
      ...runtimeProfile,
      // The tested legacy dost/dusman model needs 1280 px to resolve a
      // balloon displayed on a phone screen at this camera distance.
      imgsz: modelConfig.balloonEnabled ? 1280 : runtimeProfile.imgsz,
      conf: Math.min(modelConfig.balloonConfidence, modelConfig.bodyConfidence),
      balloon_conf_threshold: modelConfig.balloonConfidence,
      body_conf_threshold: modelConfig.bodyConfidence,
    }), 'Canlı model ayarı')
    runtime.visionStatus = runtimeResult.status
    await withTimeout(vision.start(), 'Kamera akışı başlatma', 7000)
    const enabled = [modelConfig.balloonEnabled ? 'Balon' : '', modelConfig.bodyEnabled ? 'Hava aracı' : ''].filter(Boolean)
    modelMessage.value = enabled.length ? `${enabled.join(' ve ')} modeli canlı görüntüye uygulandı.` : 'Her iki model pasif; yalnız kamera görüntüsü açık.'
  } catch (caught) { modelMessage.value = caught instanceof Error ? caught.message : 'Model ayarları uygulanamadı.' } finally { modelBusy.value = false }
}
async function chooseModel(kind: 'balloon' | 'body', event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  modelBusy.value = true
  modelMessage.value = `${file.name} yükleniyor…`
  try {
    const uploaded = await uploadVisionModel(file)
    if (kind === 'balloon') { modelConfig.balloonPath = uploaded.path; modelConfig.balloonEnabled = true }
    else { modelConfig.bodyPath = uploaded.path; modelConfig.bodyEnabled = true }
    await applyModels()
  } catch (caught) { modelMessage.value = caught instanceof Error ? caught.message : 'Model dosyası yüklenemedi.' } finally { modelBusy.value = false; input.value = '' }
}
async function runPreflight(arm = actuatorArm.value): Promise<void> {
  busy.value = true; message.value = ''
  try {
    readiness.preflight.value = await withTimeout(runCommandPreflight(arm), 'Ön kontrol')
    actuatorArm.value = readiness.preflight.value.actuator_armed
    message.value = readiness.preflight.value.ready ? 'Preflight hazır.' : readiness.preflight.value.reason_codes.join(' · ')
    void refresh().catch(() => undefined)
  } catch (caught) { message.value = caught instanceof Error ? caught.message : 'Preflight çalıştırılamadı.' } finally { busy.value = false }
}
async function runMotorTest(speedX: number, speedY: number): Promise<void> {
  motorBusy.value = true
  motorTest.value = null
  try {
    motorTest.value = await testHardwareJog({ speed_x: speedX, speed_y: speedY, duration_ms: 350 })
    await refresh()
  } catch (caught) {
    message.value = caught instanceof Error ? caught.message : 'Hareket testi gönderilemedi.'
  } finally { motorBusy.value = false }
}
async function stopMotorTest(): Promise<void> {
  motorBusy.value = true
  try { motorTest.value = await stopHardwareMotion(); await refresh() } catch (caught) { message.value = caught instanceof Error ? caught.message : 'Güvenli durdurma gönderilemedi.' } finally { motorBusy.value = false }
}
async function applyServoConfig(): Promise<void> {
  triggerBusy.value = true; triggerTest.value = null
  try { triggerTest.value = await testServoTune({ release_deg: servoConfig.releaseDeg, fire_deg: servoConfig.fireDeg, pulse_s: servoConfig.pulseS }) }
  catch (caught) { message.value = caught instanceof Error ? caught.message : 'Servo ayarı gönderilemedi.' }
  finally { triggerBusy.value = false }
}
async function runTriggerTest(): Promise<void> {
  triggerBusy.value = true; triggerTest.value = null
  try { triggerTest.value = await testHardwareTrigger() }
  catch (caught) { message.value = caught instanceof Error ? caught.message : 'Tetik testi gönderilemedi.' }
  finally { triggerBusy.value = false }
}
function next(): void { const step = steps[currentIndex.value + 1]; if (step && canContinue.value) activeStep.value = step.id }
async function continueStep(): Promise<void> {
  next()
}
function previous(): void { const step = steps[currentIndex.value - 1]; if (step) activeStep.value = step.id }
function finishSetup(): void {
  profileSaveError.value = ''
  if (!profileName.value.trim()) profileName.value = `Kurulum ${new Date().toLocaleDateString('tr-TR')}`
  saveDialogOpen.value = true
}
async function confirmProfileSave(): Promise<void> {
  const displayName = profileName.value.trim()
  if (!displayName) { profileSaveError.value = 'Profil adı gerekli.'; return }
  profileSaveBusy.value = true
  profileSaveError.value = ''
  try {
    const result = await saveDeviceProfile({
      display_name: displayName,
      command_profile: profile.value,
      servo_release_deg: servoConfig.releaseDeg,
      servo_fire_deg: servoConfig.fireDeg,
      servo_pulse_s: servoConfig.pulseS,
    })
    localStorage.setItem('istiklal_active_profile_id', result.profile.profile_id)
    saveDialogOpen.value = false
    await router.replace('/')
  } catch (caught) {
    profileSaveError.value = caught instanceof Error ? caught.message : 'Profil kaydedilemedi.'
  } finally {
    profileSaveBusy.value = false
  }
}
onMounted(() => {
  // Landing chunk is prefetched while Setup is open so "Kaydet ve çık"
  // navigation is immediate even on the Raspberry Pi / packaged build.
  void import('./LandingView.vue')
  vision.streamUrl = cameraStreamUrl()
  void resetSetupSession().then(async () => {
    // Entering or refreshing Setup preserves the active camera/model/Pico
    // bindings.  Only physical preflight/arm state is invalidated server-side.
    // Re-apply the visible command intent; LIVE still needs an explicit arm.
    readiness.preflight.value = await selectCommandProfile(profile.value, false)
    await vision.refresh()
    await refresh()
  }).catch(() => refresh())
})
watch(activeStep, (step) => { vision.streamUrl = step === 'detection' ? cameraOverlayStreamUrl() : cameraStreamUrl() })
</script>

<template>
  <main class="setup-page">
    <header class="setup-header"><div><p class="eyebrow">İSTİKLAL</p><h1>Sistem kurulumu</h1><p>Yalnız gerekli adımları tamamla; teknik ayrıntılar Mühendis Panelinde kalır.</p></div><div class="header-buttons"><button class="ghost-header" type="button" @click="router.push('/')">Başlangıç ekranı</button><button class="secondary" type="button" :disabled="busy" @click="refresh">{{ busy ? 'Kontrol ediliyor…' : 'Yeniden tara' }}</button></div></header>
    <nav class="steps" aria-label="Kurulum adımları"><button v-for="(step,index) in steps" :key="step.id" type="button" :class="{ active: activeStep === step.id, done: index < currentIndex }" @click="activeStep = step.id"><span>{{ index + 1 }}</span><b>{{ step.title }}</b><small>{{ step.subtitle }}</small></button></nav>
    <section class="panel">
      <template v-if="activeStep === 'hardware'">
        <p class="eyebrow">1 · DONANIM</p><h2>Kamera, Pico ve Acil Durdurma</h2><div class="two-col"><article class="device-card"><h3>Kamera</h3><select v-model="cameraDeviceId"><option value="">Kamera seç</option><option v-for="camera in runtime.inventory.cameras" :key="camera.device_id" :value="camera.device_id">{{ camera.description || camera.name }} · {{ camera.device_path }}</option></select><p v-if="selectedCamera"><b>{{ selectedCamera.description || selectedCamera.name }}</b><br><small>{{ selectedCamera.device_path }} · {{ selectedCamera.stable_path ?? 'kalıcı cihaz yolu yok' }}</small></p><p>{{ readinessItems.find(item => item.key === 'camera')?.message }}</p><code>{{ readinessItems.find(item => item.key === 'camera')?.reasonCode ?? 'CAMERA_READY' }}</code><img v-if="runtime.cameraStatus.running" :src="vision.streamUrl" alt="Canlı kamera önizlemesi"><div class="card-actions"><button class="secondary" type="button" :disabled="busy" @click="applyCamera">Seçili kamerayı uygula</button><button class="secondary" type="button" :disabled="busy" @click="refresh">Kameraları tara</button></div></article><article class="device-card"><h3>Pico + Acil Durdurma</h3><select v-model="picoPort"><option value="">Pico portu seç</option><option v-for="device in runtime.inventory.pico_candidates" :key="device.device_path" :value="device.device_path">{{ device.description || device.name }} · {{ device.device_path }}</option></select><label>Baudrate <input v-model.number="baudrate" type="number" min="1200"></label><p>{{ readinessItems.find(item => item.key === 'pico_estop')?.message }}</p><code>{{ readinessItems.find(item => item.key === 'pico_estop')?.reasonCode ?? 'PICO_ESTOP_READY' }}</code><div class="card-actions"><button class="secondary" type="button" :disabled="picoScanBusy" @click="findPico">{{ picoScanBusy ? 'Pico aranıyor…' : 'Pico ara (5 sn)' }}</button><button class="secondary" type="button" :disabled="busy || !isLive || !picoPort" @click="connectPico">Pico'yu bağla ve doğrula</button></div><small v-if="!isLive">Test modunda Pico zorunlu değildir.</small><small v-else-if="!runtime.inventory.pico_candidates.length">Doğrulanmış Pico bulunmadı; kartı bağladıktan sonra Pico ara seç.</small></article></div>
      </template>
      <template v-else-if="activeStep === 'detection'">
        <p class="eyebrow">2 · ALGILAMA</p><h2>Modeller ve canlı görüntü</h2>
        <article class="device-card model-card new-model-card"><h3>Algılama modelleri</h3><p class="model-help">İki model zorunlu değildir. Etkin olan model canlı akışa otomatik uygulanır.</p><section class="model-row"><div class="model-row-head"><b>Balon modeli</b><label class="switch"><input v-model="modelConfig.balloonEnabled" type="checkbox" @change="applyModels"><span></span><em>{{ modelConfig.balloonEnabled ? 'Etkin' : 'Pasif' }}</em></label></div><label>Dosya yolu<input v-model="modelConfig.balloonPath" placeholder="/yol/balon_modeli.pt" :disabled="!modelConfig.balloonEnabled" @blur="applyModels"></label><label class="file-picker"><input type="file" accept=".pt,.onnx,.engine" @change="chooseModel('balloon', $event)"><span>.pt dosyası seç</span></label><label>Güven eşiği {{ modelConfig.balloonConfidence.toFixed(3) }}<input v-model.number="modelConfig.balloonConfidence" type="range" min="0.001" max="0.99" step="0.001" :disabled="!modelConfig.balloonEnabled" @change="applyModels"></label></section><section class="model-row"><div class="model-row-head"><b>Hava aracı modeli</b><label class="switch"><input v-model="modelConfig.bodyEnabled" type="checkbox" @change="applyModels"><span></span><em>{{ modelConfig.bodyEnabled ? 'Etkin' : 'Pasif' }}</em></label></div><label>Dosya yolu<input v-model="modelConfig.bodyPath" placeholder="/yol/hava_araci_modeli.pt" :disabled="!modelConfig.bodyEnabled" @blur="applyModels"></label><label class="file-picker"><input type="file" accept=".pt,.onnx,.engine" @change="chooseModel('body', $event)"><span>.pt dosyası seç</span></label><label>Güven eşiği {{ modelConfig.bodyConfidence.toFixed(3) }}<input v-model.number="modelConfig.bodyConfidence" type="range" min="0.001" max="0.99" step="0.001" :disabled="!modelConfig.bodyEnabled" @change="applyModels"></label></section><p class="model-message" :class="{ error: modelMessage.includes('uygulanamadı') || modelMessage.includes('yüklenemedi') }">{{ modelBusy ? 'Model ayarı güncelleniyor…' : modelMessage }}</p><img v-if="runtime.cameraStatus.running" class="model-preview" :src="vision.streamUrl" alt="Canlı kamera önizlemesi"><p>{{ liveModelLabel }}</p></article>
      </template>
      <template v-else>
        <p class="eyebrow">3 · KONTROL</p><h2>Taret yön ve tetik testleri</h2>
        <label v-if="isLive" class="arm"><input v-model="actuatorArm" type="checkbox" :disabled="busy" @change="runPreflight(actuatorArm)"> Fiziksel testler için aktüatörü hazırla</label>
        <div class="control-grid">
          <article class="device-card motion-card"><h3>Taret yön testi</h3><p>{{ readinessItems.find(item => item.key === 'motion_actuator')?.message }}</p><code>{{ canPhysicalJog ? 'GATEWAY_MOTION_READY' : readinessItems.find(item => item.key === 'motion_actuator')?.reasonCode ?? 'PREFLIGHT_REQUIRED' }}</code><div class="jog-grid"><button type="button" :disabled="motorBusy" @click="runMotorTest(-140,0)">← Sol</button><button type="button" :disabled="motorBusy" @click="runMotorTest(140,0)">Sağ →</button><button type="button" :disabled="motorBusy" @click="runMotorTest(0,140)">↑ Yukarı</button><button type="button" :disabled="motorBusy" @click="runMotorTest(0,-140)">Aşağı ↓</button></div><button class="stop-test" type="button" :disabled="motorBusy" @click="stopMotorTest">Güvenli durdur</button><div v-if="motorTest" class="command-result"><b>{{ motorTest.accepted ? 'KOMUT KABUL EDİLDİ' : 'KOMUT ENGELLENDİ' }}</b><span>Gönderildi: {{ motorTest.command_sent ? 'EVET' : 'HAYIR' }} · Komut: {{ motorTest.command ?? 'yok' }}</span><span>Pico yanıtı: {{ motorTest.pico_response ?? 'yanıt yok' }}</span><span>Sürücü ACK: {{ motorTest.driver_ack ?? 'yok' }}</span><span>Durdurma: {{ motorTest.safe_stop_response ?? 'bekleniyor' }}</span><code v-if="motorTest.reason_codes.length">{{ motorTest.reason_codes.join(' · ') }}</code></div><p v-else-if="!canPhysicalJog">Komut Gateway'e gönderilir; eksik koşul varsa hareket etmeden reason code gösterilir.</p></article>
          <article class="device-card trigger-card"><h3>Taret tetik testi</h3><p>Boş haznede hava atışı için önce başlangıç ve ateş açılarını ayarla. Komut, normal Gateway güvenlik kontrollerinden geçer.</p><div class="servo-inputs"><label>Başlangıç açısı<input v-model.number="servoConfig.releaseDeg" type="number" min="0" max="179">°</label><label>Ateş açısı<input v-model.number="servoConfig.fireDeg" type="number" min="1" max="180">°</label></div><button class="secondary" type="button" :disabled="triggerBusy" @click="applyServoConfig">Açıları Pico'ya uygula</button><button class="trigger-test" type="button" :disabled="triggerBusy" @click="runTriggerTest">Tetiği test et (boş hazne)</button><div v-if="triggerTest" class="command-result"><b>{{ triggerTest.accepted ? 'TETİK KOMUTU KABUL EDİLDİ' : 'TETİK KOMUTU ENGELLENDİ' }}</b><span>Gönderildi: {{ triggerTest.command_sent ? 'EVET' : 'HAYIR' }} · Komut: {{ triggerTest.command ?? 'yok' }}</span><span>Pico yanıtı: {{ triggerTest.pico_response ?? 'yanıt yok' }}</span><span>ACK: {{ triggerTest.driver_ack ?? 'yok' }}</span><code v-if="triggerTest.reason_codes.length">{{ triggerTest.reason_codes.join(' · ') }}</code></div><p v-else-if="!canPhysicalTrigger">Komut Gateway'e gönderilir; Canlı mod, Pico, kamera, E‑Stop veya arm eksikse fiziksel çıkış üretmeden reason code gösterilir.</p></article>
        </div>
        <div class="finish-actions"><button class="primary compact" type="button" :disabled="busy || motorBusy || triggerBusy" @click="finishSetup">Kaydet ve çık</button></div>
      </template>
      <p v-if="message" class="message">{{ message }}</p>
    </section>
    <footer class="footer"><button class="ghost" type="button" :disabled="currentIndex === 0" @click="previous">Geri</button><div v-if="activeStep !== 'control'"><span v-if="!canContinue && blocker">Devam için: <code>{{ blocker.reasonCode }}</code></span><button class="primary compact" type="button" :disabled="busy || !canContinue" @click="continueStep">{{ busy ? 'Uygulanıyor…' : 'Devam et' }}</button></div></footer>
    <div v-if="saveDialogOpen" class="modal-backdrop" role="presentation" @click.self="!profileSaveBusy && (saveDialogOpen = false)">
      <form class="profile-modal" role="dialog" aria-modal="true" aria-labelledby="profile-save-title" @submit.prevent="confirmProfileSave">
        <p class="eyebrow">KURULUM PROFİLİ</p>
        <h2 id="profile-save-title">Bu ayarları kaydet</h2>
        <p>Kamera, algılama modelleri, güven eşikleri ve taret test ayarları bu adla saklanacak.</p>
        <label>Profil adı<input v-model="profileName" maxlength="80" autocomplete="off" autofocus placeholder="Örn. Laptop kamera testi"></label>
        <p v-if="profileSaveError" class="modal-error">{{ profileSaveError }}</p>
        <div class="modal-actions"><button class="ghost" type="button" :disabled="profileSaveBusy" @click="saveDialogOpen = false">Vazgeç</button><button class="primary compact" type="submit" :disabled="profileSaveBusy || !profileName.trim()">{{ profileSaveBusy ? 'Kaydediliyor…' : 'Profili kaydet ve çık' }}</button></div>
      </form>
    </div>
  </main>
</template>

<style scoped>
.setup-page{min-height:100vh;background:linear-gradient(145deg,#07121f,#060a12 58%);color:#eaf4fb;padding:clamp(20px,4vw,56px);font-family:Inter,ui-sans-serif,system-ui}.setup-header{display:flex;justify-content:space-between;gap:24px;align-items:flex-start;max-width:1180px;margin:auto}.header-buttons{display:flex;gap:9px}.eyebrow{margin:0;color:#5ce7fb;font-size:.7rem;font-weight:900;letter-spacing:.22em}.setup-header h1{margin:6px 0;font-size:clamp(1.8rem,3vw,2.8rem)}.setup-header p{margin:0;color:#9db0c0}.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;max-width:1180px;margin:32px auto 16px}.steps button{display:grid;grid-template-columns:28px 1fr;column-gap:9px;align-items:center;padding:13px;border:1px solid #ffffff1a;border-radius:12px;background:#0b1725;color:#a5b5c3;text-align:left}.steps span{grid-row:span 2;display:grid;place-items:center;width:25px;height:25px;border-radius:50%;background:#1d3143;color:#d5edf8;font-weight:900}.steps b{font-size:.82rem}.steps small{font-size:.66rem}.steps .active{border-color:#55dff7;background:#0d2838;color:#effcff}.steps .done span{background:#37c98b;color:#00140d}.panel{max-width:1180px;min-height:440px;margin:auto;padding:clamp(22px,4vw,44px);border:1px solid #61cae535;border-radius:20px;background:#07121fd9;box-shadow:0 22px 65px #0008}.panel h2{margin:7px 0 24px;font-size:clamp(1.4rem,2.5vw,2.15rem)}.two-col,.control-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.device-card{display:grid;gap:10px;min-height:145px;padding:20px;border:1px solid #ffffff1a;border-radius:14px;background:#091a2a;color:#e9f5fb;text-align:left}.device-card p,.device-card small{color:#adc1d0;line-height:1.5}.device-card select,.device-card input{width:100%;box-sizing:border-box;border:1px solid #ffffff25;border-radius:8px;background:#020811;color:#eaf7ff;padding:10px}.device-card label{display:grid;gap:5px;color:#a9bdcc;font-size:.78rem}.device-card img{width:100%;max-height:160px;object-fit:cover;border-radius:9px;background:#02060c}.card-actions,.servo-inputs{display:flex;flex-wrap:wrap;gap:8px}.servo-inputs label{flex:1;min-width:120px}.primary,.secondary,.ghost,.ghost-header,.trigger-test{border-radius:10px;padding:11px 14px;font-weight:900;cursor:pointer;transition:border-color .16s,background .16s,transform .16s}.primary{border:0;background:#49d8d0;color:#012127}.primary:hover:not(:disabled),.secondary:hover:not(:disabled),.ghost:hover:not(:disabled),.ghost-header:hover:not(:disabled),.trigger-test:hover:not(:disabled),.jog-grid button:hover:not(:disabled),.stop-test:hover:not(:disabled){transform:translateY(-1px);filter:brightness(1.12)}.primary:not(.compact){margin-top:22px;min-width:220px}.secondary{border:1px solid #63dff655;background:#0a2536;color:#c7f6ff}.trigger-test{border:1px solid #f7a65c;background:#512612;color:#fff0df}.ghost,.ghost-header{border:1px solid #ffffff1d;background:transparent;color:#b7cedb}.footer{display:flex;justify-content:space-between;align-items:center;max-width:1180px;margin:16px auto}.footer span{margin-right:12px;color:#f9c36d;font-size:.78rem}.compact{padding:10px 18px}.message{margin-top:20px;color:#ffd07e}.arm{display:flex;gap:9px;align-items:center;margin:0 0 18px;padding:13px 15px;border:1px solid #53dca044;border-radius:10px;background:#09261f;color:#e8f8ff}.arm input{width:auto}.device-card code{color:#ffd27b;font-size:.67rem}.jog-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}.jog-grid button,.stop-test{border:1px solid #59dced55;border-radius:8px;background:#0b2636;color:#d9f9ff;padding:9px;font-weight:900;cursor:pointer;transition:.16s}.jog-grid button:disabled,.stop-test:disabled,.trigger-test:disabled,.primary:disabled,.secondary:disabled{opacity:.45;cursor:not-allowed}.stop-test{border-color:#ef777755;background:#3a171b;color:#ffd4d7}.command-result{display:grid;gap:4px;padding:10px;border:1px solid #54dba344;border-radius:9px;background:#07302166}.command-result b{color:#7df0ae;font-size:.74rem}.command-result span,.command-result code{font-family:ui-monospace,monospace;font-size:.66rem;color:#c0d3dd}.new-model-card{grid-template-columns:repeat(2,minmax(0,1fr));align-items:start}.new-model-card h3,.new-model-card>.model-help,.new-model-card>.model-message,.new-model-card>.model-preview,.new-model-card>p:last-child{grid-column:1/-1}.model-help{margin:0}.model-row{display:grid;gap:9px;padding:14px;border:1px solid #ffffff15;border-radius:10px;background:#061421}.model-row-head{display:flex;align-items:center;justify-content:space-between}.switch{display:flex!important;grid-template-columns:auto 1fr;align-items:center;gap:7px!important}.switch input{position:absolute;opacity:0;pointer-events:none}.switch span{width:30px;height:17px;border-radius:99px;background:#4b6070;position:relative}.switch span:after{content:'';position:absolute;width:13px;height:13px;left:2px;top:2px;border-radius:50%;background:#fff;transition:.16s}.switch input:checked+span{background:#31c998}.switch input:checked+span:after{transform:translateX(13px)}.switch em{font-style:normal;font-size:.68rem}.file-picker{position:relative;display:block!important;border:1px dashed #55dff766;border-radius:8px;padding:9px!important;text-align:center;color:#bceefa!important;cursor:pointer}.file-picker input{position:absolute;inset:0;opacity:0;cursor:pointer}.model-message{margin:0;padding:9px 12px;border-left:3px solid #4ed7df;background:#082430;color:#c7eaf0}.model-message.error{border-left-color:#ff7d8b;color:#ffd2d8}.model-preview{width:100%;max-height:560px!important;object-fit:cover}.finish-actions{display:flex;justify-content:flex-end;margin-top:20px}.finish-actions .primary{min-width:190px}.modal-backdrop{position:fixed;inset:0;z-index:50;display:grid;place-items:center;padding:20px;background:#01050bd9;backdrop-filter:blur(8px)}.profile-modal{width:min(470px,100%);padding:26px;border:1px solid #59ddf35c;border-radius:18px;background:#081725;box-shadow:0 28px 90px #000}.profile-modal h2{margin:7px 0 10px}.profile-modal>p:not(.eyebrow):not(.modal-error){color:#a9bdcc;line-height:1.55}.profile-modal label{display:grid;gap:7px;margin-top:20px;color:#c9dce7;font-size:.78rem;font-weight:800}.profile-modal input{width:100%;box-sizing:border-box;border:1px solid #62dff65c;border-radius:9px;background:#020811;color:#effcff;padding:12px}.modal-actions{display:flex;justify-content:flex-end;gap:9px;margin-top:22px}.modal-error{color:#ff9ca4;font-size:.78rem}@media(max-width:760px){.setup-page{padding:20px}.setup-header{display:grid}.steps,.two-col,.control-grid,.new-model-card{grid-template-columns:1fr}.steps button small{display:none}.footer{align-items:flex-end}.panel{min-height:0}.modal-actions{display:grid}.modal-actions button{width:100%}}
</style>
<style scoped>
/* Kurulum alanı geniş ekranlarda rahat okunur; adımlar birbirine sıkışmaz. */
.setup-header,.steps,.panel,.footer{max-width:1420px}.panel{min-height:520px}.panel>.two-col>.device-card{min-height:400px}.panel>.two-col>.device-card:first-child>img{max-height:360px;height:360px;object-fit:cover}.new-model-card{margin:0}
</style>
