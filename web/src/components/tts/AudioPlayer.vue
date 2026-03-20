<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Play, Pause, Download, Volume2 } from 'lucide-vue-next'
import { formatTime } from '@/utils/formatTime'

const props = defineProps<{
  src: string
  filename?: string
}>()

const audioRef = ref<HTMLAudioElement>()
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1)

const progress = computed(() => {
  if (duration.value === 0) return 0
  return (currentTime.value / duration.value) * 100
})

const togglePlay = () => {
  if (!audioRef.value) return

  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
}

const onPlay = () => {
  isPlaying.value = true
}

const onPause = () => {
  isPlaying.value = false
}

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
  }
}

const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
}

const seek = (e: MouseEvent) => {
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  if (audioRef.value) {
    audioRef.value.currentTime = percent * duration.value
  }
}

const handleVolumeChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  volume.value = parseFloat(target.value)
  if (audioRef.value) {
    audioRef.value.volume = volume.value
  }
}

const download = () => {
  const a = document.createElement('a')
  a.href = props.src
  a.download = props.filename || 'speech.mp3'
  a.click()
}

// Reset when src changes
watch(() => props.src, () => {
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0
})
</script>

<template>
  <div class="bg-white border border-neutral-200 rounded-xl p-4">
    <audio
      ref="audioRef"
      :src="src"
      @play="onPlay"
      @pause="onPause"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
    />

    <div class="flex items-center gap-4">
      <!-- Play button -->
      <button
        class="w-10 h-10 bg-primary-500 hover:bg-primary-600 rounded-full flex items-center justify-center transition-colors"
        @click="togglePlay"
      >
        <Play v-if="!isPlaying" class="w-5 h-5 text-white ml-0.5" />
        <Pause v-else class="w-5 h-5 text-white" />
      </button>

      <!-- Progress bar -->
      <div class="flex-1">
        <div
          class="h-2 bg-neutral-200 rounded-full cursor-pointer"
          @click="seek"
        >
          <div
            class="h-full bg-primary-500 rounded-full transition-all"
            :style="{ width: `${progress}%` }"
          />
        </div>
        <div class="flex justify-between mt-1">
          <span class="text-xs text-neutral-400 font-mono">
            {{ formatTime(currentTime) }}
          </span>
          <span class="text-xs text-neutral-400 font-mono">
            {{ formatTime(duration) }}
          </span>
        </div>
      </div>

      <!-- Volume -->
      <div class="flex items-center gap-2">
        <Volume2 class="w-4 h-4 text-neutral-400" />
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          :value="volume"
          class="w-20 h-1 bg-neutral-200 rounded-full appearance-none cursor-pointer"
          @input="handleVolumeChange"
        />
      </div>

      <!-- Download -->
      <button
        class="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
        title="下载音频"
        @click="download"
      >
        <Download class="w-5 h-5 text-neutral-600" />
      </button>
    </div>
  </div>
</template>