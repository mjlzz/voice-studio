<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Mic, MicOff, Copy, Download, Trash2, AlertCircle, Radio, CheckCircle2, FileText } from 'lucide-vue-next'
import MainLayout from '@/components/layout/MainLayout.vue'
import VsCard from '@/components/common/Card.vue'
import VsButton from '@/components/common/Button.vue'
import { useRealtimeSTT } from '@/composables/useRealtimeSTT'

// WebSocket URL - 连接到后端端口
const wsUrl = 'ws://localhost:8765/api/v1/stt/stream'

// STT Hook
const {
  isConnected,
  isListening,
  sessionId,
  results,
  partialText,
  error,
  stats,
  fullTranscript,
  displayText,
  connect,
  disconnect,
  startListening,
  stopListening,
  sendAudio,
  clearResults
} = useRealtimeSTT(wsUrl)

// 音频相关
let audioContext: AudioContext | null = null
let workletNode: AudioWorkletNode | null = null
let mediaStream: MediaStream | null = null

// 本地状态
const connectionStatus = computed(() => {
  if (!isConnected.value) return 'disconnected'
  if (isListening.value) return 'listening'
  return 'connected'
})

const statusText = computed(() => {
  switch (connectionStatus.value) {
    case 'disconnected':
      return '未连接'
    case 'connected':
      return '已连接'
    case 'listening':
      return '正在录音...'
    default:
      return '未知'
  }
})

const statusColor = computed(() => {
  switch (connectionStatus.value) {
    case 'disconnected':
      return 'text-neutral-500'
    case 'connected':
      return 'text-green-500'
    case 'listening':
      return 'text-red-500'
    default:
      return 'text-neutral-500'
  }
})

// 连接到服务器
const handleConnect = async () => {
  try {
    await connect()
  } catch (e) {
    console.error('连接失败:', e)
  }
}

// 开始录音
const startRecording = async () => {
  try {
    // 获取麦克风权限
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        sampleRate: 16000,
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    })

    // 创建音频上下文
    audioContext = new AudioContext({ sampleRate: 16000 })
    const source = audioContext.createMediaStreamSource(mediaStream)

    // 加载 AudioWorklet
    await audioContext.audioWorklet.addModule('/audio-processor.js')
    workletNode = new AudioWorkletNode(audioContext, 'audio-processor')

    // 处理音频数据
    workletNode.port.onmessage = (event) => {
      if (event.data instanceof Uint8Array) {
        sendAudio(event.data)
      }
    }

    // 连接节点
    source.connect(workletNode)
    workletNode.connect(audioContext.destination)

    // 发送开始命令
    startListening()

  } catch (e) {
    console.error('启动录音失败:', e)
    error.value = '无法访问麦克风，请检查权限设置'
  }
}

// 停止录音
const stopRecording = () => {
  // 停止音频处理
  if (workletNode) {
    workletNode.port.onmessage = null
    workletNode.disconnect()
    workletNode = null
  }

  if (audioContext) {
    audioContext.close()
    audioContext = null
  }

  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }

  // 发送停止命令
  stopListening()
}

// 复制文本
const copyText = async () => {
  if (fullTranscript.value) {
    // 句子之间用逗号连接
    const text = results.value
      .filter(r => r.type === 'final')
      .map(r => r.text)
      .join('，')
    await navigator.clipboard.writeText(text)
  }
}

