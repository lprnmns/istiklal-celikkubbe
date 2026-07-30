import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { fetchDigitalTwinAssets, fetchDigitalTwinState, fetchLatestDigitalTwinReplay, generateDigitalTwinReplay, logDigitalTwinPanelRendered } from '../api/digitalTwin'
import { fetchEngagementDigitalTwinReplay, fetchEngagementEvidenceRecords, fetchEngagementEvidenceStatus } from '../api/engagementEvidence'
import type { DigitalTwinAssetsResponse, DigitalTwinReplayGenerateResult, DigitalTwinReplaySummary, DigitalTwinState } from '../types/digitalTwin'
import type { EngagementEvidenceStatus, EngagementEvidenceSummary } from '../types/engagementEvidence'

export const useDigitalTwinStore = defineStore('digitalTwin', () => {
  const state = ref<DigitalTwinState | null>(null)
  const assets = ref<DigitalTwinAssetsResponse | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastUpdatedAt = ref<number | null>(null)
  const lastReplay = ref<DigitalTwinReplayGenerateResult | null>(null)
  const replay = ref<DigitalTwinReplaySummary | null>(null)
  const engagementEvidence = ref<EngagementEvidenceStatus | null>(null)
  const engagementRecords = ref<EngagementEvidenceSummary[]>([])

  const readOnlyHealthy = computed(() => Boolean(
    state.value?.no_physical_command_generated
      && state.value.safety.digital_twin_read_only
      && !state.value.safety.digital_twin_command_authority,
  ))

  async function refresh(): Promise<void> {
    loading.value = true
    try {
      const [nextState, nextAssets, nextEvidence, nextEvidenceRecords] = await Promise.all([
        fetchDigitalTwinState(),
        assets.value ? Promise.resolve(assets.value) : fetchDigitalTwinAssets(),
        fetchEngagementEvidenceStatus(),
        fetchEngagementEvidenceRecords(),
      ])
      state.value = nextState
      assets.value = nextAssets
      engagementEvidence.value = nextEvidence
      engagementRecords.value = nextEvidenceRecords.records
      lastUpdatedAt.value = Date.now()
      error.value = null
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    } finally {
      loading.value = false
    }
  }

  async function generateReplay(): Promise<void> {
    try {
      lastReplay.value = await generateDigitalTwinReplay()
      error.value = null
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    }
  }

  async function loadReplay(): Promise<void> {
    try {
      replay.value = await fetchLatestDigitalTwinReplay()
      error.value = null
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    }
  }

  async function loadEngagementReplay(engagementId: string): Promise<void> {
    try {
      replay.value = await fetchEngagementDigitalTwinReplay(engagementId)
      error.value = null
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : String(exc)
    }
  }

  async function panelRendered(): Promise<void> {
    try {
      await logDigitalTwinPanelRendered()
    } catch {
      // Rendering evidence logging must never affect cockpit behavior.
    }
  }

  return {
    assets,
    error,
    engagementEvidence,
    engagementRecords,
    generateReplay,
    lastReplay,
    lastUpdatedAt,
    loadReplay,
    loadEngagementReplay,
    loading,
    panelRendered,
    readOnlyHealthy,
    refresh,
    replay,
    state,
  }
})
