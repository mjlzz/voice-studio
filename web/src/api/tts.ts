import api from './index'
import type { Voice, VoicePresets, TTSRequest } from './types'

export async function getVoices(
  language?: string,
  engine: 'cloud' | 'local' = 'cloud'
): Promise<Voice[]> {
  const params = new URLSearchParams()
  params.append('engine', engine)
  if (language) {
    params.append('language', language)
  }

  const response = await api.get<{ voices: Voice[] }>(`/tts/voices?${params.toString()}`)
  return response.data.voices
}

export async function getPresets(): Promise<VoicePresets> {
  const response = await api.get<VoicePresets>('/tts/presets')
  return response.data
}

export async function synthesizeSpeech(
  request: TTSRequest,
  engine: 'cloud' | 'local' = 'cloud'
): Promise<Blob> {
  const response = await api.post(
    `/tts/synthesize?engine=${engine}`,
    request,
    {
      responseType: 'blob'
    }
  )
  return response.data
}

export async function getEngines() {
  const response = await api.get('/engines')
  return response.data
}

export async function getHealth() {
  const response = await api.get('/health')
  return response.data
}