// 下载文本
const downloadText = () => {
  if (fullTranscript.value) {
    // 句子之间用逗号连接
    const text = results.value
      .filter(r => r.type === 'final')
      .map(r => r.text)
      .join('，')
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transcript_${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }
}

// 清理
const cleanup = () => {
  stopRecording()
  disconnect()
}

onMounted(() => {
  handleConnect()
})

onUnmounted(() => {
  cleanup()
})
</script>

<template>
  <MainLayout>
    <div class="space-y-6">
      <!-- Page header -->
      <div>
        <h1 class="text-2xl font-semibold text-neutral-900">实时语音转文字</h1>
        <p class="text-sm text-neutral-500 mt-1">
          点击开始录音，实时转换为文字
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Left: Controls -->
        <div class="space-y-4">
          <!-- Connection status -->
          <VsCard title="连接状态">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="flex items-center gap-2">
                  <Radio class="w-4 h-4" :class="statusColor" />
                  <span class="text-sm text-neutral-600">{{ statusText }}</span>
                </div>
              </div>
              <div class="text-xs text-neutral-400">
                <CheckCircle2 v-if="isConnected" class="w-4 h-4 text-green-500 inline mr-1" />
                {{ isConnected ? '已连接' : '连接中...' }}
              </div>
            </div>
          </VsCard>

          <!-- Error message -->
          <VsCard v-if="error" class="border-red-200 bg-red-50">
            <div class="flex items-center gap-3 text-red-600">
              <AlertCircle class="w-5 h-5" />
              <div>
                <p class="text-sm font-medium">错误</p>
                <p class="text-xs text-red-500">{{ error }}</p>
              </div>
            </div>
          </VsCard>

          <!-- Microphone control -->
          <VsCard title="录音控制">
            <div class="flex flex-col items-center py-6">
              <!-- Microphone button -->
              <button
                @click="isListening ? stopRecording() : startRecording()"
                :disabled="!isConnected"
                :class="[
                  'w-20 h-20 rounded-full flex items-center justify-center transition-all duration-200',
                  isListening
                    ? 'bg-red-500 hover:bg-red-600'
                    : 'bg-primary-500 hover:bg-primary-600',
                  !isConnected && 'opacity-50 cursor-not-allowed'
                ]"
              >
                <Mic v-if="!isListening" class="w-8 h-8 text-white" />
                <MicOff v-else class="w-8 h-8 text-white" />
              </button>

              <p class="mt-4 text-sm text-neutral-600">
                {{ isListening ? '点击停止录音' : '点击开始录音' }}
              </p>

              <!-- Recording indicator -->
              <div v-if="isListening" class="mt-3 flex items-center gap-2">
                <span class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                <span class="text-xs text-red-500">录音中</span>
              </div>
            </div>
          </VsCard>

          <!-- Session stats -->
          <VsCard title="会话信息">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-neutral-500">音频时长</span>
                <p class="font-medium text-neutral-900">{{ stats.audioDuration.toFixed(1) }}s</p>
              </div>
              <div>
                <span class="text-neutral-500">转写段数</span>
                <p class="font-medium text-neutral-900">{{ results.filter(r => r.type === 'final').length }}</p>
              </div>
            </div>
          </VsCard>

          <!-- Tips -->
          <VsCard class="bg-blue-50 border-blue-200">
            <h4 class="text-sm font-medium text-blue-700 mb-2">使用提示</h4>
            <ul class="text-xs text-blue-600 space-y-1">
              <li>• 确保麦克风权限已开启</li>
              <li>• 说话时请保持正常语速</li>
              <li>• 灰色文字表示正在识别中</li>
            </ul>
          </VsCard>
        </div>

        <!-- Right: Results -->
        <div class="space-y-4">
          <!-- Error state -->
          <VsCard v-if="error" class="border-red-200 bg-red-50">
            <div class="flex items-center gap-3 text-red-600">
              <AlertCircle class="w-5 h-5" />
              <div>
                <p class="text-sm font-medium">转写出错</p>
                <p class="text-xs text-red-500">{{ error }}</p>
              </div>
            </div>
          </VsCard>

          <!-- Transcription results -->
          <VsCard title="转写结果">
            <div class="min-h-[300px] max-h-[500px] overflow-y-auto">
              <!-- Has content -->
              <div v-if="displayText" class="space-y-2">
                <!-- Final results -->
                <template v-for="result in results.filter(r => r.type === 'final')" :key="result.id">
                  <p class="text-neutral-900 leading-relaxed">{{ result.text }}</p>
                </template>
                <!-- Partial result -->
                <p v-if="partialText" class="text-neutral-400 italic">{{ partialText }}</p>
              </div>
              <!-- Empty state -->
              <div v-else class="flex flex-col items-center justify-center h-full min-h-[200px] text-neutral-400">
                <FileText class="w-12 h-12 mb-3" />
                <p class="text-sm">等待语音输入...</p>
                <p class="text-xs mt-1">点击左侧按钮开始录音</p>
              </div>
            </div>

            <!-- Actions -->
            <div v-if="fullTranscript" class="flex items-center justify-between mt-4 pt-4 border-t border-neutral-100">
              <span class="text-xs text-neutral-500">字符数: {{ fullTranscript.length }}</span>
              <div class="flex items-center gap-2">
                <VsButton variant="secondary" size="sm" @click="copyText">
                  <Copy class="w-4 h-4 mr-1" />
                  复制
                </VsButton>
                <VsButton variant="secondary" size="sm" @click="downloadText">
                  <Download class="w-4 h-4 mr-1" />
                  下载
                </VsButton>
                <VsButton variant="secondary" size="sm" @click="clearResults">
                  <Trash2 class="w-4 h-4 mr-1" />
                  清空
                </VsButton>
              </div>
            </div>
          </VsCard>
        </div>
      </div>
    </div>
  </MainLayout>
</template>