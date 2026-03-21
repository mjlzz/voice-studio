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
    meta: { title: '语音转文字' }
  },
  {
    path: '/stt/realtime',
    name: 'RealtimeSTT',
    component: () => import('@/views/RealtimeSTTView.vue'),
    meta: { title: '实时语音转文字' }
  },
  {
    path: '/tts',
    name: 'TTS',
    component: () => import('@/views/TTSView.vue'),
    meta: { title: '文字转语音' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'Voice Studio'} - Voice Studio`
  next()
})

export default router