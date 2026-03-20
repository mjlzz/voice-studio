<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Mic, Volume2, Settings, Radio } from 'lucide-vue-next'
import { useEngineStore } from '@/stores/engine'
import VsToggle from '@/components/common/Toggle.vue'

const route = useRoute()
const engineStore = useEngineStore()

const navItems = [
  { path: '/tts', name: 'TTS', label: '文字转语音', icon: Volume2 },
  { path: '/stt', name: 'STT', label: '语音转文字', icon: Mic },
  { path: '/settings', name: 'Settings', label: '设置', icon: Settings }
]

const isActive = (path: string) => {
  return route.path === path
}
</script>

<template>
  <header class="h-14 bg-white border-b border-neutral-200 flex items-center justify-between px-6">
    <!-- Logo -->
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 bg-primary-500 rounded-lg flex items-center justify-center">
        <Radio class="w-5 h-5 text-white" />
      </div>
      <span class="text-lg font-semibold text-neutral-900">Voice Studio</span>
    </div>

    <!-- Navigation -->
    <nav class="flex items-center gap-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive(item.path)
            ? 'bg-primary-50 text-primary-600'
            : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
        ]"
      >
        <component :is="item.icon" class="w-4 h-4" />
        {{ item.label }}
      </router-link>
    </nav>

    <!-- Engine Toggle -->
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-2 text-sm">
        <span :class="engineStore.ttsEngine === 'cloud' ? 'text-primary-600 font-medium' : 'text-neutral-400'">
          云端
        </span>
        <VsToggle
          :model-value="engineStore.ttsEngine === 'local'"
          @update:model-value="engineStore.setTTSEngine($event ? 'local' : 'cloud')"
        />
        <span :class="engineStore.ttsEngine === 'local' ? 'text-primary-600 font-medium' : 'text-neutral-400'">
          本地
        </span>
      </div>
    </div>
  </header>
</template>