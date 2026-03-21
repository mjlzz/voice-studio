"""
WebSocket 会话管理
处理实时 STT 的 WebSocket 连接
"""
import asyncio
import time
import uuid
import json
import threading
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import numpy as np

from fastapi import WebSocket, WebSocketDisconnect

from .engine import StreamingSTTEngine, TranscriptionChunk, TranscriptionType


@dataclass
class STTSession:
    """
    STT 会话

    管理 WebSocket 连接和转写引擎的生命周期。
    """

    session_id: str
    websocket: WebSocket
    engine: Optional[StreamingSTTEngine] = None
    is_active: bool = False
    created_at: float = field(default_factory=time.time)
    language: Optional[str] = None
    model: str = "base"
    sample_rate: int = 16000

    # 统计信息
    _total_audio_bytes: int = 0
    _transcription_count: int = 0

    async def start(self, config: Optional[Dict[str, Any]] = None):
        """
        启动会话

        Args:
            config: 配置参数
        """
        if config:
            self.language = config.get("language")
            self.model = config.get("model", "base")
            self.sample_rate = config.get("sample_rate", 16000)

        self.engine = StreamingSTTEngine(
            model_size=self.model,
            vad_threshold=config.get("vad_threshold", 0.5) if config else 0.5,
            min_silence_ms=config.get("min_silence_ms", 500) if config else 500,
            sample_rate=self.sample_rate,
        )

        def on_result(chunk: TranscriptionChunk):
            """转写结果回调"""
            asyncio.run_coroutine_threadsafe(
                self._send_transcription(chunk),
                asyncio.get_event_loop()
            )

        self.engine.start(on_result=on_result)
        self.is_active = True

    async def process_audio(self, audio_data: bytes):
        """
        处理接收到的音频数据

        Args:
            audio_data: PCM 音频数据 (16-bit, 16kHz, 单声道)
        """
        if not self.is_active or self.engine is None:
            return

        self._total_audio_bytes += len(audio_data)

        # 转换为 numpy 数组
        audio = np.frombuffer(audio_data, dtype=np.int16)

        # 在线程池中处理（避免阻塞事件循环）
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.engine.process_audio,
            audio,
            self.sample_rate
        )

        if result:
            await self._send_transcription(result)

    async def _send_transcription(self, chunk: TranscriptionChunk):
        """
        发送转写结果

        Args:
            chunk: 转写结果块
        """
        try:
            message = {
                "type": chunk.type.value,
                "session_id": self.session_id,
                "text": chunk.text,
                "language": chunk.language,
                "confidence": round(chunk.confidence, 3),
                "timestamp": round(chunk.start_time, 3),
                "duration": round(chunk.end_time - chunk.start_time, 3),
                "server_time": time.time(),
            }

            await self.websocket.send_json(message)
            self._transcription_count += 1

        except Exception as e:
            print(f"发送转写结果失败: {e}")

    async def stop(self):
        """停止会话"""
        if self.engine:
            # 获取最终结果
            result = self.engine.force_finalize()
            if result:
                await self._send_transcription(result)
            self.engine.stop()

        self.is_active = False

    async def close(self):
        """关闭会话"""
        await self.stop()
        self.engine = None

    def get_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        duration = time.time() - self.created_at
        audio_duration = self._total_audio_bytes / 2 / self.sample_rate  # 16-bit = 2 bytes

        return {
            "session_id": self.session_id,
            "status": "active" if self.is_active else "inactive",
            "duration": round(duration, 2),
            "audio_duration": round(audio_duration, 2),
            "transcription_count": self._transcription_count,
            "language": self.language,
            "model": self.model,
        }


class SessionManager:
    """
    会话管理器

    管理所有活跃的 STT 会话。
    """

    _sessions: Dict[str, STTSession] = {}
    _lock = threading.Lock()

    @classmethod
    def create_session(cls, websocket: WebSocket) -> STTSession:
        """
        创建新会话

        Args:
            websocket: WebSocket 连接

        Returns:
            新创建的会话
        """
        session_id = str(uuid.uuid4())[:8]
        session = STTSession(
            session_id=session_id,
            websocket=websocket,
        )

        with cls._lock:
            cls._sessions[session_id] = session

        return session

    @classmethod
    def get_session(cls, session_id: str) -> Optional[STTSession]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            会话对象或 None
        """
        with cls._lock:
            return cls._sessions.get(session_id)

    @classmethod
    def remove_session(cls, session_id: str):
        """
        移除会话

        Args:
            session_id: 会话 ID
        """
        with cls._lock:
            session = cls._sessions.pop(session_id, None)
            if session:
                asyncio.create_task(session.close())

    @classmethod
    def get_all_sessions(cls) -> Dict[str, Dict[str, Any]]:
        """
        获取所有会话信息

        Returns:
            会话信息字典
        """
        with cls._lock:
            return {
                sid: session.get_stats()
                for sid, session in cls._sessions.items()
            }

    @classmethod
    def get_active_count(cls) -> int:
        """获取活跃会话数量"""
        with cls._lock:
            return sum(1 for s in cls._sessions.values() if s.is_active)


async def handle_stt_websocket(websocket: WebSocket):
    """
    处理 STT WebSocket 连接

    Args:
        websocket: WebSocket 连接
    """
    await websocket.accept()

    session = SessionManager.create_session(websocket)

    try:
        # 发送就绪消息
        await websocket.send_json({
            "type": "ready",
            "session_id": session.session_id,
            "message": "WebSocket connected, waiting for start command",
        })

        while True:
            # 接收消息
            message = await websocket.receive()

            if message["type"] == "websocket.receive":
                if "text" in message:
                    # JSON 控制消息
                    try:
                        data = json.loads(message["text"])
                        await handle_control_message(session, data)
                    except json.JSONDecodeError:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Invalid JSON message",
                        })

                elif "bytes" in message:
                    # 二进制音频数据
                    if session.is_active:
                        await session.process_audio(message["bytes"])
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Session not started, send start command first",
                        })

            elif message["type"] == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except:
            pass

    finally:
        SessionManager.remove_session(session.session_id)


async def handle_control_message(session: STTSession, data: Dict[str, Any]):
    """
    处理控制消息

    Args:
        session: 会话对象
        data: 消息数据
    """
    msg_type = data.get("type")

    if msg_type == "start":
        # 启动会话
        config = data.get("payload", {})
        await session.start(config)

        await session.websocket.send_json({
            "type": "listening",
            "session_id": session.session_id,
            "config": {
                "sample_rate": session.sample_rate,
                "model": session.model,
            },
        })

    elif msg_type == "stop":
        # 停止会话
        await session.stop()

        await session.websocket.send_json({
            "type": "stopped",
            "session_id": session.session_id,
            "stats": session.get_stats(),
        })

    elif msg_type == "reset":
        # 重置会话
        if session.engine:
            session.engine.reset()

        await session.websocket.send_json({
            "type": "reset",
            "session_id": session.session_id,
        })

    elif msg_type == "config":
        # 更新配置（需要先停止再重新启动）
        if session.is_active:
            await session.websocket.send_json({
                "type": "error",
                "message": "Cannot change config while session is active",
            })
        else:
            config = data.get("payload", {})
            session.language = config.get("language")
            session.model = config.get("model", session.model)
            session.sample_rate = config.get("sample_rate", session.sample_rate)

            await session.websocket.send_json({
                "type": "config_updated",
                "session_id": session.session_id,
            })

    else:
        await session.websocket.send_json({
            "type": "error",
            "message": f"Unknown message type: {msg_type}",
        })