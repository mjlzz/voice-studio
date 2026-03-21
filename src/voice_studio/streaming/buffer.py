"""
音频环形缓冲区
用于实时音频流处理
"""
import threading
from typing import Optional
import numpy as np


class AudioRingBuffer:
    """
    线程安全的环形音频缓冲区

    用于存储实时音频流，支持写入、读取和清空操作。
    """

    def __init__(
        self,
        max_duration_ms: int = 30000,
        sample_rate: int = 16000
    ):
        """
        初始化环形缓冲区

        Args:
            max_duration_ms: 最大缓冲时长（毫秒）
            sample_rate: 采样率
        """
        self._sample_rate = sample_rate
        self._max_size = int(max_duration_ms * sample_rate / 1000)
        self._buffer = np.zeros(self._max_size, dtype=np.float32)
        self._write_pos = 0
        self._data_size = 0  # 已写入数据量
        self._lock = threading.Lock()

    def write(self, audio: np.ndarray) -> int:
        """
        写入音频数据

        Args:
            audio: 音频数据 (float32, 16kHz)

        Returns:
            写入的样本数
        """
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)

        with self._lock:
            n_samples = len(audio)
            # 如果数据量超过缓冲区大小，只保留最后的数据
            if n_samples >= self._max_size:
                self._buffer[:self._max_size] = audio[-self._max_size:]
                self._write_pos = self._max_size % self._max_size
                self._data_size = self._max_size
                return self._max_size

            # 分两次写入（处理环形）
            first_chunk = min(n_samples, self._max_size - self._write_pos)
            self._buffer[self._write_pos:self._write_pos + first_chunk] = audio[:first_chunk]

            if first_chunk < n_samples:
                second_chunk = n_samples - first_chunk
                self._buffer[:second_chunk] = audio[first_chunk:]
                self._write_pos = second_chunk
            else:
                self._write_pos += first_chunk

            self._data_size = min(self._data_size + n_samples, self._max_size)
            return n_samples

    def read_all(self) -> np.ndarray:
        """
        读取所有缓冲数据

        Returns:
            音频数据 (float32)
        """
        with self._lock:
            if self._data_size == 0:
                return np.array([], dtype=np.float32)

            # 计算读取起始位置
            start_pos = (self._write_pos - self._data_size) % self._max_size

            if start_pos + self._data_size <= self._max_size:
                # 数据连续存储
                return self._buffer[start_pos:start_pos + self._data_size].copy()
            else:
                # 数据环形存储，需要拼接
                first_chunk = self._max_size - start_pos
                second_chunk = self._data_size - first_chunk
                return np.concatenate([
                    self._buffer[start_pos:],
                    self._buffer[:second_chunk]
                ])

    def read_last(self, duration_ms: int) -> np.ndarray:
        """
        读取最后指定时长的数据

        Args:
            duration_ms: 时长（毫秒）

        Returns:
            音频数据 (float32)
        """
        with self._lock:
            n_samples = int(duration_ms * self._sample_rate / 1000)
            n_samples = min(n_samples, self._data_size)

            if n_samples == 0:
                return np.array([], dtype=np.float32)

            start_pos = (self._write_pos - n_samples) % self._max_size

            if start_pos + n_samples <= self._max_size:
                return self._buffer[start_pos:start_pos + n_samples].copy()
            else:
                first_chunk = self._max_size - start_pos
                second_chunk = n_samples - first_chunk
                return np.concatenate([
                    self._buffer[start_pos:],
                    self._buffer[:second_chunk]
                ])

    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self._buffer.fill(0)
            self._write_pos = 0
            self._data_size = 0

    @property
    def duration_ms(self) -> float:
        """当前缓冲时长（毫秒）"""
        return self._data_size / self._sample_rate * 1000

    @property
    def data_size(self) -> int:
        """当前数据量（样本数）"""
        return self._data_size

    @property
    def sample_rate(self) -> int:
        """采样率"""
        return self._sample_rate

    def is_empty(self) -> bool:
        """缓冲区是否为空"""
        return self._data_size == 0