<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Upload, FileAudio, FileVideo, X } from 'lucide-vue-next'
import { formatFileSize } from '@/utils/formatTime'

const { t } = useI18n()

const emit = defineEmits<{
  upload: [file: File]
}>()

const isDragging = ref(false)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()

// 支持的音频类型
const audioTypes = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/ogg', 'audio/x-m4a', 'audio/webm']
const audioExts = /\.(wav|mp3|m4a|flac|ogg|webm)$/i

// 支持的视频类型
const videoTypes = ['video/mp4', 'video/x-m4v', 'video/x-matroska', 'video/quicktime', 'video/x-msvideo', 'video/webm']
const videoExts = /\.(mp4|mkv|avi|mov|webm|flv|wmv|m4v)$/i

const maxAudioSize = 100 * 1024 * 1024 // 100MB
const maxVideoSize = 500 * 1024 * 1024 // 500MB

const isVideoFile = (file: File): boolean => {
  return videoTypes.includes(file.type) || videoExts.test(file.name)
}

const isAudioFile = (file: File): boolean => {
  return audioTypes.includes(file.type) || audioExts.test(file.name)
}

const validateFile = (file: File): { valid: boolean; error?: string } => {
  const isVideo = isVideoFile(file)
  const isAudio = isAudioFile(file)

  if (!isVideo && !isAudio) {
    return { valid: false, error: t('stt.unsupportedFormat') }
  }

  const maxSize = isVideo ? maxVideoSize : maxAudioSize
  const maxSizeText = isVideo ? '500MB' : '100MB'

  if (file.size > maxSize) {
    return { valid: false, error: t('stt.fileSizeLimit', { limit: maxSizeText }) }
  }
  return { valid: true }
}

const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    processFile(files[0])
  }
}

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (files?.length) {
    processFile(files[0])
  }
}

const processFile = (file: File) => {
  const result = validateFile(file)
  if (result.valid) {
    selectedFile.value = file
    emit('upload', file)
  } else {
    alert(result.error)
  }
}

const clearFile = () => {
  selectedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const triggerUpload = () => {
  fileInput.value?.click()
}
</script>

<template>
  <div class="w-full">
    <!-- Drop zone -->
    <div
      v-if="!selectedFile"
      :class="[
        'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
        isDragging
          ? 'border-primary-500 bg-primary-50'
          : 'border-neutral-200 hover:border-primary-400 hover:bg-neutral-50'
      ]"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
      @click="triggerUpload"
    >
      <input
        ref="fileInput"
        type="file"
        accept="audio/*,video/*"
        class="hidden"
        @change="handleFileSelect"
      />
      <div class="flex flex-col items-center gap-3">
        <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
          <Upload class="w-6 h-6 text-primary-500" />
        </div>
        <div>
          <p class="text-sm font-medium text-neutral-700">
            {{ t('stt.dragOrClick') }}
          </p>
          <p class="text-xs text-neutral-400 mt-1">
            {{ t('stt.audioFormats') }}
          </p>
          <p class="text-xs text-neutral-400">
            {{ t('stt.videoFormats') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Selected file info -->
    <div
      v-else
      class="bg-white border border-neutral-200 rounded-xl p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg flex items-center justify-center" :class="isVideoFile(selectedFile) ? 'bg-purple-100' : 'bg-primary-100'">
            <FileVideo v-if="isVideoFile(selectedFile)" class="w-5 h-5 text-purple-500" />
            <FileAudio v-else class="w-5 h-5 text-primary-500" />
          </div>
          <div>
            <div class="flex items-center gap-2">
              <p class="text-sm font-medium text-neutral-700 truncate max-w-xs">
                {{ selectedFile.name }}
              </p>
              <span v-if="isVideoFile(selectedFile)" class="text-xs bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded">
                {{ t('stt.video') }}
              </span>
            </div>
            <p class="text-xs text-neutral-400">
              {{ formatFileSize(selectedFile.size) }}
            </p>
          </div>
        </div>
        <button
          class="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
          @click="clearFile"
        >
          <X class="w-4 h-4 text-neutral-400" />
        </button>
      </div>
    </div>
  </div>
</template>