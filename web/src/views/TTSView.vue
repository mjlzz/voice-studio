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
import { useEngineStore, type TTSEngineType } from '@/stores/engine'
import { useSettingsStore } from '@/stores/settings'
import { synthesizeSpeech, synthesizeMixedSpeech } from '@/api/tts'

const engineStore = useEngineStore()
const settingsStore = useSettingsStore()

const text = ref('')
const voice = ref('')
const loading = ref(false)
const error = ref<string | null>(null)
const audioUrl = ref<string | null>(null)

const canSynthesize = computed(() => {
  if (engineStore.isMixed) {
    return text.value.trim() && !loading.value
  }
  return text.value.trim() && voice.value && !loading.value
})

// Engine options
const engineOptions: { value: TTSEngineType; label: string; desc: string }[] = [
  { value: 'cloud', label: '云端', desc: '在线多音色' },
  { value: 'local', label: '本地', desc: '离线Piper' },
  { value: 'mixed', label: '中英混合', desc: '离线多语言' }
]

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

// Mixed TTS speed control
const mixedSpeed = ref(1.0)
const speedLabels = [
  { label: '0.5x', value: 0.5 },
  { label: '0.75x', value: 0.75 },
  { label: '1.0x', value: 1.0 },
  { label: '1.25x', value: 1.25 },
  { label: '1.5x', value: 1.5 },
  { label: '2.0x', value: 2.0 }
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
    let blob: Blob
    if (engineStore.isMixed) {
      // Mixed TTS
      blob = await synthesizeMixedSpeech({
        text: text.value,
        length_scale: 1.0 / mixedSpeed.value  // 转换: speed越大越快，length_scale越大越慢
      })
    } else {
      // Cloud or Local TTS
      blob = await synthesizeSpeech(
        {
          text: text.value,
          voice: voice.value,
          rate: rate.value,
          volume: volume.value
        },
        engineStore.ttsEngine as 'cloud' | 'local'
      )
    }
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

// Get file extension based on engine
const audioExtension = computed(() => {
  if (engineStore.isMixed) return 'wav'
  if (engineStore.isCloud) return 'mp3'
  return 'wav'
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
          <!-- Engine selector -->
          <VsCard title="选择引擎">
            <div class="flex gap-2">
              <button
                v-for="opt in engineOptions"
                :key="opt.value"
                :class="[
                  'flex-1 px-3 py-2 text-sm rounded-lg border transition-colors',
                  engineStore.ttsEngine === opt.value
                    ? 'border-primary-500 bg-primary-50 text-primary-600'
                    : 'border-neutral-200 hover:border-primary-300'
                ]"
                @click="engineStore.setTTSEngine(opt.value)"
              >
                <div class="font-medium">{{ opt.label }}</div>
                <div class="text-xs text-neutral-500">{{ opt.desc }}</div>
              </button>
            </div>
          </VsCard>

          <!-- Text input -->
          <VsCard title="输入文字">
            <TextInput v-model="text" :placeholder="engineStore.isMixed ? '支持中英文混合输入，如：欢迎使用voice studio' : undefined" />
          </VsCard>

          <!-- Voice selector (not for mixed mode) -->
          <VsCard v-if="!engineStore.isMixed" title="选择音色">
            <VoiceSelector v-model="voice" />
          </VsCard>

          <!-- Mixed mode voice info -->
          <VsCard v-if="engineStore.isMixed" title="音色信息">
            <div class="flex items-center gap-3 p-3 bg-primary-50 rounded-lg">
              <div class="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center">
                <Volume2 class="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <p class="text-sm font-medium text-neutral-700">默认音色</p>
                <p class="text-xs text-neutral-500">中英混合模式使用统一的默认音色，支持中英文无缝切换</p>
              </div>
            </div>
          </VsCard>

          <!-- Speed control for mixed mode -->
          <VsCard v-if="engineStore.isMixed" title="语速调节">
            <div class="flex gap-2">
              <button
                v-for="opt in speedLabels"
                :key="opt.value"
                :class="[
                  'px-3 py-2 text-sm rounded-lg border transition-colors',
                  mixedSpeed === opt.value
                    ? 'border-primary-500 bg-primary-50 text-primary-600'
                    : 'border-neutral-200 hover:border-primary-300'
                ]"
                @click="mixedSpeed = opt.value"
              >
                {{ opt.label }}
              </button>
            </div>
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
              :filename="`speech.${audioExtension}`"
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