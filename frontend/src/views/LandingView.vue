<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { runCommandPreflight, selectCommandProfile, type GatewayPreflightResult } from '../api/safety'
import { applyDeviceProfile, fetchDeviceProfiles } from '../api/deviceProfiles'
import { useOperationalReadiness, type OperationalReadinessItem } from '../composables/useOperationalReadiness'
import type { DeviceProfile } from '../types/deviceProfile'

type StartupMode = 'TRACKING_TEST' | 'LIVE_HARDWARE'

const router = useRouter()
const readiness = useOperationalReadiness()
const readinessItems = readiness.items
const readinessLoading = readiness.loading
const readinessError = readiness.error
const primaryBlocker = readiness.primaryBlocker
const selectedMode = ref<StartupMode>('TRACKING_TEST')
const busy = ref(false)
const feedback = ref('')
const profiles = ref<DeviceProfile[]>([])
const profilesLoading = ref(false)
const selectedProfileId = ref(localStorage.getItem('istiklal_active_profile_id') ?? '')
const startupPreflight = ref<GatewayPreflightResult | null>(null)
const startupWarnings = ref<string[]>([])
const now = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null
let refreshTimer: ReturnType<typeof setInterval> | null = null

const timeLabel = computed(() => now.value.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
const modeTitle = computed(() => selectedMode.value === 'TRACKING_TEST' ? 'Test sistemini hazırla' : 'Canlı sistemi hazırla')
const selectedProfile = computed(() => profiles.value.find((item) => item.profile_id === selectedProfileId.value) ?? null)
const profileSummary = computed(() => {
  const current = selectedProfile.value
  if (!current) return 'Profil seçilmedi; mevcut çalışma ayarları kullanılacak.'
  const camera = current.selected_camera_name || current.camera_profile?.device_id || 'Kamera bekleniyor'
  const balloon = current.vision_config?.balloon_model_path?.split(/[\\/]/).pop() || 'Balon modeli kapalı'
  const body = current.vision_config?.body_model_path?.split(/[\\/]/).pop() || 'Hava aracı modeli kapalı'
  return `${camera} · ${balloon} · ${body}`
})

function selectMode(mode: StartupMode): void {
  selectedMode.value = mode
  feedback.value = ''
  startupPreflight.value = null
  startupWarnings.value = []
}

function openFix(item: OperationalReadinessItem): void {
  if (item.action === 'refresh') {
    void readiness.refresh()
    return
  }
  const step = item.action === 'setup-camera' ? 'hardware' : item.action === 'setup-pico' ? 'hardware' : 'control'
  void router.push(`/setup?intent=live&step=${step}`)
}

function openSetup(): void { void router.push('/setup?intent=live') }

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

async function prepareGateway(actuatorArm: boolean): Promise<GatewayPreflightResult> {
  let result = await selectCommandProfile('LIVE_TEST', actuatorArm)
  startupPreflight.value = result
  for (let attempt = 0; attempt < 8; attempt += 1) {
    const authorized = actuatorArm ? result.physical_fire_enabled : result.physical_motion_enabled
    if (authorized) return result
    // Camera capture and the Windows worker need a short warm-up after a
    // profile is applied. Re-run the visible preflight; never hide its gates.
    await wait(650)
    result = await runCommandPreflight(actuatorArm)
    startupPreflight.value = result
  }
  return result
}

async function continueFlow(): Promise<void> {
  busy.value = true
  feedback.value = ''
  startupWarnings.value = []
  try {
    if (!selectedProfileId.value) throw new Error('Önce bir kurulum profili seçin veya Kurulum ve ayarlar bölümünden profil oluşturun.')
    const applied = await applyDeviceProfile(selectedProfileId.value, true)
    if (!applied.accepted) throw new Error(applied.warnings.join(' · ') || applied.reason)
    startupWarnings.value = applied.warnings
    localStorage.setItem('istiklal_active_profile_id', applied.profile.profile_id)

    const liveFire = selectedMode.value === 'LIVE_HARDWARE'
    const preflight = await prepareGateway(liveFire)
    const authorized = liveFire ? preflight.physical_fire_enabled : preflight.physical_motion_enabled
    if (!authorized) {
      const codes = preflight.reason_codes.filter((code) => !(code === 'ACTUATOR_NOT_ARMED' && !liveFire))
      feedback.value = codes.length
        ? `Sistem henüz hazır değil: ${codes.join(' · ')}`
        : 'Sistem henüz hazır değil. Aşağıdaki ön kontrol maddelerini düzeltip yeniden deneyin.'
      await readiness.refresh()
      return
    }

    localStorage.setItem('istiklal_startup_intent', liveFire ? 'LIVE_HARDWARE' : 'TRACKING_TEST')
    await router.push(liveFire ? '/cockpit?live=1&fire=1&autotrack=1' : '/cockpit?live=1&fire=0&autotrack=1')
  } catch (caught) {
    feedback.value = caught instanceof Error ? caught.message : 'Mod seçimi uygulanamadı.'
  } finally {
    busy.value = false
  }
}

async function loadProfiles(): Promise<void> {
  profilesLoading.value = true
  try {
    const result = await fetchDeviceProfiles()
    profiles.value = result.profiles.filter((item) => item.updated_at > 0)
    const requestedId = selectedProfileId.value || result.active_profile_id
    const selected = profiles.value.find((item) => item.profile_id === requestedId)
    if (selected) {
      selectedProfileId.value = selected.profile_id
      localStorage.setItem('istiklal_active_profile_id', selected.profile_id)
    } else if (selectedProfileId.value) {
      selectedProfileId.value = ''
      localStorage.removeItem('istiklal_active_profile_id')
    }
  } catch (caught) {
    feedback.value = caught instanceof Error ? caught.message : 'Profiller yüklenemedi.'
  } finally {
    profilesLoading.value = false
  }
}

watch(selectedProfileId, (profileId) => {
  const selected = profiles.value.find((item) => item.profile_id === profileId)
  if (!selected) return
  localStorage.setItem('istiklal_active_profile_id', selected.profile_id)
  feedback.value = ''
  startupPreflight.value = null
  startupWarnings.value = []
})

onMounted(() => {
  void readiness.refresh()
  void loadProfiles()
  timer = setInterval(() => { now.value = new Date() }, 1000)
  refreshTimer = setInterval(() => { void readiness.refresh() }, 3000)
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<template>
  <main class="landing">
    <img class="background" src="/assets/startup/ilk_acilis_ekrani.png?v=20260716" alt="İSTİKLAL taret sistemi" />
    <div class="veil" />
    <header class="header">
      <div>
        <p class="eyebrow">İSTİKLAL</p>
        <h1>Hava Savunma Sistemi</h1>
      </div>
      <div class="header-actions">
        <button class="setup-link" type="button" @click="openSetup">Kurulum ve ayarlar</button>
        <div class="clock" aria-label="Sistem saati">
          <b>{{ timeLabel }}</b>
          <span>{{ readinessItems[0]?.state === 'READY' ? 'MERKEZ SİSTEM BAĞLI' : 'MERKEZ SİSTEM BEKLİYOR' }}</span>
        </div>
      </div>
    </header>

    <section class="content">
      <aside class="readiness-card" aria-label="Sistem hazırlığı">
        <div class="card-heading">
          <div>
            <p class="eyebrow">CANLI DURUM</p>
            <h2>Sistem durumu</h2>
          </div>
          <button class="refresh" type="button" :disabled="readinessLoading" @click="readiness.refresh()">
            {{ readinessLoading ? 'Kontrol ediliyor' : 'Yenile' }}
          </button>
        </div>
        <button v-for="item in readinessItems" :key="item.key" class="readiness-row" type="button" @click="openFix(item)">
          <span class="state-dot" :class="item.state.toLowerCase()" />
          <span class="row-copy"><b>{{ item.title }}</b><small>{{ item.message }}</small></span>
          <span class="row-action">{{ item.state === 'READY' ? 'Ayrıntı' : item.action === 'refresh' ? 'Yenile' : 'Düzelt' }}</span>
          <code v-if="item.reasonCode">{{ item.reasonCode }}</code>
        </button>
        <p v-if="readinessError" class="error">{{ readinessError }}</p>
      </aside>

      <section class="decision" aria-label="Çalışma modu seçimi">
        <p class="eyebrow">ÇALIŞMA BİÇİMİ</p>
        <div class="profile-picker">
          <div><b>Kurulum profili</b><small>{{ profileSummary }}</small></div>
          <select v-model="selectedProfileId" :disabled="profilesLoading">
            <option value="">{{ profilesLoading ? 'Profiller yükleniyor…' : 'Profil seçmeden devam et' }}</option>
            <option v-for="item in profiles" :key="item.profile_id" :value="item.profile_id">{{ item.display_name }}</option>
          </select>
        </div>
        <div class="mode-grid">
          <button class="mode-card" :class="{ selected: selectedMode === 'TRACKING_TEST' }" type="button" @click="selectMode('TRACKING_TEST')">
            <span class="mode-icon">◌</span><b>TEST</b><small>Gerçek takip ve taret hareketi</small><em>Tetik kapalı</em>
          </button>
          <button class="mode-card live" :class="{ selected: selectedMode === 'LIVE_HARDWARE' }" type="button" @click="selectMode('LIVE_HARDWARE')">
            <span class="mode-icon">◉</span><b>CANLI SİSTEM</b><small>Gerçek taret ve tetik</small><em>Ön kontrol ile etkin</em>
          </button>
        </div>
        <div class="selection-summary">
          <span>{{ selectedMode === 'TRACKING_TEST' ? 'Test seçili · FIRE kapalı' : 'Canlı sistem seçili · FIRE açık' }}</span>
          <code v-if="startupPreflight?.reason_codes.length">{{ startupPreflight.reason_codes.join(' · ') }}</code>
          <code v-else-if="primaryBlocker">{{ primaryBlocker.reasonCode }}</code>
        </div>
        <button class="continue" type="button" :disabled="busy" @click="continueFlow">
          {{ busy ? 'Uygulanıyor…' : modeTitle }}
        </button>
        <div v-if="startupPreflight" class="preflight-result" :class="{ ready: selectedMode === 'LIVE_HARDWARE' ? startupPreflight.physical_fire_enabled : startupPreflight.physical_motion_enabled }">
          <b>{{ (selectedMode === 'LIVE_HARDWARE' ? startupPreflight.physical_fire_enabled : startupPreflight.physical_motion_enabled) ? 'SİSTEM HAZIR' : 'DÜZELTİLMESİ GEREKENLER' }}</b>
          <div v-for="gate in startupPreflight.gates" :key="gate.code"><span :class="gate.ready ? 'ok' : 'bad'">{{ gate.ready ? '●' : '●' }}</span><code>{{ gate.code }}</code><small>{{ gate.detail }}</small></div>
        </div>
        <p v-if="startupWarnings.length" class="warning">{{ startupWarnings.join(' · ') }}</p>
        <p v-if="feedback" class="error">{{ feedback }}</p>
      </section>
    </section>
  </main>
</template>

<style scoped>
.landing{position:relative;min-height:100vh;overflow:hidden;background:#020812;color:#edf8ff;font-family:Inter,ui-sans-serif,system-ui,sans-serif}.background,.veil{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}.background{opacity:.96;object-position:center}.veil{background:radial-gradient(ellipse at 55% 44%,rgba(4,11,20,.04) 0%,rgba(2,8,16,.18) 48%,rgba(1,7,16,.82) 100%),linear-gradient(90deg,rgba(1,7,16,.66),transparent 52%,rgba(1,7,16,.35));pointer-events:none}.header,.content{position:relative;z-index:1}.header{display:flex;align-items:flex-start;justify-content:space-between;padding:38px clamp(24px,5vw,72px)}.eyebrow{margin:0;color:#62e8ff;font-size:.7rem;font-weight:900;letter-spacing:.25em}.header h1{margin:7px 0 4px;font-size:clamp(1.8rem,3vw,3.2rem);text-transform:uppercase;letter-spacing:.02em}.header-actions{display:flex;align-items:center;gap:10px}.setup-link{border:1px solid #70dff455;border-radius:10px;background:#071b2ac9;color:#c5f6ff;padding:11px 13px;font-size:.75rem;font-weight:900}.clock{display:grid;gap:4px;min-width:180px;padding:13px 16px;border:1px solid #5ec4d744;border-radius:14px;background:#061321c9;text-align:right}.clock b{font-size:1.2rem;letter-spacing:.08em}.clock span{color:#75dcec;font-size:.68rem;font-weight:800;letter-spacing:.12em}.content{display:grid;grid-template-columns:1fr minmax(350px,410px);grid-template-rows:1fr auto;gap:24px;min-height:calc(100vh - 145px);padding:0 clamp(24px,5vw,72px) 32px}.readiness-card,.decision{border:1px solid #65cbdf35;border-radius:18px;background:#06101dcc;box-shadow:0 22px 65px #0008;backdrop-filter:blur(14px)}.readiness-card{grid-column:2;grid-row:1;align-self:start;margin-top:4px;padding:20px}.card-heading{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}.card-heading h2{margin:5px 0;font-size:1.3rem}.refresh{border:1px solid #80dff644;border-radius:9px;background:#0b2335;color:#b7f3ff;padding:8px 10px;font-weight:800}.readiness-row{display:grid;grid-template-columns:9px 1fr auto;gap:10px;align-items:center;width:100%;padding:15px 4px;border:0;border-top:1px solid #ffffff10;background:transparent;color:inherit;text-align:left;cursor:pointer}.readiness-row code{grid-column:2/4;color:#ffc66d;font-size:.62rem}.state-dot{width:9px;height:9px;border-radius:99px;background:#8da0b4}.state-dot.ready{background:#4fe39d;box-shadow:0 0 14px #4fe39d}.state-dot.blocked{background:#fb6974;box-shadow:0 0 14px #fb6974}.state-dot.degraded,.state-dot.unknown{background:#f5bd55}.row-copy{display:grid;gap:3px}.row-copy b{font-size:.9rem}.row-copy small{color:#a6bacb;font-size:.74rem;line-height:1.35}.row-action{color:#79e7fb;font-size:.7rem;font-weight:800}.decision{grid-column:1/-1;grid-row:2;justify-self:center;width:min(660px,calc(100vw - 48px));padding:16px 20px}.mode-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}.mode-card{display:grid;grid-template-columns:auto 1fr;column-gap:9px;align-content:center;min-height:94px;padding:13px;border:1px solid #ffffff20;border-radius:13px;background:#071827cc;color:#e7f6ff;text-align:left;cursor:pointer;transition:.18s}.mode-card:hover,.mode-card.selected{border-color:#69e5fb;background:#0b2a3bbd}.mode-card.live.selected{border-color:#ffbd5b;background:#302113cc}.mode-icon{grid-row:span 3;font-size:1.15rem;color:#72e9ff}.mode-card.live .mode-icon{color:#ffbc59}.mode-card b{font-size:.9rem;letter-spacing:.08em}.mode-card small{margin-top:4px;color:#b9c8d4;font-size:.72rem}.mode-card em{margin-top:5px;font-style:normal;color:#7deab4;font-size:.66rem;font-weight:800}.mode-card.live em{color:#ffce7f}.selection-summary{display:flex;justify-content:space-between;align-items:center;margin:10px 0 7px;color:#b7c8d8;font-size:.74rem}.selection-summary code{color:#ffc66d}.continue{width:100%;border:0;border-radius:11px;background:linear-gradient(135deg,#14b9d7,#3ee1c1);color:#00121b;padding:12px;font-weight:950;font-size:.9rem;cursor:pointer}.continue:disabled,.refresh:disabled{opacity:.55;cursor:wait}.error{margin:12px 0 0;color:#ff9ca4;font-size:.78rem;line-height:1.45}@media(max-width:850px){.header{padding:24px}.clock{display:none}.content{grid-template-columns:1fr;grid-template-rows:auto auto;min-height:auto;padding:56px 24px 32px}.readiness-card{grid-column:1;grid-row:1}.decision{grid-column:1;grid-row:2;width:auto;justify-self:stretch}.mode-grid{grid-template-columns:1fr}}
</style>
<style scoped>
.profile-picker{display:grid;grid-template-columns:minmax(0,1fr) minmax(210px,280px);gap:14px;align-items:center;margin-top:10px;padding:12px 14px;border:1px solid #67dced33;border-radius:12px;background:#061725d9}.profile-picker>div{display:grid;gap:4px}.profile-picker b{font-size:.82rem}.profile-picker small{overflow:hidden;color:#a9bdcc;font-size:.69rem;text-overflow:ellipsis;white-space:nowrap}.profile-picker select{width:100%;border:1px solid #64dff54d;border-radius:9px;background:#020a13;color:#eaf9ff;padding:10px;cursor:pointer}.profile-picker select:disabled{opacity:.55;cursor:wait}@media(max-width:620px){.profile-picker{grid-template-columns:1fr}.profile-picker small{white-space:normal}}
.preflight-result{display:grid;gap:6px;max-height:190px;overflow:auto;margin-top:10px;padding:10px;border:1px solid #ff796855;border-radius:10px;background:#2a1114dd}.preflight-result.ready{border-color:#49dfa06b;background:#09261ddd}.preflight-result>b{font-size:.7rem;letter-spacing:.12em}.preflight-result>div{display:grid;grid-template-columns:12px max-content 1fr;gap:7px;align-items:start}.preflight-result code{color:#e9f7ff;font-size:.63rem}.preflight-result small{color:#aabfcd;font-size:.62rem;line-height:1.3}.preflight-result .ok{color:#4fe39d}.preflight-result .bad{color:#ff6f78}.warning{margin:9px 0 0;color:#ffd07e;font-size:.7rem;line-height:1.4}
</style>
<style scoped>
@media(min-width:851px){
  .landing{height:100vh;min-height:0}
  .header{box-sizing:border-box;height:112px;padding:22px clamp(24px,5vw,72px)}
  .header h1{font-size:clamp(1.8rem,2.55vw,2.85rem)}
  .setup-link{padding:9px 12px}
  .clock{min-width:165px;padding:10px 14px}
  .content{box-sizing:border-box;height:calc(100vh - 112px);min-height:0;grid-template-rows:minmax(0,1fr) auto;gap:12px;padding:0 clamp(24px,5vw,72px) 16px}
  .readiness-card{margin-top:0;padding:15px 18px}
  .card-heading{margin-bottom:7px}
  .card-heading h2{margin:3px 0;font-size:1.18rem}
  .refresh{padding:7px 9px}
  .readiness-row{gap:9px;padding:10px 3px}
  .readiness-row code{font-size:.58rem}
  .row-copy b{font-size:.83rem}
  .row-copy small{font-size:.68rem;line-height:1.25}
  .decision{width:min(640px,calc(100vw - 48px));padding:11px 16px}
  .profile-picker{gap:10px;margin-top:7px;padding:8px 11px}
  .profile-picker select{padding:8px 9px}
  .mode-grid{gap:9px;margin-top:8px}
  .mode-card{min-height:72px;padding:9px 11px}
  .mode-card small{margin-top:2px}
  .mode-card em{margin-top:3px}
  .selection-summary{margin:7px 0 5px}
  .continue{padding:10px}
}
@media(min-width:851px) and (max-height:760px){
  .header{height:92px;padding-top:14px;padding-bottom:14px}
  .header h1{font-size:2rem}
  .content{height:calc(100vh - 92px)}
  .readiness-row{padding:7px 3px}
  .decision{padding:8px 13px}
  .mode-card{min-height:64px}
}
</style>
