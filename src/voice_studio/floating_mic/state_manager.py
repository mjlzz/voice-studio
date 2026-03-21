"""
状态管理器
协调悬浮话筒应用的所有组件
"""

import asyncio
import threading
from enum import Enum, auto
from typing import Optional, Callable
from dataclasses import dataclass

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from .config import FloatingMicConfig
from .audio_capture import AudioCapture, AudioConfig
from .websocket_client import WebSocketClient, TranscriptionMessage
from .batch_transcriber import BatchTranscriber, BatchTranscriptionResult
from .clipboard import copy_to_clipboard


class State(Enum):
    """应用状态"""
    IDLE = auto()
    CONNECTING = auto()
    RECORDING = auto()
    PROCESSING = auto()
    ERROR = auto()


@dataclass
class TranscriptionResult:
    """转写结果"""
    text: str
    success: bool


class StateManager(QObject):
    """状态管理器"""

    # Qt 信号
    state_changed = pyqtSignal(object)
    transcript_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    recording_finished = pyqtSignal(str)

    # 内部信号（跨线程）
    _state_update = pyqtSignal(object)
    _copy_to_clipboard = pyqtSignal(str)

    def __init__(self, config: FloatingMicConfig):
        super().__init__()

        self._config = config
        self._state = State.IDLE
        self._audio_capture: Optional[AudioCapture] = None
        self._ws_client: Optional[WebSocketClient] = None
        self._batch_transcriber: Optional[BatchTranscriber] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._loop_thread: Optional[threading.Thread] = None
        self.on_state_change: Optional[Callable[[State], None]] = None
        self._current_text: str = ""

        # 连接内部信号
        self._state_update.connect(self._handle_state_update)
        self._copy_to_clipboard.connect(self._handle_copy)

    @property
    def state(self) -> State:
        return self._state

    @property
    def current_transcript(self) -> str:
        return self._current_text

    @pyqtSlot(object)
    def _handle_state_update(self, state: State) -> None:
        """处理状态更新（主线程）"""
        self._state = state
        self.state_changed.emit(state)
        if self.on_state_change:
            try:
                self.on_state_change(state)
            except Exception as e:
                print(f"State callback error: {e}")

    @pyqtSlot(str)
    def _handle_copy(self, text: str) -> None:
        """处理剪贴板复制（主线程）"""
        if text:
            copy_to_clipboard(text)

    def _set_state(self, state: State) -> None:
        """设置状态（线程安全）"""
        self._state_update.emit(state)

    def _ensure_event_loop(self) -> None:
        """确保事件循环运行"""
        if self._loop is None or not self._loop.is_running():
            self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._loop_thread.start()
            import time
            for _ in range(100):
                if self._loop is not None:
                    break
                time.sleep(0.01)

    def _run_event_loop(self) -> None:
        """运行事件循环"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def toggle_recording(self) -> None:
        """切换录音状态"""
        if self._state == State.IDLE:
            self.start_recording()
        elif self._state == State.RECORDING:
            self.stop_recording()

    def start_recording(self) -> None:
        """开始录音"""
        if self._state != State.IDLE:
            return
        self._ensure_event_loop()

        if self._config.transcription_mode == "batch":
            self._start_batch_recording()
        else:
            asyncio.run_coroutine_threadsafe(self._do_start_streaming(), self._loop)

    async def _do_start_streaming(self) -> None:
        """执行开始录音（streaming 模式）"""
        try:
            self._set_state(State.CONNECTING)

            self._ws_client = WebSocketClient(self._config.ws_url)
            self._ws_client._on_message = self._on_ws_message

            connected = await self._ws_client.connect()
            if not connected:
                self._set_state(State.ERROR)
                self.error_occurred.emit("无法连接到语音服务，请确保后端已启动 (vs serve)")
                return

            config = {}
            if self._config.language:
                config["language"] = self._config.language

            listening = await self._ws_client.start_listening(config)
            if not listening:
                self._set_state(State.ERROR)
                self.error_occurred.emit("无法启动语音识别")
                return

            self._audio_capture = AudioCapture(
                config=AudioConfig(
                    sample_rate=self._config.sample_rate,
                    block_size_ms=self._config.audio_chunk_ms
                ),
                on_audio_chunk=self._on_audio_chunk
            )

            if not self._audio_capture.start():
                self._set_state(State.ERROR)
                self.error_occurred.emit("无法启动麦克风，请检查麦克风权限")
                await self._ws_client.disconnect()
                return

            self._current_text = ""
            self._set_state(State.RECORDING)

        except Exception as e:
            print(f"Start recording error: {e}")
            self._set_state(State.ERROR)
            self.error_occurred.emit(f"启动失败: {e}")

    def stop_recording(self) -> None:
        """停止录音"""
        if self._state != State.RECORDING:
            return
        self._set_state(State.PROCESSING)

        if self._config.transcription_mode == "batch":
            asyncio.run_coroutine_threadsafe(self._do_stop_batch(), self._loop)
        else:
            asyncio.run_coroutine_threadsafe(self._do_stop_streaming(), self._loop)

    async def _do_stop_streaming(self) -> None:
        """执行停止录音（streaming 模式）"""
        try:
            if self._audio_capture:
                self._audio_capture.stop()
                self._audio_capture = None

            if self._ws_client:
                await self._ws_client.stop_listening()
                self._current_text = self._ws_client.full_transcript
                await self._ws_client.disconnect()
                self._ws_client = None

            # 通过信号在主线程复制到剪贴板
            if self._config.auto_copy and self._current_text:
                self._copy_to_clipboard.emit(self._current_text)

            self.recording_finished.emit(self._current_text)
            self._set_state(State.IDLE)

        except Exception as e:
            print(f"Stop recording error: {e}")
            self._set_state(State.ERROR)
            self.error_occurred.emit(f"停止失败: {e}")

    def _on_audio_chunk(self, audio_data: bytes) -> None:
        """音频数据回调（streaming 模式）"""
        if self._ws_client and self._state == State.RECORDING and self._loop:
            asyncio.run_coroutine_threadsafe(
                self._ws_client.send_audio(audio_data),
                self._loop
            )

    def _start_batch_recording(self) -> None:
        """开始录音（batch 模式）"""
        asyncio.run_coroutine_threadsafe(self._do_start_batch(), self._loop)

    async def _do_start_batch(self) -> None:
        """执行开始录音（batch 模式）"""
        try:
            # 创建 BatchTranscriber
            self._batch_transcriber = BatchTranscriber(
                api_base_url=self._config.api_base_url,
                language=self._config.language
            )
            self._batch_transcriber.start_recording(self._config.sample_rate)

            # 创建 AudioCapture
            self._audio_capture = AudioCapture(
                config=AudioConfig(
                    sample_rate=self._config.sample_rate,
                    block_size_ms=self._config.audio_chunk_ms
                ),
                on_audio_chunk=self._on_audio_chunk_batch
            )

            if not self._audio_capture.start():
                self._set_state(State.ERROR)
                self.error_occurred.emit("无法启动麦克风，请检查麦克风权限")
                self._batch_transcriber = None
                return

            self._current_text = ""
            self._set_state(State.RECORDING)

        except Exception as e:
            print(f"Start batch recording error: {e}")
            self._set_state(State.ERROR)
            self.error_occurred.emit(f"启动失败: {e}")

    def _on_audio_chunk_batch(self, audio_data: bytes) -> None:
        """音频数据回调（batch 模式）"""
        if self._batch_transcriber and self._state == State.RECORDING:
            self._batch_transcriber.add_audio_chunk(audio_data)

    async def _do_stop_batch(self) -> None:
        """执行停止录音（batch 模式）"""
        try:
            # 停止音频采集
            if self._audio_capture:
                self._audio_capture.stop()
                self._audio_capture = None

            # 执行转写
            if self._batch_transcriber:
                result = await self._batch_transcriber.transcribe()

                if result.success:
                    self._current_text = result.text
                    if self._config.auto_copy and self._current_text:
                        self._copy_to_clipboard.emit(self._current_text)
                    self.recording_finished.emit(self._current_text)
                    self._set_state(State.IDLE)
                else:
                    self._set_state(State.ERROR)
                    self.error_occurred.emit(result.error or "转写失败")

                self._batch_transcriber = None
            else:
                self._set_state(State.IDLE)

        except Exception as e:
            print(f"Stop batch recording error: {e}")
            self._set_state(State.ERROR)
            self.error_occurred.emit(f"转写失败: {e}")

    def _on_ws_message(self, message: TranscriptionMessage) -> None:
        """WebSocket 消息回调"""
        if message.type == "final" and message.text:
            self._current_text = self._ws_client.full_transcript if self._ws_client else ""
            self.transcript_updated.emit(self._current_text)
        elif message.type == "partial":
            if self._ws_client:
                self.transcript_updated.emit(self._ws_client.display_text)

    def cleanup(self) -> None:
        """清理资源"""
        if self._audio_capture:
            self._audio_capture.stop()
            self._audio_capture = None
        if self._ws_client and self._loop:
            asyncio.run_coroutine_threadsafe(self._ws_client.disconnect(), self._loop)
            self._ws_client = None
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._loop = None