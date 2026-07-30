<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { Clock3, Settings2, ShieldCheck } from '@lucide/vue'
import type { CockpitBadge } from './types'

const props = defineProps<{ badges: CockpitBadge[] }>()
const emit = defineEmits<{ toggleEngineer: [] }>()
const clock = ref(new Date())
let timer: ReturnType<typeof setInterval> | null = null

const timeLabel = computed(() => clock.value.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
const visibleBadges = computed(() => props.badges.slice(0, 4).map((badge) => {
  const separator = badge.label.indexOf(' ')
  return {
    ...badge,
    key: separator > 0 ? badge.label.slice(0, separator) : 'DURUM',
    value: separator > 0 ? badge.label.slice(separator + 1) : badge.label,
  }
}))

onMounted(() => { timer = setInterval(() => { clock.value = new Date() }, 1000) })
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <header class="topbar">
    <div class="brand">
      <span class="brand-mark"><ShieldCheck :size="18" /></span>
      <div><p>İSTİKLAL</p><h1>Operasyon Kokpiti</h1></div>
    </div>

    <div class="states" aria-label="Operasyon durumu">
      <div v-for="badge in visibleBadges" :key="badge.label" class="state" :class="`state-${badge.tone}`">
        <span>{{ badge.key }}</span><b>{{ badge.value }}</b>
      </div>
    </div>

    <div class="top-actions">
      <button class="engineer" type="button" @click="emit('toggleEngineer')"><Settings2 :size="16" /><span>Mühendis</span></button>
      <time><Clock3 :size="15" />{{ timeLabel }}</time>
    </div>
  </header>
</template>

<style scoped>
.topbar{display:grid;grid-template-columns:minmax(210px,.78fr) minmax(520px,2fr) auto;align-items:center;gap:14px;min-height:64px;padding:9px 12px;border:1px solid rgba(92,225,248,.18);border-radius:16px;background:linear-gradient(180deg,rgba(8,24,38,.96),rgba(4,13,24,.96));color:#eefaff;box-shadow:0 14px 36px rgba(0,0,0,.3)}.brand{display:flex;align-items:center;gap:10px;min-width:0}.brand-mark{display:grid;place-items:center;width:35px;height:35px;border:1px solid rgba(94,234,255,.34);border-radius:11px;background:rgba(8,47,73,.72);color:#6ee7f9}.brand p{margin:0;color:#60e6fa;font-size:.59rem;font-weight:900;letter-spacing:.24em}.brand h1{overflow:hidden;margin:3px 0 0;font-size:.96rem;text-overflow:ellipsis;white-space:nowrap}.states{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.state{position:relative;min-width:0;padding:7px 9px 7px 12px;border:1px solid rgba(148,163,184,.13);border-radius:10px;background:rgba(8,23,37,.76)}.state:before{position:absolute;top:10px;bottom:10px;left:0;width:3px;border-radius:0 3px 3px 0;background:#64748b;content:''}.state span,.state b{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.state span{color:#7f94a7;font-size:.54rem;font-weight:900;letter-spacing:.12em}.state b{margin-top:3px;color:#dbeafe;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.69rem}.state-good:before{background:#34d399}.state-warn:before{background:#fbbf24}.state-bad:before{background:#fb7185}.state-good b{color:#9af2c3}.state-warn b{color:#ffd47e}.state-bad b{color:#ffa2aa}.top-actions{display:flex;align-items:center;gap:8px}.engineer,time{display:flex;align-items:center;gap:7px;border:1px solid rgba(103,232,249,.24);border-radius:10px;background:rgba(8,47,73,.42);color:#cffafe;padding:8px 10px;font-size:.68rem;font-weight:850;white-space:nowrap}.engineer{cursor:pointer;transition:.16s}.engineer:hover{border-color:rgba(103,232,249,.58);background:rgba(8,74,99,.58);transform:translateY(-1px)}time{border-color:rgba(148,163,184,.14);background:rgba(2,8,18,.5);color:#cbd5e1;font-family:ui-monospace,monospace}@media(max-width:1150px){.topbar{grid-template-columns:1fr auto}.states{grid-column:1/-1;grid-row:2}.top-actions{grid-column:2;grid-row:1}}@media(max-width:700px){.topbar{display:flex;flex-wrap:wrap}.brand{flex:1}.states{order:3;grid-template-columns:repeat(2,1fr);width:100%}time{display:none}.engineer span{display:none}}
</style>
