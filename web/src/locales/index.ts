import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN.json'
import enUS from './en-US.json'
import jaJP from './ja-JP.json'

export type MessageSchema = typeof zhCN

export const SUPPORTED_LOCALES = [
  { value: 'zh-CN', label: '中文' },
  { value: 'en-US', label: 'English' },
  { value: 'ja-JP', label: '日本語' }
] as const

export type SupportedLocale = typeof SUPPORTED_LOCALES[number]['value']

// Get saved language from localStorage or use browser language
function getDefaultLocale(): SupportedLocale {
  const saved = localStorage.getItem('voice-studio-ui-language')
  if (saved && SUPPORTED_LOCALES.some(l => l.value === saved)) {
    return saved as SupportedLocale
  }

  // Try to match browser language
  const browserLang = navigator.language
  if (browserLang.startsWith('zh')) return 'zh-CN'
  if (browserLang.startsWith('ja')) return 'ja-JP'
  if (browserLang.startsWith('en')) return 'en-US'

  return 'zh-CN'
}

const i18n = createI18n<[MessageSchema], SupportedLocale>({
  legacy: false,
  locale: getDefaultLocale(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP
  }
})

export function setUILocale(locale: SupportedLocale) {
  (i18n.global.locale as unknown as { value: SupportedLocale }).value = locale
  localStorage.setItem('voice-studio-ui-language', locale)
}

export function getUILocale(): SupportedLocale {
  return (i18n.global.locale as unknown as { value: SupportedLocale }).value as SupportedLocale
}

export default i18n