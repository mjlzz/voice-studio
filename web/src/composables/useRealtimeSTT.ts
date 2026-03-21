/**
 * 实时语音转文字 WebSocket Hook
 */
import { ref, computed, onUnmounted } from 'vue'

export interface TranscriptionMessage {
  type: 'partial' | 'final' | 'error' | 'ready' | 'listening' | 'stopped' | 'reset'
  session_id?: string
  text?: string
  language?: string
  confidence?: number
  timestamp?: number
  duration?: number
  server_time?: number
  message?: string
  config?: {
    sample_rate: number
    model: string
  }
  stats?: {
    duration: number
    audio_duration: number
    transcription_count: number
  }
}

export interface TranscriptResult {
  id: string
  text: string
  type: 'partial' | 'final'
  timestamp: number
  duration?: number
  language?: string
  confidence?: number
}

export function useRealtimeSTT(wsUrl: string) {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isListening = ref(false)
  const sessionId = ref<string | null>(null)
  const results = ref<TranscriptResult[]>([])
  const partialText = ref('')
  const error = ref<string | null>(null)
  const stats = ref({
    duration: 0,
    audioDuration: 0,
    transcriptionCount: 0
  })

  // 完整转录文本（仅 final 结果）
  const fullTranscript = computed(() => {
    return results.value
      .filter(r => r.type === 'final')
      .map(r => r.text)
      .join(' ')
  })

  // 当前显示文本（partial + final）
  const displayText = computed(() => {
    const finals = results.value
      .filter(r => r.type === 'final')
      .map(r => r.text)
      .join('')

    if (partialText.value) {
      return finals + (finals ? ' ' : '') + partialText.value
    }
    return finals
  })

  // 连接 WebSocket
  const connect = (): Promise<void> => {
    return new Promise((resolve, reject) => {
      try {
        ws.value = new WebSocket(wsUrl)

        ws.value.onopen = () => {
          isConnected.value = true
          error.value = null
          resolve()
        }

        ws.value.onmessage = (event) => {
          const data: TranscriptionMessage = JSON.parse(event.data)
          handleMessage(data)
        }

        ws.value.onerror = (e) => {
          error.value = 'WebSocket 连接错误'
          reject(e)
        }

        ws.value.onclose = () => {
          isConnected.value = false
          isListening.value = false
          sessionId.value = null
        }
      } catch (e) {
        reject(e)
      }
    })
  }

  // 断开连接
  const disconnect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isConnected.value = false
    isListening.value = false
    sessionId.value = null
  }

  // 开始监听
  const startListening = (config?: { language?: string; model?: string }) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({
        type: 'start',
        payload: config || {}
      }))
    }
  }

  // 发送音频数据
  const sendAudio = (audioData: Uint8Array | ArrayBuffer) => {
    if (ws.value?.readyState === WebSocket.OPEN && isListening.value) {
      if (audioData instanceof ArrayBuffer) {
        ws.value.send(audioData)
      } else {
        ws.value.send(audioData.buffer)
      }
    }
  }

  // 停止监听
  const stopListening = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'stop' }))
    }
    isListening.value = false
  }

  // 重置
  const reset = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'reset' }))
    }
    results.value = []
    partialText.value = ''
  }

  // 清空结果
  const clearResults = () => {
    results.value = []
    partialText.value = ''
    error.value = null
  }

  // 处理消息
  const handleMessage = (data: TranscriptionMessage) => {
    switch (data.type) {
      case 'ready':
        sessionId.value = data.session_id || null
        break

      case 'listening':
        isListening.value = true
        break

      case 'partial':
        if (data.text) {
          partialText.value = data.text
        }
        break

      case 'final':
        if (data.text) {
          results.value.push({
            id: crypto.randomUUID(),
            text: data.text,
            type: 'final',
            timestamp: data.timestamp || 0,
            duration: data.duration,
            language: data.language,
            confidence: data.confidence
          })
          partialText.value = ''
        }
        break

      case 'stopped':
        isListening.value = false
        if (data.stats) {
          stats.value = {
            duration: data.stats.duration,
            audioDuration: data.stats.audio_duration,
            transcriptionCount: data.stats.transcription_count
          }
        }
        break

      case 'error':
        error.value = data.message || '未知错误'
        break

      case 'reset':
        results.value = []
        partialText.value = ''
        break
    }
  }

  // 组件卸载时断开连接
  onUnmounted(() => {
    disconnect()
  })

  return {
    // 状态
    isConnected,
    isListening,
    sessionId,
    results,
    partialText,
    error,
    stats,

    // 计算属性
    fullTranscript,
    displayText,

    // 方法
    connect,
    disconnect,
    startListening,
    stopListening,
    sendAudio,
    reset,
    clearResults
  }
}