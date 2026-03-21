/**
 * Audio Worklet Processor
 * 用于实时音频处理
 *
 * 将麦克风音频转换为 16kHz 16-bit PCM 格式
 */
class AudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    // 缓冲区大小: 400ms @ 16kHz = 6400 samples
    this.bufferSize = 6400
    this.buffer = new Float32Array(this.bufferSize)
    this.writeIndex = 0
  }

  // @ts-ignore - AudioWorkletProcessor global
  bufferSize
  // @ts-ignore - AudioWorkletProcessor global
  buffer
  // @ts-ignore - AudioWorkletProcessor global
  writeIndex

  process(inputs, outputs, _parameters) {
    const input = inputs[0]
    if (input.length > 0) {
      const channelData = input[0] // 单声道

      for (let i = 0; i < channelData.length; i++) {
        this.buffer[this.writeIndex++] = channelData[i]

        if (this.writeIndex >= this.bufferSize) {
          // 转换为 16-bit PCM
          const pcmData = new Int16Array(this.bufferSize)
          for (let j = 0; j < this.bufferSize; j++) {
            // 限制范围并转换
            const sample = Math.max(-1, Math.min(1, this.buffer[j]))
            pcmData[j] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF
          }

          // 发送到主线程
          this.port.postMessage(new Uint8Array(pcmData.buffer), [pcmData.buffer])

          // 重置
          this.writeIndex = 0
        }
      }
    }
    return true // 保持处理器活跃
  }
}

registerProcessor('audio-processor', AudioProcessor)