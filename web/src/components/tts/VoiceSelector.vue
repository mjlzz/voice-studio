<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { User } from 'lucide-vue-next'
import { useEngineStore } from '@/stores/engine'
import { getVoices, getPresets } from '@/api/tts'
import type { Voice, VoicePresets } from '@/api/types'
import VsSelect from '@/components/common/Select.vue'

// Local voice type (different from cloud)
interface LocalVoice {
  name: string
  language: string
  quality: string
  downloaded: boolean
}

const engineStore = useEngineStore()

defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const voices = ref<(Voice | LocalVoice)[]>([])
const presets = ref<VoicePresets | null>(null)
const loading = ref(false)

// Selected language filter
const language = ref<string>('zh')

const languageOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: '英文' }
]

// Check if current engine is local
const isLocalEngine = computed(() => engineStore.ttsEngine === 'local')

// Get effective engine for voice selection (mixed mode uses cloud voices)
const effectiveEngine = computed(() => {
  const engine = engineStore.ttsEngine
  if (engine === 'mixed') return 'cloud'
  return engine
})

// Voice options for select - handle both cloud and local formats
const voiceOptions = computed(() => {
  if (isLocalEngine.value) {
    // Local voices have different structure
    return (voices.value as LocalVoice[])
      .filter(v => {
        // Filter by language
        if (language.value === 'zh') {
          return v.language.startsWith('zh')
        } else {
          return v.language.startsWith('en')
        }
      })
      .map(v => ({
        value: v.name,
        label: `${v.name} (${v.quality})${v.downloaded ? ' ✓' : ''}`
      }))
  } else {
    // Cloud voices
    return (voices.value as Voice[])
      .filter(v => {
        if (language.value === 'zh') {
          return v.locale?.startsWith('zh')
        } else {
          return v.locale?.startsWith('en')
        }
      })
      .map(v => ({
        value: v.short_name,
        label: `${v.short_name} (${v.gender === 'Female' ? '女' : '男'})`
      }))
  }
})

// Preset voices
const presetVoices = computed(() => {
  if (!presets.value) return []
  const engine = effectiveEngine.value as 'cloud' | 'local'
  const lang = language.value
  const presetMap = presets.value[engine]?.[lang === 'zh' ? 'chinese' : 'english'] || {}
  return Object.entries(presetMap).map(([key, value]) => ({
    key,
    value: value as string,
    label: key
  }))
})

// Fetch voices
async function fetchVoices() {
  loading.value = true
  try {
    voices.value = await getVoices(language.value, effectiveEngine.value as 'cloud' | 'local')
  } catch (e) {
    console.error('Failed to fetch voices:', e)
  } finally {
    loading.value = false
  }
}

// Fetch presets
async function fetchPresets() {
  try {
    presets.value = await getPresets()
  } catch (e) {
    console.error('Failed to fetch presets:', e)
  }
}

// Watch engine and language changes
watch([() => engineStore.ttsEngine, language], () => {
  fetchVoices()
})

// Select preset voice
const selectPreset = (voice: string) => {
  emit('update:modelValue', voice)
}

onMounted(() => {
  fetchVoices()
  fetchPresets()
})

// Set default voice when engine changes
watch(() => engineStore.ttsEngine, (engine) => {
  if (engine === 'local') {
    emit('update:modelValue', 'zh_CN-huayan')
  } else {
    emit('update:modelValue', 'zh-CN-XiaoxiaoNeural')
  }
}, { immediate: true })
</script>

<template>
  <div class="space-y-4">
    <!-- Language filter -->
    <div class="flex items-center gap-4">
      <span class="text-sm text-neutral-600">语言：</span>
      <div class="flex gap-2">
        <button
          v-for="lang in languageOptions"
          :key="lang.value"
          :class="[
            'px-3 py-1.5 text-sm rounded-lg transition-colors',
            language === lang.value
              ? 'bg-primary-100 text-primary-600'
              : 'text-neutral-600 hover:bg-neutral-100'
          ]"
          @click="language = lang.value"
        >
          {{ lang.label }}
        </button>
      </div>
    </div>

    <!-- Preset voices -->
    <div v-if="presetVoices.length > 0" class="space-y-2">
      <span class="text-sm text-neutral-600">推荐音色：</span>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="preset in presetVoices"
          :key="preset.key"
          :class="[
            'px-3 py-2 text-sm rounded-lg border transition-colors flex items-center gap-2',
            modelValue === preset.value
              ? 'border-primary-500 bg-primary-50 text-primary-600'
              : 'border-neutral-200 hover:border-primary-300 hover:bg-neutral-50'
          ]"
          @click="selectPreset(preset.value)"
        >
          <User class="w-4 h-4" />
          {{ preset.label }}
        </button>
      </div>
    </div>

    <!-- Voice selector -->
    <div class="space-y-2">
      <span class="text-sm text-neutral-600">全部音色：</span>
      <VsSelect
        :model-value="modelValue"
        :options="voiceOptions"
        placeholder="选择音色..."
        @update:model-value="emit('update:modelValue', $event)"
      />
    </div>
  </div>
</template>