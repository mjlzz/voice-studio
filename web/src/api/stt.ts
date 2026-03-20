import api from './index'
import type { TranscribeResult } from './types'

export interface TranscribeOptions {
  language?: string
  word_timestamps?: boolean
}

export async function transcribeAudio(
  file: File,
  options: TranscribeOptions = {}
): Promise<TranscribeResult> {
  const formData = new FormData()
  formData.append('file', file)

  const params = new URLSearchParams()
  if (options.language) {
    params.append('language', options.language)
  }
  if (options.word_timestamps !== undefined) {
    params.append('word_timestamps', String(options.word_timestamps))
  }

  const response = await api.post<TranscribeResult>(
    `/stt/transcribe?${params.toString()}`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )

  return response.data
}