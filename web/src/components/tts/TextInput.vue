<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { X } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps<{
  modelValue: string
  maxLength?: number
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const maxLength = props.maxLength || 5000
const placeholderText = props.placeholder || t('tts.inputPlaceholder')

const charCount = computed(() => props.modelValue.length)
const isOverLimit = computed(() => charCount.value > maxLength)

const updateValue = (e: Event) => {
  const target = e.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)
}

const clear = () => {
  emit('update:modelValue', '')
}
</script>

<template>
  <div class="w-full">
    <div class="relative">
      <textarea
        :value="modelValue"
        :class="[
          'w-full h-40 px-4 py-3 text-sm border rounded-lg resize-none',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
          isOverLimit
            ? 'border-red-300 bg-red-50'
            : 'border-neutral-200 bg-white hover:border-neutral-300'
        ]"
        :placeholder="placeholderText"
        @input="updateValue"
      />
      <button
        v-if="modelValue"
        class="absolute top-3 right-3 p-1 hover:bg-neutral-100 rounded"
        @click="clear"
      >
        <X class="w-4 h-4 text-neutral-400" />
      </button>
    </div>
    <div class="flex justify-end mt-1">
      <span :class="['text-xs', isOverLimit ? 'text-red-500' : 'text-neutral-400']">
        {{ charCount }} / {{ maxLength }}
      </span>
    </div>
  </div>
</template>