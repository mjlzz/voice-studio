<script setup lang="ts">
import { ref } from 'vue'
import { AlertCircle } from 'lucide-vue-next'
import MainLayout from '@/components/layout/MainLayout.vue'
import VsCard from '@/components/common/Card.vue'
import VsButton from '@/components/common/Button.vue'
import VsSpinner from '@/components/common/Spinner.vue'
import AudioUploader from '@/components/stt/AudioUploader.vue'
import TranscriptionResult from '@/components/stt/TranscriptionResult.vue'
import { transcribeAudio } from '@/api/stt'
import type { TranscribeResult } from '@/api/types'

const loading = ref(false)
const error = ref<string | null>(null)
const result = ref<TranscribeResult | null>(null)

const handleUpload = async (file: File) => {
  loading.value = true
  error.value = null
  result.value = null

  try {
    result.value = await transcribeAudio(file, {
      word_timestamps: true
    })
  } catch (e: any) {
    error.value = e.response?.data?.detail || '转录失败，请重试'
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
        <h1 class="text-2xl font-semibold text-neutral-900">语音转文字</h1>
        <p class="text-sm text-neutral-500 mt-1">
          上传音频文件，自动转换为文字
        </p>
      </div>

      <!-- Upload area -->
      <VsCard v-if="!result && !loading" title="上传音频">
        <AudioUploader @upload="handleUpload" />
      </VsCard>

      <!-- Loading state -->
      <VsCard v-if="loading" class="text-center py-12">
        <div class="flex flex-col items-center gap-4">
          <VsSpinner size="lg" />
          <p class="text-sm text-neutral-600">正在转录音频...</p>
          <p class="text-xs text-neutral-400">这可能需要几分钟，请耐心等待</p>
        </div>
      </VsCard>

      <!-- Error state -->
      <VsCard v-if="error && !loading" class="border-red-200 bg-red-50">
        <div class="flex items-center gap-3 text-red-600">
          <AlertCircle class="w-5 h-5" />
          <div>
            <p class="text-sm font-medium">转录失败</p>
            <p class="text-xs text-red-500">{{ error }}</p>
          </div>
        </div>
        <VsButton class="mt-4" variant="secondary" @click="reset">
          重新上传
        </VsButton>
      </VsCard>

      <!-- Result -->
      <div v-if="result && !loading">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-medium text-neutral-900">转录结果</h2>
          <VsButton variant="secondary" @click="reset">
            新的转录
          </VsButton>
        </div>
        <TranscriptionResult :result="result" />
      </div>
    </div>
  </MainLayout>
</template>