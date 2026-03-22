# Voice Studio

中文 | [English](README_EN.md) | [日本語](README_JA.md)

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

- **Web UI**: 现代、简约的 Web 界面，开箱即用，支持中/英/日三语界面
- **STT (语音转文字)**: 基于 faster-whisper，支持中英文混合识别，带词级时间戳
  - 支持导出 TXT、SRT、JSON 格式
- **TTS (文字转语音)**:
  - **云端**: 基于 edge-tts，高质量多音色语音合成
  - **本地**: 基于 Piper TTS，离线可用，CPU 优化
  - **中英混合**: 基于 ONNX 模型，支持中英文无缝混合合成，自动处理长文本
- **悬浮话筒**: 桌面悬浮窗口，一键语音转文字，支持系统托盘，自动复制到剪贴板
  - **实时流式**: 边说边转，实时显示识别结果
  - **录音后转写**: 录音完成后一次性转写（默认模式）
  - 支持中/英/日三语界面
- **REST API**: FastAPI 后端服务，易于集成
- **CLI 工具**: 命令行快速调用，支持进程管理

## 系统要求

- **Python**: 3.10 或更高版本
- **Node.js**: 16.0 或更高版本（仅 Web UI 需要）
- **操作系统**: Windows / macOS / Linux
- **内存**: 建议 4GB 以上（STT 模型加载需要）
- **存储**: 约 2GB（模型首次使用时自动下载）

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

### 1. 启动后端

```bash
vs serve
# 访问 http://localhost:8765/docs 查看 API 文档
```

### 2. Web UI

```bash
# 启动前端开发服务器（需要先启动后端）
cd web && npm run dev
# 访问 http://localhost:2345
```

### 3. 悬浮话筒

```bash
# 启动悬浮话筒（需要先启动后端）
vs mic

# 两种转写模式：
# - 录音后转写（默认）：录音完成后一次性转写
# - 实时流式：边说边转，实时显示结果
# 右键托盘图标 → 转写模式 → 选择模式

# 支持中/英/日三语界面：
# 右键托盘图标 → 语言 → 选择语言
```

### 4. CLI 命令

```bash
# 语音转文字
vs stt -i recording.mp3 -o result.json

# 文字转语音
vs tts -t "你好世界" -o output.mp3              # 云端（默认）
vs tts -t "你好世界" -o output.wav --engine local  # 本地离线
vs tts -t "Hello 世界" -o output.wav --engine mixed  # 中英混合

# 查看可用音色
vs voices
vs voices --local  # 查看本地模型状态

# 服务管理
vs dev        # 启动开发服务器（前后端一起）
vs dev --open # 启动并打开浏览器
vs status     # 查看服务状态
vs stop       # 停止服务
vs restart    # 重启服务
vs logs -f    # 实时查看日志
```

### API 调用

访问 http://localhost:8765/docs 查看完整 API 文档

```bash
# 语音转文字
curl -X POST "http://localhost:8765/api/v1/stt/transcribe" \
  -F "file=@test.mp3"

# 文字转语音
curl -X POST "http://localhost:8765/api/v1/tts/synthesize?engine=cloud" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "voice": "zh-CN-XiaoxiaoNeural"}' \
  --output speech.mp3
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

## 隐私说明

- **本地模式**：STT 和本地 TTS 引擎完全在本地运行，不会将任何数据发送到外部服务器
- **云端 TTS**：使用云端（edge-tts）引擎时，输入文本会发送到 Microsoft 服务器进行语音合成
- **数据存储**：所有生成的音频文件保存在本地 `~/.voicestudio/output/` 目录
- **无遥测**：本项目不收集任何使用数据或用户信息

## 更多文档

- [技术架构与项目结构](docs/ARCHITECTURE.md) - 技术栈、架构设计、扩展开发指南

## 许可证

MIT