import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { EngineStatus } from '@/api/types'
import { getEngines } from '@/api/tts'

export type TTSEngineType = 'cloud' | 'local' | 'mixed'

const STORAGE_KEY = 'voice-studio-engine'

export const useEngineStore = defineStore('engine', () => {
  const ttsEngine = ref<TTSEngineType>('cloud')
  const sttEngine = ref<'local'>('local')
  const status = ref<EngineStatus | null>(null)
  const loading = ref(false)

  const isCloud = computed(() => ttsEngine.value === 'cloud')
  const isLocal = computed(() => ttsEngine.value === 'local')
  const isMixed = computed(() => ttsEngine.value === 'mixed')

  function load() {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && ['cloud', 'local', 'mixed'].includes(saved)) {
      ttsEngine.value = saved as TTSEngineType
    }
  }

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

  function setTTSEngine(engine: TTSEngineType) {
    ttsEngine.value = engine
    localStorage.setItem(STORAGE_KEY, engine)
  }

  load()

  return {
    ttsEngine,
    sttEngine,
    status,
    loading,
    isCloud,
    isLocal,
    isMixed,
    fetchStatus,
    setTTSEngine
  }
})