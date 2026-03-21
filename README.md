# Voice Studio

让声音创作触手可及 - 轻量、灵活、可扩展的声音处理工作台

## 预览

<p align="center">
  <img src="docs/screenshots/web-stt.png" width="90%" alt="STT Web界面">
</p>
<p align="center">
  <img src="docs/screenshots/web-tts.png" width="90%" alt="TTS Web界面">
</p>

<p align="center">
  <img src="docs/screenshots/floating-mic.png" width="20%" alt="悬浮话筒">
  <img src="docs/screenshots/system-tray.png" width="30%" alt="系统托盘菜单">
</p>

## 功能

- **Web UI**: 现代、简约的 Web 界面，开箱即用
- **STT (语音转文字)**: 基于 faster-whisper，支持中英文混合识别，带词级时间戳
  - 支持导出 TXT、SRT、JSON 格式
- **TTS (文字转语音)**:
  - **云端**: 基于 edge-tts，高质量多音色语音合成
  - **本地**: 基于 Piper TTS，离线可用，CPU 优化
  - **中英混合**: 基于 ONNX 模型，支持中英文无缝混合合成，自动处理长文本
- **悬浮话筒**: 桌面悬浮窗口，一键语音转文字，支持系统托盘，自动复制到剪贴板
  - **实时流式**: 边说边转，实时显示识别结果
  - **录音后转写**: 录音完成后一次性转写（默认模式）
- **REST API**: FastAPI 后端服务，易于集成
- **CLI 工具**: 命令行快速调用，支持进程管理

## 安装

```bash
# 安装 Python 依赖
pip install -e .

# 安装 Web UI 依赖
cd web && npm install
```

> **提示**: 安装后可使用 `vs` 命令。如果提示命令未找到，可使用 `python -m voice_studio.cli` 替代，例如：
> ```bash
> python -m voice_studio.cli serve
> ```
> 或确保 Python Scripts 目录在 PATH 环境变量中。

## 快速开始

### Web UI

```bash
# 启动后端服务
vs serve

# 启动前端开发服务器 (另一个终端)
cd web && npm run dev

# 访问 http://localhost:2345
```

### CLI 使用

```bash
# ========== 语音转文字 ==========

# 文件转写
vs stt -i recording.mp3 -o result.json

# ========== 文字转语音 ==========

# 云端 TTS (默认，需要联网)
vs tts -t "你好，这是一个测试" -o output.mp3

# 本地 TTS (离线可用，首次会自动下载模型)
vs tts -t "你好，这是一个测试" -o output.wav --engine local

# 中英混合 TTS (支持中英文无缝混合，离线可用)
vs tts -t "欢迎使用 voice studio，这是一个很棒的工具" -o output.wav --engine mixed

# 查看可用音色
vs voices

# 查看本地模型状态
vs voices --local

# ========== 服务管理 ==========

# 启动开发服务器（前后端一起）
vs dev

# 启动开发服务器并自动打开浏览器
vs dev --open

# 仅启动后端/前端
vs dev --backend-only
vs dev --frontend-only

# 查看服务状态
vs status

# 停止服务
vs stop

# 重启服务
vs restart

# 查看日志
vs logs              # 查看最近 50 行日志
vs logs --backend    # 仅后端日志
vs logs -f           # 实时跟踪日志

# 启动 API 服务（仅后端）
vs serve

# ========== 悬浮话筒 ==========

# 启动悬浮话筒（需要先启动后端服务）
vs mic

# 悬浮话筒支持两种转写模式：
# - 录音后转写（默认）：录音完成后一次性转写
# - 实时流式：边说边转，实时显示结果
# 右键托盘图标 → 转写模式 → 选择模式
```

### API 使用

启动服务后访问 http://localhost:8765/docs 查看交互式 API 文档

#### STT 接口

```bash
# 上传音频文件转写
curl -X POST "http://localhost:8765/api/v1/stt/transcribe" \
  -F "file=@test.mp3"
```

#### TTS 接口

