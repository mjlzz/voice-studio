// STT Types
export interface Word {
  word: string
  start: number
  end: number
  probability: number
}

export interface Segment {
  id: number
  start: number
  end: number
  text: string
  words: Word[]
}

export interface TranscribeResult {
  language: string
  language_prob: number
  duration: number
  process_time: number
  rtf: number
  segments: Segment[]
  text: string
}

// TTS Types
export interface Voice {
  name: string
  short_name: string
  gender: string
  locale: string
}

export interface TTSRequest {
  text: string
  voice?: string
  engine?: 'cloud' | 'local'
  rate?: string
  volume?: string
}

export interface MixedTTSRequest {
  text: string
  length_scale?: number  // 语速控制 (0.1-3.0, 越大越慢)
  noise_scale?: number   // 随机性控制
}

export interface VoicePresets {
  cloud: {
    chinese: Record<string, string>
    english: Record<string, string>
  }
  local: {
    chinese: Record<string, string>
    english: Record<string, string>
    available_models: string[]
  }
}

// Engine Types
export interface EngineStatus {
  stt: {
    current: string
    available: string[]
    status: string
  }
  tts: {
    current: string
    available: string[]
    status: string
    local_models: string[]
  }
}

export interface HealthResponse {
  status: string
  version: string
  stt_engine: string
  tts_engine: string
}