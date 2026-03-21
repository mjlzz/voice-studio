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

router.beforeEach((to, _from, next) => {
  // Use a default title, will be updated by the component after i18n is ready
  document.title = `${to.meta.titleKey || 'Voice Studio'} - Voice Studio`
  next()
})

export default router