```bash
# 云端 TTS (默认)
curl -X POST "http://localhost:8765/api/v1/tts/synthesize?engine=cloud" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "voice": "zh-CN-XiaoxiaoNeural"}' \
  --output speech.mp3

# 本地 TTS (离线)
curl -X POST "http://localhost:8765/api/v1/tts/synthesize?engine=local" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "voice": "zh_CN-huayan"}' \
  --output speech.wav

# 中英混合 TTS (支持中英文无缝混合，自动分块处理)
curl -X POST "http://localhost:8765/api/v1/tts/synthesize-mixed" \
  -H "Content-Type: application/json" \
  -d '{"text": "欢迎使用 voice studio，这是一个很棒的工具", "length_scale": 1.0}' \
  --output speech_mixed.wav

# 获取可用音色
curl "http://localhost:8765/api/v1/tts/voices?engine=cloud&language=zh"
curl "http://localhost:8765/api/v1/tts/voices?engine=local"
```

## Web UI 功能

### 多语言支持
Web UI 支持中文、英文、日文三种界面语言：
- 自动检测浏览器语言
- 在设置页面切换语言
- 语言偏好自动保存

### 语音转文字 (STT)
- 拖拽或点击上传音频文件
- 支持多种音频格式 (MP3、WAV、M4A、OGG、FLAC)
- 实时显示转写进度
- 词级时间戳展示
- 导出格式：TXT、SRT、JSON

### 文字转语音 (TTS)
- 三种引擎模式：云端 / 本地 / 中英混合
- **云端模式**: 多音色选择，语速音量调节
- **本地模式**: Piper TTS 离线合成
- **中英混合模式**:
  - 支持中英文无缝混合输入
  - 自动下载模型（首次使用）
  - 智能分块处理长文本
  - 语速调节（0.5x ~ 2.0x）
- 试听与下载

## 预设音色

### 云端音色 (edge-tts)

#### 中文音色

| 名称 | 音色 ID | 特点 |
|------|---------|------|
| xiaoxiao | zh-CN-XiaoxiaoNeural | 晓晓 - 女声，自然 |
| yunxi | zh-CN-YunxiNeural | 云希 - 男声，年轻 |
| yunjian | zh-CN-YunjianNeural | 云健 - 男声，新闻播报 |
| xiaoyi | zh-CN-XiaoyiNeural | 晓伊 - 女声，温柔 |

#### 英文音色

| 名称 | 音色 ID | 特点 |
|------|---------|------|
| jenny | en-US-JennyNeural | Jenny - 女声，自然 |
| guy | en-US-GuyNeural | Guy - 男声，自然 |
| aria | en-US-AriaNeural | Aria - 女声，情感丰富 |

### 本地音色 (Piper TTS)

| 名称 | 音色 ID | 语言 | 说明 |
|------|---------|------|------|
| huayan | zh_CN-huayan | 中文 | 华燕 - 女声 |
| lessac | en_US-lessac | 英文 | Lessac - 女声，自然 |
| amy | en_US-amy | 英文 | Amy - 女声 |

### 中英混合 TTS

基于 ONNX 模型的中英混合语音合成，特点：

| 特性 | 说明 |
|-----|------|
| 中英混合 | 同一段文本无缝切换，如 "欢迎使用 voice studio" |
| 完全离线 | 模型下载后无需联网 |
| 统一音色 | 中英文使用同一音色，更自然 |
| 长文本支持 | 自动分块处理，并发合成 |
| 语速控制 | 0.5x ~ 2.0x 可调 |

> 首次使用时，模型会自动从 ModelScope 下载到 `~/.voicestudio/models/mixed_tts/`（约 125MB）

> 首次使用本地引擎时，模型会自动下载到 `~/.voicestudio/models/piper/`

## 配置

环境变量配置 (前缀 `VS_`):

```bash
# 服务配置
VS_HOST=127.0.0.1
VS_PORT=8765
VS_DEBUG=true

# STT 配置
VS_WHISPER_MODEL=base  # tiny/base/small/medium
VS_WHISPER_DEVICE=cpu

# TTS 配置
VS_DEFAULT_VOICE=zh-CN-XiaoxiaoNeural
```

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

## 许可证

MIT