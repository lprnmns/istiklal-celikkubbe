<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Activity, Check, Gauge, Play, Square, Star } from '@lucide/vue'
import {
  applyTrackingPreset,
  fetchTrackingTuning,
  rateTrackingTrial,
  startTrackingTrial,
  stopTrackingTrial,
  type TrackingTuningStatus,
} from '../../api/trackingTuning'

const status = ref<TrackingTuningStatus>({ presets: [], active_trial: null, results: [] })
const busy = ref(false)
const message = ref('Bir profil seçin; her denemede balonu aynı rotada hareket ettirin.')
let timer: ReturnType<typeof setInterval> | null = null

const rankedResults = computed(() => [...status.value.results].reverse().sort((a, b) => {
  const operatorDelta = (b.operator_rating ?? 0) - (a.operator_rating ?? 0)
  return operatorDelta || b.technical_score - a.technical_score
}))

async function refresh(): Promise<void> {
  try { status.value = await fetchTrackingTuning() } catch (error) { message.value = String(error) }
}

async function start(presetId: string): Promise<void> {
  busy.value = true
  try {
    status.value = await startTrackingTrial(presetId)
    message.value = 'Deneme başladı · balonu sağ-sol, yukarı-aşağı ve kısa süre kadraj dışına taşıyın.'
  } catch (error) { message.value = `Başlatılamadı: ${error instanceof Error ? error.message : error}` }
  finally { busy.value = false }
}

async function stop(): Promise<void> {
  busy.value = true
  try { status.value = await stopTrackingTrial(); message.value = 'Deneme kaydedildi. Arkadaşınız 1–5 yıldız versin.' }
  catch (error) { message.value = `Durdurulamadı: ${error instanceof Error ? error.message : error}` }
  finally { busy.value = false }
}

async function rate(trialId: string, rating: number): Promise<void> {
  status.value = await rateTrackingTrial(trialId, rating)
  message.value = `${rating}/5 operatör puanı kaydedildi.`
}

async function applyWinner(presetId: string): Promise<void> {
  busy.value = true
  try { status.value = await applyTrackingPreset(presetId); message.value = 'Profil aktif tracker ayarı olarak uygulandı.' }
  catch (error) { message.value = `Uygulanamadı: ${error instanceof Error ? error.message : error}` }
  finally { busy.value = false }
}

