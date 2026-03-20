<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Volume2, AlertCircle } from 'lucide-vue-next'
import MainLayout from '@/components/layout/MainLayout.vue'
import VsCard from '@/components/common/Card.vue'
import VsButton from '@/components/common/Button.vue'
import VsSpinner from '@/components/common/Spinner.vue'
import TextInput from '@/components/tts/TextInput.vue'
import VoiceSelector from '@/components/tts/VoiceSelector.vue'
import AudioPlayer from '@/components/tts/AudioPlayer.vue'
import { useEngineStore } from '@/stores/engine'
import { useSettingsStore } from '@/stores/settings'
import { synthesizeSpeech } from '@/api/tts'

const engineStore = useEngineStore()
const settingsStore = useSettingsStore()

const text = ref('')
const voice = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const audioUrl = ref<string | null>(null)

const canSynthesize = computed(() => {
  return text.value.trim() && voice.value && !loading.value
})

// Rate and volume (cloud only)
const rate = ref('+0%')
const volume = ref('+0%')

const rateOptions = [
  { label: '很慢', value: '-50%' },
  { label: '较慢', value: '-25%' },
  { label: '正常', value: '+0%' },
  { label: '较快', value: '+25%' },
  { label: '很快', value: '+50%' }
]

const synthesize = async () => {
  if (!canSynthesize.value) return

  loading.value = true
  error.value = null
  audioUrl.value = null

  // Revoke previous URL
  if (audioUrl.value) {
    URL.revokeObjectURL(audioUrl.value)
  }

  try {
    const blob = await synthesizeSpeech(
      {
        text: text.value,
        voice: voice.value,
        rate: rate.value,
        volume: volume.value
      },
      engineStore.ttsEngine
    )
    audioUrl.value = URL.createObjectURL(blob)
  } catch (e: any) {
    error.value = e.response?.data?.detail || '合成失败，请重试'
  } finally {
    loading.value = false
  }
}

const reset = () => {
  text.value = ''
  audioUrl.value = null
  error.value = null
}

// Save voice preference
watch(voice, (newVoice) => {
  if (newVoice) {
    settingsStore.setDefaultVoice(newVoice)
  }
})
</script>

<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Page header -->
      <div>
        <h1 class="text-2xl font-semibold text-neutral-900">文字转语音</h1>
        <p class="text-sm text-neutral-500 mt-1">
          输入文字，选择音色，生成语音
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left: Input -->
        <div class="space-y-4">
          <!-- Text input -->
          <VsCard title="输入文字">
            <TextInput v-model="text" />
          </VsCard>

          <!-- Voice selector -->
          <VsCard title="选择音色">
            <VoiceSelector v-model="voice" />
          </VsCard>

          <!-- Rate (cloud only) -->
          <VsCard v-if="engineStore.isCloud" title="语速调节">
            <div class="flex gap-2">
              <button
                v-for="opt in rateOptions"
                :key="opt.value"
                :class="[
                  'px-3 py-2 text-sm rounded-lg border transition-colors',
                  rate === opt.value
                    ? 'border-primary-500 bg-primary-50 text-primary-600'
                    : 'border-neutral-200 hover:border-primary-300'
                ]"
                @click="rate = opt.value"
              >
                {{ opt.label }}
              </button>
            </div>
          </VsCard>

          <!-- Synthesize button -->
          <VsButton
            size="lg"
            block
            :loading="loading"
            :disabled="!canSynthesize"
            @click="synthesize"
          >
            <Volume2 class="w-5 h-5" />
            生成语音
          </VsButton>
        </div>

        <!-- Right: Output -->
        <div class="space-y-4">
          <!-- Loading state -->
          <VsCard v-if="loading" class="text-center py-12">
            <div class="flex flex-col items-center gap-4">
              <VsSpinner size="lg" />
              <p class="text-sm text-neutral-600">正在生成语音...</p>
            </div>
          </VsCard>

          <!-- Error state -->
          <VsCard v-if="error && !loading" class="border-red-200 bg-red-50">
            <div class="flex items-center gap-3 text-red-600">
              <AlertCircle class="w-5 h-5" />
              <div>
                <p class="text-sm font-medium">合成失败</p>
                <p class="text-xs text-red-500">{{ error }}</p>
              </div>
            </div>
          </VsCard>

          <!-- Audio player -->
          <div v-if="audioUrl && !loading">
            <h3 class="text-sm font-medium text-neutral-700 mb-2">播放结果</h3>
            <AudioPlayer
              :src="audioUrl"
              :filename="`speech.${engineStore.isCloud ? 'mp3' : 'wav'}`"
            />
            <VsButton class="mt-4" variant="secondary" block @click="reset">
              重新生成
            </VsButton>
          </div>

          <!-- Empty state -->
          <VsCard v-if="!audioUrl && !loading && !error" class="text-center py-12">
            <div class="flex flex-col items-center gap-3 text-neutral-400">
              <Volume2 class="w-12 h-12" />
              <p class="text-sm">输入文字并点击生成</p>
            </div>
          </VsCard>
        </div>
      </div>
    </div>
  </MainLayout>
</template>