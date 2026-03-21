<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import MainLayout from '@/components/layout/MainLayout.vue'
import VsCard from '@/components/common/Card.vue'
import VsToggle from '@/components/common/Toggle.vue'
import VsSpinner from '@/components/common/Spinner.vue'
import { useEngineStore } from '@/stores/engine'
import { useSettingsStore } from '@/stores/settings'
import { getHealth } from '@/api/tts'
import type { HealthResponse } from '@/api/types'
import { setUILocale, getUILocale, SUPPORTED_LOCALES, type SupportedLocale } from '@/locales'

const { t } = useI18n()

const engineStore = useEngineStore()
const settingsStore = useSettingsStore()

const health = ref<HealthResponse | null>(null)
const loading = ref(false)
const uiLanguage = ref<SupportedLocale>(getUILocale())

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

const languageOptions = SUPPORTED_LOCALES

function changeUILanguage(locale: SupportedLocale) {
  uiLanguage.value = locale
  setUILocale(locale)
}
</script>

<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Page header -->
      <div>
        <h1 class="text-2xl font-semibold text-neutral-900">{{ t('settings.title') }}</h1>
        <p class="text-sm text-neutral-500 mt-1">
          {{ t('settings.subtitle') }}
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left column -->
        <div class="space-y-4">
          <!-- Engine settings -->
          <VsCard :title="t('settings.engineConfig')">
            <div class="space-y-4">
              <!-- TTS Engine -->
              <div class="flex items-center justify-between py-2">
                <div>
                  <p class="text-sm font-medium text-neutral-700">{{ t('settings.ttsEngine') }}</p>
                  <p class="text-xs text-neutral-500">{{ t('settings.ttsEngineDesc') }}</p>
                </div>
                <div class="flex items-center gap-2 text-sm">
                  <span :class="engineStore.ttsEngine === 'cloud' ? 'text-primary-600 font-medium' : 'text-neutral-400'">
                    {{ t('settings.cloud') }}
                  </span>
                  <VsToggle
                    :model-value="engineStore.ttsEngine === 'local'"
                    @update:model-value="engineStore.setTTSEngine($event ? 'local' : 'cloud')"
                  />
                  <span :class="engineStore.ttsEngine === 'local' ? 'text-primary-600 font-medium' : 'text-neutral-400'">
                    {{ t('settings.local') }}
                  </span>
                </div>
              </div>

              <!-- Divider -->
              <div class="border-t border-neutral-100" />

              <!-- Engine info -->
              <div v-if="engineStatus" class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-neutral-500">{{ t('settings.sttEngine') }}</span>
                  <span class="text-neutral-700">{{ engineStatus.stt.current }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-neutral-500">{{ t('settings.ttsEngine') }}</span>
                  <span class="text-neutral-700">{{ engineStatus.tts.current }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-neutral-500">{{ t('settings.availableTtsEngines') }}</span>
                  <span class="text-neutral-700">{{ engineStatus.tts.available }}</span>
                </div>
              </div>
            </div>
          </VsCard>

          <!-- Default settings -->
          <VsCard :title="t('settings.defaultConfig')">
            <div class="space-y-4">
              <!-- Default voice -->
              <div class="flex items-center justify-between py-2">
                <div>
                  <p class="text-sm font-medium text-neutral-700">{{ t('settings.defaultVoice') }}</p>
                  <p class="text-xs text-neutral-500">{{ t('settings.defaultVoiceDesc') }}</p>
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
                  <p class="text-sm font-medium text-neutral-700">{{ t('settings.defaultLanguage') }}</p>
                  <p class="text-xs text-neutral-500">{{ t('settings.defaultLanguageDesc') }}</p>
                </div>
                <span class="text-sm text-neutral-600">
                  {{ settingsStore.defaultLanguage === 'zh' ? t('settings.defaultLanguage') === 'Default Language' ? 'Chinese' : '中文' : t('settings.defaultLanguage') === 'Default Language' ? 'English' : '英文' }}
                </span>
              </div>
            </div>
          </VsCard>

          <!-- UI Language settings -->
          <VsCard :title="t('settings.uiLanguage')">
            <div class="flex items-center justify-between py-2">
              <div>
                <p class="text-sm font-medium text-neutral-700">{{ t('settings.uiLanguage') }}</p>
                <p class="text-xs text-neutral-500">{{ t('settings.uiLanguageDesc') }}</p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  v-for="lang in languageOptions"
                  :key="lang.value"
                  :class="[
                    'px-3 py-1.5 text-sm rounded-lg transition-colors',
                    uiLanguage === lang.value
                      ? 'bg-primary-100 text-primary-600'
                      : 'text-neutral-600 hover:bg-neutral-100'
                  ]"
                  @click="changeUILanguage(lang.value)"
                >
                  {{ lang.label }}
                </button>
              </div>
            </div>
          </VsCard>
        </div>

        <!-- Right column -->
        <div class="space-y-4">
          <!-- System info -->
          <VsCard :title="t('settings.systemInfo')">
            <div v-if="loading" class="flex justify-center py-4">
              <VsSpinner />
            </div>
            <div v-else-if="health" class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-neutral-500">{{ t('settings.version') }}</span>
                <span class="text-neutral-700">{{ health.version }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-neutral-500">{{ t('settings.status') }}</span>
                <span class="text-green-600">{{ health.status }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-neutral-500">{{ t('settings.sttEngine') }}</span>
                <span class="text-neutral-700">{{ health.stt_engine }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-neutral-500">{{ t('settings.ttsEngine') }}</span>
                <span class="text-neutral-700">{{ health.tts_engine }}</span>
              </div>
            </div>
          </VsCard>

          <!-- About -->
          <VsCard :title="t('settings.about')">
            <div class="space-y-3 text-sm text-neutral-600">
              <p><strong>Voice Studio</strong> {{ t('settings.aboutDesc') }}</p>
              <p class="text-neutral-500">
                {{ t('settings.tagline') }}
              </p>
              <div class="pt-2 flex gap-4 text-xs text-neutral-400">
                <span>{{ t('settings.version') }} 0.1.0</span>
                <span>{{ t('settings.techStack') }}</span>
              </div>
            </div>
          </VsCard>
        </div>
      </div>
    </div>
  </MainLayout>
</template>