<script setup lang="ts">
import { ref } from 'vue'
import { Upload, FileAudio, X } from 'lucide-vue-next'
import { formatFileSize } from '@/utils/formatTime'

const emit = defineEmits<{
  upload: [file: File]
}>()

const isDragging = ref(false)
const selectedFile = ref<File | null>(null)
const fileInput = ref<HTMLInputElement>()

const validTypes = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/flac', 'audio/ogg', 'audio/x-m4a', 'audio/webm']
const maxSize = 100 * 1024 * 1024 // 100MB

const validateFile = (file: File): { valid: boolean; error?: string } => {
  if (!validTypes.includes(file.type) && !file.name.match(/\.(wav|mp3|m4a|flac|ogg|webm)$/i)) {
    return { valid: false, error: '不支持的音频格式' }
  }
  if (file.size > maxSize) {
    return { valid: false, error: '文件大小超过 100MB 限制' }
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
        accept="audio/*"
        class="hidden"
        @change="handleFileSelect"
      />
      <div class="flex flex-col items-center gap-3">
        <div class="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
          <Upload class="w-6 h-6 text-primary-500" />
        </div>
        <div>
          <p class="text-sm font-medium text-neutral-700">
            拖拽音频文件到这里，或点击上传
          </p>
          <p class="text-xs text-neutral-400 mt-1">
            支持 WAV, MP3, M4A, FLAC, OGG 格式，最大 100MB
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
          <div class="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <FileAudio class="w-5 h-5 text-primary-500" />
          </div>
          <div>
            <p class="text-sm font-medium text-neutral-700 truncate max-w-xs">
              {{ selectedFile.name }}
            </p>
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