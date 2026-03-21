"""
WebSocket 客户端
与后端 STT 服务通信
"""

import asyncio
import json
import threading
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    LISTENING = auto()
    ERROR = auto()


@dataclass
class TranscriptionMessage:
    """转写消息"""
    type: str
    text: str = ""
    session_id: str = ""
    language: str = ""
    confidence: float = 0.0
    timestamp: float = 0.0
    duration: float = 0.0


class WebSocketClient:
    """WebSocket 客户端"""

    def __init__(self, url: str = "ws://localhost:8765/api/v1/stt/stream"):
        self._url = url
        self._ws = None
        self._session_id: Optional[str] = None

        self._state = ConnectionState.DISCONNECTED
        self._receive_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        # 回调函数
        self._on_message: Optional[Callable[[TranscriptionMessage], None]] = None
        self._on_state_change: Optional[Callable[[ConnectionState], None]] = None

        # 转写结果缓存
        self._transcript_parts: list = []
        self._partial_text: str = ""

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def session_id(self) -> Optional[str]:
        return self._session_id

    @property
    def is_connected(self) -> bool:
        return self._state in (ConnectionState.CONNECTED, ConnectionState.LISTENING)

    @property
    def is_listening(self) -> bool:
        return self._state == ConnectionState.LISTENING

    @property
    def full_transcript(self) -> str:
        """获取完整转写文本"""
        return " ".join(self._transcript_parts)

    @property
    def partial_text(self) -> str:
        """获取部分转写文本"""
        return self._partial_text

    @property
    def display_text(self) -> str:
        """获取显示文本（完整 + 部分）"""
        text = self.full_transcript
        if self._partial_text:
            text = f"{text} {self._partial_text}" if text else self._partial_text
        return text.strip()

    def _set_state(self, state: ConnectionState) -> None:
        """设置状态"""
        self._state = state
        if self._on_state_change:
            self._on_state_change(state)

    async def connect(self) -> bool:
        """
        连接到服务器

        Returns:
            是否成功连接
        """
        if self.is_connected:
            return True

        try:
            import websockets

            self._set_state(ConnectionState.CONNECTING)
            self._loop = asyncio.get_event_loop()

            self._ws = await websockets.connect(
                self._url,
                ping_interval=20,
                ping_timeout=10
            )

            # 等待 ready 消息
            ready_msg = await self._ws.recv()
            data = json.loads(ready_msg)

            if data.get("type") != "ready":
                raise ConnectionError("未收到 ready 消息")

            self._session_id = data.get("session_id")
            self._set_state(ConnectionState.CONNECTED)

            # 启动接收循环
            self._receive_task = asyncio.create_task(self._receive_loop())

            return True

        except Exception as e:
            print(f"WebSocket 连接失败: {e}")
            self._set_state(ConnectionState.ERROR)
            return False

    async def disconnect(self) -> None:
        """断开连接"""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None

        self._set_state(ConnectionState.DISCONNECTED)
        self._session_id = None

    async def start_listening(self, config: Optional[dict] = None) -> bool:
        """
        开始监听

        Args:
            config: 配置参数 (language, model 等)

        Returns:
            是否成功开始
        """
        if not self.is_connected:
            return False

        try:
            # 发送 start 命令
            await self._ws.send(json.dumps({
                "type": "start",
                "payload": config or {}
            }))

            # 等待 listening 消息（在接收循环中处理）
            # 设置超时等待
            for _ in range(50):  # 最多等待5秒
                if self._state == ConnectionState.LISTENING:
                    return True
                await asyncio.sleep(0.1)

            return self._state == ConnectionState.LISTENING

        except Exception as e:
            print(f"开始监听失败: {e}")
            return False

    async def stop_listening(self) -> bool:
        """
        停止监听

        Returns:
            是否成功停止
        """
        if not self.is_listening:
            return True

        try:
            # 发送 stop 命令
            await self._ws.send(json.dumps({"type": "stop"}))

            # 等待 stopped 消息
            for _ in range(50):  # 最多等待5秒
                if self._state == ConnectionState.CONNECTED:
                    return True
                await asyncio.sleep(0.1)

            return True

        except Exception as e:
            print(f"停止监听失败: {e}")
            return False

    async def send_audio(self, audio_data: bytes) -> bool:
        """
        发送音频数据

        Args:
            audio_data: PCM 音频数据 (16-bit, 16kHz, mono)

        Returns:
            是否成功发送
        """
        if not self.is_listening or not self._ws:
            return False

        try:
            await self._ws.send(audio_data)
            return True
        except Exception as e:
            print(f"发送音频失败: {e}")
            return False

    async def _receive_loop(self) -> None:
        """接收消息循环"""
        try:
            async for message in self._ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    print(f"无效的 JSON 消息: {message[:100]}")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"接收循环错误: {e}")
            self._set_state(ConnectionState.ERROR)

    async def _handle_message(self, data: dict) -> None:
        """处理接收到的消息"""
        msg_type = data.get("type")

        if msg_type == "listening":
            self._set_state(ConnectionState.LISTENING)

        elif msg_type == "partial":
            self._partial_text = data.get("text", "")
            if self._on_message:
                self._on_message(TranscriptionMessage(
                    type="partial",
                    text=self._partial_text,
                    session_id=data.get("session_id", ""),
                ))

        elif msg_type == "final":
            text = data.get("text", "")
            if text:
                self._transcript_parts.append(text)
                self._partial_text = ""

            if self._on_message:
                self._on_message(TranscriptionMessage(
                    type="final",
                    text=text,
                    session_id=data.get("session_id", ""),
                    language=data.get("language", ""),
                    confidence=data.get("confidence", 0),
                    timestamp=data.get("timestamp", 0),
                    duration=data.get("duration", 0),
                ))

        elif msg_type == "stopped":
            self._set_state(ConnectionState.CONNECTED)

        elif msg_type == "error":
            print(f"服务器错误: {data.get('message', 'Unknown error')}")

    def clear_transcript(self) -> None:
        """清空转写结果"""
        self._transcript_parts.clear()
        self._partial_text = ""