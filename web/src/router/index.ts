import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/tts'
  },
  {
    path: '/stt',
    name: 'STT',
    component: () => import('@/views/STTView.vue'),
    meta: { titleKey: 'nav.stt' }
  },
  {
    path: '/stt/realtime',
    name: 'RealtimeSTT',
    component: () => import('@/views/RealtimeSTTView.vue'),
    meta: { titleKey: 'nav.realtime' }
  },
  {
    path: '/tts',
    name: 'TTS',
    component: () => import('@/views/TTSView.vue'),
    meta: { titleKey: 'nav.tts' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { titleKey: 'nav.settings' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((_to, _from, next) => {
  document.title = 'Voice Studio'
  next()
})

export default router