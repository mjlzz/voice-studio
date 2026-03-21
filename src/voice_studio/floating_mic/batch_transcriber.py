"""
录音后转写处理器
负责收集音频数据、保存 WAV 文件、调用 HTTP API
"""

import tempfile
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiohttp


@dataclass
class BatchTranscriptionResult:
    """转写结果"""
    text: str
    language: str
    duration: float
    success: bool
    error: Optional[str] = None


class BatchTranscriber:
    """录音后转写处理器"""

    def __init__(
        self,
        api_base_url: str = "http://localhost:8765",
        language: Optional[str] = None
    ):
        self._api_base_url = api_base_url.rstrip('/')
        self._language = language

        # 音频缓冲区
        self._audio_chunks: list[bytes] = []
        self._sample_rate: int = 16000
        self._channels: int = 1
        self._sample_width: int = 2  # 16-bit = 2 bytes

    @property
    def chunk_count(self) -> int:
        """已收集的音频块数量"""
        return len(self._audio_chunks)

    @property
    def audio_duration_ms(self) -> float:
        """当前音频时长（毫秒）"""
        total_bytes = sum(len(chunk) for chunk in self._audio_chunks)
        # 每个采样点 2 bytes，16000 采样率
        return (total_bytes / 2 / self._sample_rate) * 1000

    def start_recording(self, sample_rate: int = 16000) -> None:
        """开始录音，重置缓冲区"""
        self._sample_rate = sample_rate
        self._audio_chunks.clear()

    def add_audio_chunk(self, audio_data: bytes) -> None:
        """添加音频数据块"""
        self._audio_chunks.append(audio_data)

    def cancel_recording(self) -> None:
        """取消录音，清空缓冲区"""
        self._audio_chunks.clear()

    def _create_wav_file(self) -> Path:
        """创建 WAV 临时文件"""
        # 创建临时文件
        temp_fd, temp_path = tempfile.mkstemp(suffix=".wav")

        # 合并所有音频数据
        all_audio = b''.join(self._audio_chunks)

        # 写入 WAV 文件
        with wave.open(temp_path, 'wb') as wav_file:
            wav_file.setnchannels(self._channels)
            wav_file.setsampwidth(self._sample_width)
            wav_file.setframerate(self._sample_rate)
            wav_file.writeframes(all_audio)

        return Path(temp_path)

    async def transcribe(self) -> BatchTranscriptionResult:
        """执行转写"""
        if not self._audio_chunks:
            return BatchTranscriptionResult(
                text="",
                language="",
                duration=0,
                success=False,
                error="没有录音数据"
            )

        temp_path = None
        try:
            # 创建 WAV 文件
            temp_path = self._create_wav_file()

            # 调用 HTTP API
            url = f"{self._api_base_url}/api/v1/stt/transcribe"

            async with aiohttp.ClientSession() as session:
                with open(temp_path, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field(
                        'file',
                        f,
                        filename='recording.wav',
                        content_type='audio/wav'
                    )

                    params = {}
                    if self._language:
                        params['language'] = self._language

                    async with session.post(url, data=form_data, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            return BatchTranscriptionResult(
                                text=result.get('text', ''),
                                language=result.get('language', ''),
                                duration=result.get('duration', 0),
                                success=True
                            )
                        else:
                            try:
                                error_data = await response.json()
                                error_msg = error_data.get('message', f'HTTP {response.status}')
                            except Exception:
                                error_msg = f'HTTP {response.status}'
                            return BatchTranscriptionResult(
                                text="",
                                language="",
                                duration=0,
                                success=False,
                                error=error_msg
                            )

        except Exception as e:
            return BatchTranscriptionResult(
                text="",
                language="",
                duration=0,
                success=False,
                error=str(e)
            )

        finally:
            # 清理临时文件
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            # 清空缓冲区
            self._audio_chunks.clear()