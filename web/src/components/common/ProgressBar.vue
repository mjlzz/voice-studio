<script setup lang="ts">
import { computed } from 'vue'

defineOptions({
  name: 'VsProgressBar'
})

interface Props {
  value: number
  max?: number
  label?: string
}

const props = withDefaults(defineProps<Props>(), {
  max: 100
})

const percentage = computed(() => {
  return Math.min(Math.max((props.value / props.max) * 100, 0), 100)
})
</script>

<template>
  <div class="w-full">
    <div v-if="label" class="flex justify-between items-center mb-1">
      <span class="text-xs font-medium text-neutral-600">{{ label }}</span>
      <span class="text-xs font-medium text-neutral-500">{{ value }}%</span>
    </div>
    <div class="w-full h-2 bg-neutral-200 rounded-full overflow-hidden">
      <div
        class="h-full bg-primary-500 rounded-full transition-all duration-300"
        :style="{ width: `${percentage}%` }"
      />
    </div>
  </div>
</template>