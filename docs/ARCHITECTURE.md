# 技术架构

## 技术栈

### 后端
- Python 3.10+
- FastAPI - Web 框架
- faster-whisper - 语音识别
- edge-tts - 云端 TTS
- Piper TTS - 本地 TTS
- ONNX Runtime - 中英混合 TTS

### 前端
- Vue 3 + TypeScript
- Vite - 构建工具
- Tailwind CSS - 样式
- Lucide Vue Next - 图标
- vue-i18n - 国际化（支持中/英/日）

## 项目结构

```
src/voice_studio/
├── __init__.py    # 包入口
├── config.py      # 配置管理
├── stt.py         # STT 引擎 (faster-whisper)
├── tts.py         # TTS 引擎 - 云端 (edge-tts)
├── tts_local.py   # TTS 引擎 - 本地 (Piper TTS)
├── tts_mixed.py   # TTS 引擎 - 中英混合 (ONNX)
├── api.py         # FastAPI 服务
├── cli.py         # CLI 工具
├── process_manager.py  # 进程管理
├── streaming/          # 实时语音处理
│   ├── engine.py       # 流式 STT 引擎
│   ├── session.py      # 会话管理
│   ├── buffer.py       # 音频缓冲
│   └── vad.py          # 语音活动检测
├── floating_mic/       # 悬浮话筒应用
│   ├── main.py         # 入口
│   ├── config.py       # 配置
│   ├── floating_window.py  # 悬浮窗口
│   ├── state_manager.py    # 状态管理
│   ├── system_tray.py      # 系统托盘
│   ├── audio_capture.py    # 音频采集
│   ├── websocket_client.py # WebSocket 客户端
│   ├── batch_transcriber.py # 录音后转写处理器
│   └── clipboard.py        # 剪贴板操作

web/
├── src/
│   ├── components/    # Vue 组件
│   │   ├── common/    # 通用组件
│   │   ├── stt/       # STT 相关组件
│   │   └── tts/       # TTS 相关组件
│   ├── views/         # 页面视图
│   ├── api/           # API 调用
│   ├── locales/       # 国际化翻译文件
│   └── utils/         # 工具函数
└── package.json
```

## 架构设计

### 双引擎策略

TTS 支持三种引擎模式：
- **云端 (edge-tts)**: 高质量多音色，需要联网
- **本地 (Piper)**: CPU 优化，完全离线
- **中英混合 (ONNX)**: 支持中英文无缝混合，离线可用

### 双转写模式

悬浮话筒支持两种转写模式：
- **Batch (录音后转写)**: 录音完成后一次性转写，准确率更高
- **Streaming (实时流式)**: 边说边转，实时反馈

### 实时流式架构

```
客户端音频 → WebSocket → VAD检测 → 音频缓冲 → Whisper推理 → 实时返回结果
```

核心组件：
- `streaming/engine.py` - 流式引擎核心
- `streaming/vad.py` - Voice Activity Detection
- `streaming/buffer.py` - 音频帧缓冲管理
- `streaming/session.py` - 会话生命周期管理

## 扩展开发

### 添加新的 TTS 引擎

1. 在 `src/voice_studio/` 下创建新引擎文件（如 `tts_xxx.py`）
2. 实现 `synthesize(text: str, voice: str, ...)` 接口
3. 在 `api.py` 中注册新路由
4. 在 `cli.py` 中添加命令支持

### 添加新的语言支持

前端国际化文件位于 `web/src/locales/`，添加新的 JSON 文件即可。

## 配置

环境变量配置 (前缀 `VS_`):

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `VS_HOST` | 服务主机 | `127.0.0.1` |
| `VS_PORT` | 服务端口 | `8765` |
| `VS_DEBUG` | 调试模式 | `True` |
| `VS_WHISPER_MODEL` | Whisper 模型大小 | `base` |
| `VS_WHISPER_DEVICE` | Whisper 推理设备 | `cpu` |
| `VS_DEFAULT_VOICE` | 默认 TTS 音色 | `zh-CN-XiaoxiaoNeural` |