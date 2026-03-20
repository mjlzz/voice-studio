<script setup lang="ts">
defineOptions({
  name: 'VsCard'
})

interface Props {
  title?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

withDefaults(defineProps<Props>(), {
  padding: 'md'
})

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6'
}
</script>

<template>
  <div class="bg-white rounded-xl shadow-card">
    <div v-if="title" class="px-4 py-3 border-b border-neutral-100">
      <h3 class="text-sm font-medium text-neutral-800">{{ title }}</h3>
    </div>
    <div :class="paddingClasses[padding]">
      <slot />
    </div>
  </div>
</template>