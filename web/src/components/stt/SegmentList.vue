<script setup lang="ts">
import { ref } from 'vue'
import { Clock } from 'lucide-vue-next'
import type { Segment } from '@/api/types'
import { formatTime } from '@/utils/formatTime'

defineProps<{
  segments: Segment[]
}>()

const expandedSegment = ref<number | null>(null)

const toggleSegment = (id: number) => {
  expandedSegment.value = expandedSegment.value === id ? null : id
}
</script>

<template>
  <div class="bg-white border border-neutral-200 rounded-xl">
    <div class="px-4 py-3 border-b border-neutral-100">
      <h4 class="text-sm font-medium text-neutral-700">时间轴片段</h4>
    </div>
    <div class="divide-y divide-neutral-100 max-h-96 overflow-y-auto">
      <div
        v-for="segment in segments"
        :key="segment.id"
        class="px-4 py-3 hover:bg-neutral-50 cursor-pointer transition-colors"
        @click="toggleSegment(segment.id)"
      >
        <div class="flex items-start gap-3">
          <div class="flex items-center gap-1 text-xs text-neutral-400 font-mono shrink-0">
            <Clock class="w-3 h-3" />
            {{ formatTime(segment.start) }} - {{ formatTime(segment.end) }}
          </div>
          <p class="text-sm text-neutral-700 flex-1">
            {{ segment.text }}
          </p>
        </div>
        <!-- Words details -->
        <div
          v-if="expandedSegment === segment.id && segment.words?.length"
          class="mt-2 pl-8 space-y-1"
        >
          <div
            v-for="(word, idx) in segment.words"
            :key="idx"
            class="text-xs text-neutral-500 font-mono"
          >
            <span class="text-neutral-400">{{ formatTime(word.start, true) }}</span>
            <span class="mx-2">|</span>
            <span>{{ word.word }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>