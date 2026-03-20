<script setup lang="ts">
import { computed } from 'vue'

defineOptions({
  name: 'VsToggle'
})

interface Props {
  modelValue: boolean
  label?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const toggle = () => {
  if (!props.disabled) {
    emit('update:modelValue', !props.modelValue)
  }
}

const bgClass = computed(() => {
  if (props.disabled) return 'bg-neutral-200'
  return props.modelValue ? 'bg-primary-500' : 'bg-neutral-300'
})

const knobClass = computed(() => {
  return props.modelValue ? 'translate-x-5' : 'translate-x-0'
})
</script>

<template>
  <button
    type="button"
    role="switch"
    :aria-checked="modelValue"
    :disabled="disabled"
    class="inline-flex items-center gap-3"
    @click="toggle"
  >
    <span
      :class="[
        'relative inline-flex h-6 w-11 flex-shrink-0 rounded-full transition-colors duration-200',
        bgClass
      ]"
    >
      <span
        :class="[
          'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200',
          knobClass,
          'mt-0.5 ml-0.5'
        ]"
      />
    </span>
    <span v-if="label" class="text-sm text-neutral-700">{{ label }}</span>
  </button>
</template>