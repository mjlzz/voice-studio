import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { EngineStatus } from '@/api/types'
import { getEngines } from '@/api/tts'

export const useEngineStore = defineStore('engine', () => {
  const ttsEngine = ref<'cloud' | 'local'>('cloud')
  const sttEngine = ref<'local'>('local')
  const status = ref<EngineStatus | null>(null)
  const loading = ref(false)

  const isCloud = computed(() => ttsEngine.value === 'cloud')
  const isLocal = computed(() => ttsEngine.value === 'local')

  async function fetchStatus() {
    loading.value = true
    try {
      status.value = await getEngines()
    } catch (error) {
      console.error('Failed to fetch engine status:', error)
    } finally {
      loading.value = false
    }
  }

  function setTTSEngine(engine: 'cloud' | 'local') {
    ttsEngine.value = engine
  }

  return {
    ttsEngine,
    sttEngine,
    status,
    loading,
    isCloud,
    isLocal,
    fetchStatus,
    setTTSEngine
  }
})