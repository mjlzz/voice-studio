<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import MainLayout from '@/components/layout/MainLayout.vue'
import VsCard from '@/components/common/Card.vue'
import VsToggle from '@/components/common/Toggle.vue'
import VsSpinner from '@/components/common/Spinner.vue'
import { useEngineStore } from '@/stores/engine'
import { useSettingsStore } from '@/stores/settings'
import { getHealth } from '@/api/tts'
import type { HealthResponse } from '@/api/types'

const engineStore = useEngineStore()
const settingsStore = useSettingsStore()

const health = ref<HealthResponse | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    await engineStore.fetchStatus()
    health.value = await getHealth()
  } catch (e) {
    console.error('Failed to fetch status:', e)
  } finally {
    loading.value = false
  }
})

const engineStatus = computed(() => {
  if (!engineStore.status) return null
  return {
    stt: {
      current: engineStore.status.stt.current,
      available: engineStore.status.stt.available.join(', ')
    },
    tts: {
      current: engineStore.status.tts.current,
      available: engineStore.status.tts.available.join(', ')
    }
  }
})
</script>

<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Page header -->
      <div>
        <h1 class="text-2xl font-semibold text-neutral-900">设置</h1>
        <p class="text-sm text-neutral-500 mt-1">
          配置 Voice Studio
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Engine settings -->
        <VsCard title="引擎配置">
          <div class="space-y-4">
            <!-- TTS Engine -->
            <div class="flex items-center justify-between py-2">
              <div>
                <p class="text-sm font-medium text-neutral-700">TTS 引擎</p>
                <p class="text-xs text-neutral-500">选择文字转语音引擎</p>
              </div>
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

            <!-- Divider -->
            <div class="border-t border-neutral-100" />

            <!-- Engine info -->
            <div v-if="engineStatus" class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-neutral-500">STT 引擎</span>
                <span class="text-neutral-700">{{ engineStatus.stt.current }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-neutral-500">TTS 引擎</span>
                <span class="text-neutral-700">{{ engineStatus.tts.current }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-neutral-500">可用 TTS 引擎</span>
                <span class="text-neutral-700">{{ engineStatus.tts.available }}</span>
              </div>
            </div>
          </div>
        </VsCard>

        <!-- Default settings -->
        <VsCard title="默认配置">
          <div class="space-y-4">
            <!-- Default voice -->
            <div class="flex items-center justify-between py-2">
              <div>
                <p class="text-sm font-medium text-neutral-700">默认音色</p>
                <p class="text-xs text-neutral-500">TTS 合成的默认音色</p>
              </div>
              <span class="text-sm text-neutral-600 font-mono">
                {{ settingsStore.defaultVoice }}
              </span>
            </div>

            <!-- Divider -->
            <div class="border-t border-neutral-100" />

            <!-- Default language -->
            <div class="flex items-center justify-between py-2">
              <div>
                <p class="text-sm font-medium text-neutral-700">默认语言</p>
                <p class="text-xs text-neutral-500">默认语音语言</p>
              </div>
              <span class="text-sm text-neutral-600">
                {{ settingsStore.defaultLanguage === 'zh' ? '中文' : '英文' }}
              </span>
            </div>
          </div>
        </VsCard>

        <!-- System info -->
        <VsCard title="系统信息">
          <div v-if="loading" class="flex justify-center py-4">
            <VsSpinner />
          </div>
          <div v-else-if="health" class="space-y-2 text-sm">
            <div class="flex justify-between">
              <span class="text-neutral-500">版本</span>
              <span class="text-neutral-700">{{ health.version }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-neutral-500">状态</span>
              <span class="text-green-600">{{ health.status }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-neutral-500">STT 引擎</span>
              <span class="text-neutral-700">{{ health.stt_engine }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-neutral-500">TTS 引擎</span>
              <span class="text-neutral-700">{{ health.tts_engine }}</span>
            </div>
          </div>
        </VsCard>

        <!-- About -->
        <VsCard title="关于">
          <div class="space-y-3 text-sm text-neutral-600">
            <p><strong>Voice Studio</strong> 是一个轻量、灵活、可扩展的声音处理工作台。</p>
            <p class="text-neutral-500">
              让声音创作触手可及
            </p>
            <div class="pt-2 flex gap-4 text-xs text-neutral-400">
              <span>版本 0.1.0</span>
              <span>基于 Vue 3 + FastAPI</span>
            </div>
          </div>
        </VsCard>
      </div>
    </div>
  </MainLayout>
</template>