<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { Copy, Download, FileText } from 'lucide-vue-next'
import type { TranscribeResult, Segment } from '@/api/types'
import { formatTime } from '@/utils/formatTime'
import VsButton from '@/components/common/Button.vue'
import SegmentList from './SegmentList.vue'

const { t } = useI18n()

const props = defineProps<{
  result: TranscribeResult
}>()

const copyText = async () => {
  try {
    await navigator.clipboard.writeText(props.result.text)
    alert(t('stt.copied'))
  } catch (e) {
    console.error('Copy failed:', e)
  }
}

const downloadText = () => {
  const blob = new Blob([props.result.text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'transcription.txt'
  a.click()
  URL.revokeObjectURL(url)
}

const downloadJson = () => {
  const blob = new Blob([JSON.stringify(props.result, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'transcription.json'
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Format seconds to SRT time format: HH:MM:SS,mmm
 */
const formatSrtTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  const ms = Math.floor((seconds % 1) * 1000)

  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`
}

/**
 * Generate SRT content from segments
 */
const generateSrt = (segments: Segment[]): string => {
  return segments
    .map((segment, index) => {
      const startTime = formatSrtTime(segment.start)
      const endTime = formatSrtTime(segment.end)
      return `${index + 1}\n${startTime} --> ${endTime}\n${segment.text}`
    })
    .join('\n\n')
}

const downloadSrt = () => {
  const srtContent = generateSrt(props.result.segments)
  const blob = new Blob([srtContent], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'transcription.srt'
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div class="space-y-4">
    <!-- Stats -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-neutral-50 rounded-lg p-3">
        <p class="text-xs text-neutral-500">{{ t('stt.language') }}</p>
        <p class="text-sm font-medium text-neutral-700">{{ result.language.toUpperCase() }}</p>
      </div>
      <div class="bg-neutral-50 rounded-lg p-3">
        <p class="text-xs text-neutral-500">{{ t('stt.duration') }}</p>
        <p class="text-sm font-medium text-neutral-700">{{ formatTime(result.duration) }}</p>
      </div>
      <div class="bg-neutral-50 rounded-lg p-3">
        <p class="text-xs text-neutral-500">{{ t('stt.processTime') }}</p>
        <p class="text-sm font-medium text-neutral-700">{{ result.process_time.toFixed(1) }}s</p>
      </div>
      <div class="bg-neutral-50 rounded-lg p-3">
        <p class="text-xs text-neutral-500">RTF</p>
        <p class="text-sm font-medium text-neutral-700">{{ result.rtf.toFixed(2) }}x</p>
      </div>
    </div>

    <!-- Full text -->
    <div class="bg-white border border-neutral-200 rounded-xl p-4">
      <div class="flex items-center justify-between mb-3">
        <h4 class="text-sm font-medium text-neutral-700">{{ t('stt.transcriptText') }}</h4>
        <div class="flex gap-2">
          <VsButton size="sm" variant="ghost" @click="copyText">
            <Copy class="w-4 h-4" />
            {{ t('stt.copy') }}
          </VsButton>
          <VsButton size="sm" variant="ghost" @click="downloadText">
            <Download class="w-4 h-4" />
            TXT
          </VsButton>
          <VsButton size="sm" variant="ghost" @click="downloadSrt">
            <FileText class="w-4 h-4" />
            SRT
          </VsButton>
          <VsButton size="sm" variant="ghost" @click="downloadJson">
            <Download class="w-4 h-4" />
            JSON
          </VsButton>
        </div>
      </div>
      <p class="text-sm text-neutral-600 leading-relaxed whitespace-pre-wrap">
        {{ result.text }}
      </p>
    </div>

    <!-- Segments -->
    <SegmentList :segments="result.segments" />
  </div>
</template>