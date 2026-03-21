"""
音频采集模块
使用 sounddevice 进行音频采集
"""

import queue
import threading
from typing import Callable, Optional
from dataclasses import dataclass

import numpy as np


@dataclass
class AudioConfig:
    """音频配置"""
    sample_rate: int = 16000
    channels: int = 1
    block_size_ms: int = 100  # 每块时长(毫秒)
    dtype: str = "int16"


class AudioCapture:
    """音频采集器"""

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        on_audio_chunk: Optional[Callable[[bytes], None]] = None
    ):
        self._config = config or AudioConfig()
        self._on_audio_chunk = on_audio_chunk

        self._stream = None
        self._running = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def sample_rate(self) -> int:
        return self._config.sample_rate

    def start(self) -> bool:
        """
        开始音频采集

        Returns:
            是否成功启动
        """
        if self._running:
            return True

        try:
            import sounddevice as sd

            block_size = int(self._config.sample_rate * self._config.block_size_ms / 1000)

            self._stream = sd.InputStream(
                samplerate=self._config.sample_rate,
                channels=self._config.channels,
                dtype=self._config.dtype,
                callback=self._audio_callback,
                blocksize=block_size,
                latency="low"
            )

            self._stream.start()
            self._running = True
            return True

        except Exception as e:
            print(f"音频采集启动失败: {e}")
            self._running = False
            return False

    def stop(self) -> None:
        """停止音频采集"""
        self._running = False

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        """
        音频回调函数

        Args:
            indata: 输入音频数据
            frames: 帧数
            time: 时间信息
            status: 状态
        """
        if not self._running:
            return

        if status:
            print(f"音频状态: {status}")

        # 转换为 bytes (已经是 int16)
        audio_bytes = indata.tobytes()

        if self._on_audio_chunk:
            try:
                self._on_audio_chunk(audio_bytes)
            except Exception as e:
                print(f"音频回调错误: {e}")

    @staticmethod
    def list_devices() -> list:
        """
        列出所有音频输入设备

        Returns:
            设备列表
        """
        try:
            import sounddevice as sd
            devices = []
            for i, dev in enumerate(sd.query_devices()):
                if dev['max_input_channels'] > 0:
                    devices.append({
                        'id': i,
                        'name': dev['name'],
                        'channels': dev['max_input_channels'],
                        'sample_rate': dev['default_samplerate']
                    })
            return devices
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []

    @staticmethod
    def get_default_device() -> Optional[dict]:
        """获取默认输入设备"""
        try:
            import sounddevice as sd
            dev = sd.query_devices(kind='input')
            return {
                'name': dev['name'],
                'channels': dev['max_input_channels'],
                'sample_rate': dev['default_samplerate']
            }
        except Exception:
            return None