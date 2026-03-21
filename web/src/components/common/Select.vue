<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'

defineOptions({
  name: 'VsSelect'
})

interface Option {
  value: string
  label: string
  disabled?: boolean
}

interface Props {
  modelValue: string
  options: Option[]
  placeholder?: string
  disabled?: boolean
}

const { t } = useI18n()

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  disabled: false
})

const resolvedPlaceholder = computed(() => props.placeholder || t('common.pleaseSelect'))

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isOpen = ref(false)
const searchQuery = ref('')

const selectedOption = computed(() => {
  return props.options.find(opt => opt.value === props.modelValue)
})

const filteredOptions = computed(() => {
  if (!searchQuery.value) return props.options
  const query = searchQuery.value.toLowerCase()
  return props.options.filter(opt =>
    opt.label.toLowerCase().includes(query)
  )
})

function selectOption(option: Option) {
  if (!option.disabled) {
    emit('update:modelValue', option.value)
    isOpen.value = false
    searchQuery.value = ''
  }
}

function toggleDropdown() {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

function closeDropdown() {
  isOpen.value = false
  searchQuery.value = ''
}

// Close on click outside
const selectRef = ref<HTMLElement>()
</script>

<template>
  <div ref="selectRef" class="relative">
    <button
      type="button"
      :disabled="disabled"
      :class="[
        'w-full flex items-center justify-between px-3 py-2 text-sm',
        'bg-white border border-neutral-200 rounded-lg',
        'hover:border-neutral-300 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
        'disabled:bg-neutral-50 disabled:text-neutral-400 disabled:cursor-not-allowed'
      ]"
      @click="toggleDropdown"
    >
      <span :class="selectedOption ? 'text-neutral-900' : 'text-neutral-400'">
        {{ selectedOption?.label || resolvedPlaceholder }}
      </span>
      <svg
        :class="[
          'w-4 h-4 text-neutral-400 transition-transform',
          isOpen ? 'rotate-180' : ''
        ]"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <div
      v-if="isOpen"
      class="absolute z-10 mt-1 w-full bg-white border border-neutral-200 rounded-lg shadow-lg max-h-60 overflow-auto"
    >
      <div class="p-2 border-b border-neutral-100">
        <input
          v-model="searchQuery"
          type="text"
          :placeholder="t('common.search')"
          class="w-full px-2 py-1.5 text-sm border border-neutral-200 rounded focus:outline-none focus:ring-1 focus:ring-primary-500"
          @click.stop
        />
      </div>
      <ul class="py-1">
        <li
          v-for="option in filteredOptions"
          :key="option.value"
          :class="[
            'px-3 py-2 text-sm cursor-pointer',
            option.disabled ? 'text-neutral-300 cursor-not-allowed' : 'hover:bg-neutral-50',
            modelValue === option.value ? 'bg-primary-50 text-primary-600' : 'text-neutral-700'
          ]"
          @click="selectOption(option)"
        >
          {{ option.label }}
        </li>
        <li v-if="filteredOptions.length === 0" class="px-3 py-2 text-sm text-neutral-400">
          {{ t('common.noMatch') }}
        </li>
      </ul>
    </div>

    <!-- Overlay to close dropdown -->
    <div
      v-if="isOpen"
      class="fixed inset-0 z-0"
      @click="closeDropdown"
    />
  </div>
</template>