<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertCircle } from 'lucide-vue-next'
import MainLayout from '@/components/layout/MainLayout.vue'
import VsCard from '@/components/common/Card.vue'
import VsButton from '@/components/common/Button.vue'
import VsSpinner from '@/components/common/Spinner.vue'
import AudioUploader from '@/components/stt/AudioUploader.vue'
import TranscriptionResult from '@/components/stt/TranscriptionResult.vue'
import { transcribeAudio, getSTTLanguageSupport } from '@/api/stt'
import type { TranscribeResult } from '@/api/types'

const { t, locale } = useI18n()

const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<TranscribeResult | null>(null)
const languageSupport = ref('')

onMounted(async () => {
  try {
    const info = await getSTTLanguageSupport(locale.value)
    languageSupport.value = info.display
  } catch (e) {
    console.error('Failed to get language support:', e)
  }
})

const handleUpload = async (file: File) => {
  loading.value = true
  error.value = null
  result.value = null

  try {
    result.value = await transcribeAudio(file, {
      word_timestamps: true
    })
  } catch (e: any) {
    error.value = e.response?.data?.detail || t('error.transcribeFailed')
  } finally {
    loading.value = false
  }
}

const reset = () => {
  result.value = null
  error.value = null
}
</script>

<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Page header -->
      <div>
        <h1 class="text-2xl font-semibold text-neutral-900">{{ t('stt.title') }}</h1>
        <p class="text-sm text-neutral-500 mt-1">
          {{ t('stt.subtitle') }}
        </p>
        <p v-if="languageSupport" class="text-xs text-primary-600 mt-1">
          {{ languageSupport }}
        </p>
      </div>

      <!-- 使用 grid 保持与其他页面布局一致 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="space-y-4">
          <!-- Upload area -->
          <VsCard v-if="!result && !loading" :title="t('stt.uploadAudio')">
            <AudioUploader @upload="handleUpload" />
          </VsCard>

          <!-- Loading state -->
          <VsCard v-if="loading" :title="t('stt.transcribing')">
            <div class="flex flex-col items-center gap-4 py-8">
              <VsSpinner size="lg" />
              <p class="text-sm text-neutral-600">{{ t('stt.transcribingAudio') }}</p>
              <p class="text-xs text-neutral-400">{{ t('stt.mayTakeMinutes') }}</p>
            </div>
          </VsCard>

          <!-- Error state -->
          <VsCard v-if="error && !loading" :title="t('stt.transcribeFailed')">
            <div class="flex items-center gap-3 text-red-600">
              <AlertCircle class="w-5 h-5" />
              <div>
                <p class="text-sm font-medium">{{ t('stt.error') }}</p>
                <p class="text-xs text-red-500">{{ error }}</p>
              </div>
            </div>
            <VsButton class="mt-4" variant="secondary" @click="reset">
              {{ t('stt.retryUpload') }}
            </VsButton>
          </VsCard>
        </div>

        <!-- Right column: Result -->
        <div class="space-y-4">
          <template v-if="result && !loading">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-medium text-neutral-900">{{ t('stt.transcriptResult') }}</h2>
              <VsButton variant="secondary" size="sm" @click="reset">
                {{ t('stt.newTranscript') }}
              </VsButton>
            </div>
            <TranscriptionResult :result="result" />
          </template>

          <!-- Empty state for right column -->
          <VsCard v-if="!result && !loading" class="text-center py-12">
            <div class="flex flex-col items-center gap-3 text-neutral-400">
              <p class="text-sm">{{ t('stt.resultWillAppear') }}</p>
            </div>
          </VsCard>
        </div>
      </div>
    </div>
  </MainLayout>
</template>