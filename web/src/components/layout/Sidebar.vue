<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Mic, Mic2, Volume2, Settings } from 'lucide-vue-next'

const route = useRoute()
const { t } = useI18n()

const navItems = [
  { path: '/tts', labelKey: 'nav.tts', icon: Volume2 },
  { path: '/stt', labelKey: 'nav.stt', icon: Mic },
  { path: '/stt/realtime', labelKey: 'nav.realtime', icon: Mic2 },
  { path: '/settings', labelKey: 'nav.settings', icon: Settings }
]
</script>

<template>
  <aside class="w-64 bg-white border-r border-neutral-200 h-full">
    <nav class="p-4 space-y-1">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        :class="[
          'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
          route.path.startsWith(item.path) && (item.path !== '/stt' || route.path === '/stt')
            ? 'bg-primary-50 text-primary-600'
            : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900'
        ]"
      >
        <component :is="item.icon" class="w-5 h-5" />
        {{ t(item.labelKey) }}
      </router-link>
    </nav>
  </aside>
</template>