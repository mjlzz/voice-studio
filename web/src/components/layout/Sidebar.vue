<script setup lang="ts">
import { useRoute } from 'vue-router'
import { Mic, Mic2, Volume2, Settings } from 'lucide-vue-next'

const route = useRoute()

const navItems = [
  { path: '/tts', label: '文字转语音', icon: Volume2 },
  { path: '/stt', label: '语音转文字', icon: Mic },
  { path: '/stt/realtime', label: '实时转写', icon: Mic2 },
  { path: '/settings', label: '设置', icon: Settings }
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
        {{ item.label }}
      </router-link>
    </nav>
  </aside>
</template>