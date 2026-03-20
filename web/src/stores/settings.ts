import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const defaultVoice = ref<string>('zh-CN-XiaoxiaoNeural')
  const defaultLanguage = ref<string>('zh')
  const theme = ref<'light' | 'dark'>('light')

  // Load from localStorage
  function load() {
    const saved = localStorage.getItem('voice-studio-settings')
    if (saved) {
      try {
        const data = JSON.parse(saved)
        defaultVoice.value = data.defaultVoice || defaultVoice.value
        defaultLanguage.value = data.defaultLanguage || defaultLanguage.value
        theme.value = data.theme || theme.value
      } catch (e) {
        console.error('Failed to load settings:', e)
      }
    }
  }

  // Save to localStorage
  function save() {
    localStorage.setItem('voice-studio-settings', JSON.stringify({
      defaultVoice: defaultVoice.value,
      defaultLanguage: defaultLanguage.value,
      theme: theme.value
    }))
  }

  function setDefaultVoice(voice: string) {
    defaultVoice.value = voice
    save()
  }

  function setDefaultLanguage(lang: string) {
    defaultLanguage.value = lang
    save()
  }

  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    save()
  }

  // Load on init
  load()

  return {
    defaultVoice,
    defaultLanguage,
    theme,
    setDefaultVoice,
    setDefaultLanguage,
    toggleTheme
  }
})