onMounted(() => { void refresh(); timer = setInterval(() => void refresh(), 750) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <section class="tuning-panel">
    <header>
      <div><p>FİZİKSEL SAHA KARŞILAŞTIRMASI</p><h3>Takip Algoritması ve PID Deneyleri</h3></div>
      <span :class="status.active_trial ? 'live' : ''"><Activity :size="14" />{{ status.active_trial ? 'ÖLÇÜM AKTİF' : 'BEKLİYOR' }}</span>
    </header>

    <div v-if="status.active_trial" class="active-trial">
      <div><small>Çalışan profil</small><b>{{ status.active_trial.preset_name }}</b><em>{{ status.active_trial.algorithm }}</em></div>
      <div class="live-metrics">
        <span><b>{{ status.active_trial.elapsed_s }} s</b><small>Süre</small></span>
        <span><b>{{ status.active_trial.target_frames }}</b><small>Hedefli kare</small></span>
        <span><b>{{ status.active_trial.lost_frames }}</b><small>Kayıp kare</small></span>
        <span><b>{{ status.active_trial.reversals }}</b><small>Yön değişimi</small></span>
      </div>
      <button class="stop" :disabled="busy" @click="stop"><Square :size="15" /> Denemeyi bitir ve kaydet</button>
    </div>

    <div class="preset-grid">
      <article v-for="preset in status.presets" :key="preset.preset_id" :class="{ selected: status.active_trial?.preset_id === preset.preset_id }">
        <div class="preset-title"><Gauge :size="17" /><div><b>{{ preset.name }}</b><small>{{ preset.algorithm }}</small></div></div>
        <p>{{ preset.description }}</p>
        <div class="config-line">
          <span>Kp {{ preset.config.pid_kp_x }}/{{ preset.config.pid_kp_y }}</span>
          <span>Kd {{ preset.config.pid_kd_x }}/{{ preset.config.pid_kd_y }}</span>
          <span>Hız {{ preset.config.max_speed }}</span>
          <span>{{ preset.config.lead_enabled ? 'Lead açık' : 'Lead kapalı' }}</span>
        </div>
        <button :disabled="busy || !!status.active_trial" @click="start(preset.preset_id)"><Play :size="14" /> Bu profille dene</button>
      </article>
    </div>

    <p class="message">{{ message }}</p>

    <div v-if="rankedResults.length" class="results">
      <h4>Kaydedilmiş denemeler</h4>
      <article v-for="(result, index) in rankedResults" :key="result.trial_id">
        <div class="rank">#{{ index + 1 }}</div>
        <div class="result-name"><b>{{ result.preset_name }}</b><small>{{ result.duration_s }} s · {{ result.samples }} kare</small></div>
        <div><b>{{ result.mean_error_px }} px</b><small>Ort. hata</small></div>
        <div><b>{{ result.p95_error_px }} px</b><small>P95 hata</small></div>
        <div><b>{{ Math.round(result.loss_ratio * 100) }}%</b><small>Hedef kaybı</small></div>
        <div><b>{{ result.technical_score }}</b><small>Teknik puan</small></div>
        <div class="stars"><button v-for="star in 5" :key="star" :class="{ on: star <= (result.operator_rating ?? 0) }" @click="rate(result.trial_id, star)"><Star :size="13" /></button></div>
        <button class="apply" :disabled="busy || !!status.active_trial" @click="applyWinner(result.preset_id)"><Check :size="13" /> Uygula</button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.tuning-panel{display:grid;gap:12px;color:#e8f7ff}.tuning-panel>header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.tuning-panel header p{margin:0;color:#5ee5fb;font-size:.59rem;font-weight:900;letter-spacing:.17em}.tuning-panel h3{margin:4px 0 0;font-size:1rem}.tuning-panel header>span{display:flex;align-items:center;gap:5px;border:1px solid #ffffff1c;border-radius:999px;padding:6px 8px;color:#93aabd;font-size:.62rem;font-weight:900}.tuning-panel header>span.live{border-color:#40d99b66;color:#7bf1bd;background:#0b392b88}.active-trial{display:grid;gap:10px;padding:12px;border:1px solid #42dda05c;border-radius:12px;background:#08291f}.active-trial small,.results small{display:block;color:#91a9b9;font-size:.61rem}.active-trial em{display:block;color:#70e8f7;font-size:.68rem;font-style:normal}.live-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.live-metrics span{padding:7px;border-radius:8px;background:#031610;text-align:center}.stop,.preset-grid button,.apply{display:flex;align-items:center;justify-content:center;gap:6px;border:1px solid #ffffff20;border-radius:8px;padding:8px;background:#0b2030;color:#d9f7ff;font-size:.68rem;font-weight:900;cursor:pointer}.stop{border-color:#fa718866;background:#41151d;color:#ffd6dc}.preset-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.preset-grid article{display:grid;gap:8px;padding:11px;border:1px solid #ffffff16;border-radius:11px;background:#071523}.preset-grid article.selected{border-color:#53e3ae;background:#092a21}.preset-title{display:flex;gap:8px;align-items:center}.preset-title>b,.preset-title b{display:block;font-size:.76rem}.preset-title small{display:block;color:#63ddec;font-size:.6rem}.preset-grid p{min-height:32px;margin:0;color:#9db1bf;font-size:.64rem;line-height:1.4}.config-line{display:flex;gap:5px;flex-wrap:wrap}.config-line span{padding:3px 5px;border-radius:5px;background:#020b14;color:#a8bdcb;font:600 .56rem ui-monospace,monospace}.message{margin:0;padding:8px 10px;border-left:3px solid #55daeb;background:#08202c;color:#bdeef5;font-size:.67rem}.results{display:grid;gap:6px}.results h4{margin:4px 0;font-size:.75rem}.results article{display:grid;grid-template-columns:28px minmax(100px,1.5fr) repeat(4,minmax(58px,1fr));gap:6px;align-items:center;padding:8px;border:1px solid #ffffff12;border-radius:9px;background:#06111d}.results article>div:not(.stars){min-width:0}.results article>div>b{font-size:.66rem}.rank{color:#5ee5fb;font-weight:900}.stars{display:flex;grid-column:2/6;gap:2px}.stars button{border:0;background:transparent;color:#425469;padding:2px;cursor:pointer}.stars button.on{color:#facc15}.apply{grid-column:6;padding:6px}.tuning-panel button:hover:not(:disabled){filter:brightness(1.18);transform:translateY(-1px)}.tuning-panel button:disabled{opacity:.4;cursor:not-allowed}@media(max-width:560px){.preset-grid{grid-template-columns:1fr}.live-metrics{grid-template-columns:1fr 1fr}.results article{grid-template-columns:28px 1fr 1fr}.stars,.apply{grid-column:auto}}
</style>
