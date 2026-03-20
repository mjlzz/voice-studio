# Voice Studio

让声音创作触手可及 - 轻量、灵活、可扩展的声音处理工作台

## 功能

- **Web UI**: 现代、简约的 Web 界面，开箱即用
- **STT (语音转文字)**: 基于 faster-whisper，支持中英文混合识别，带词级时间戳
  - 支持导出 TXT、SRT、JSON 格式
- **TTS (文字转语音)**:
  - **云端**: 基于 edge-tts，高质量多音色语音合成
  - **本地**: 基于 Piper TTS，离线可用，CPU 优化
- **REST API**: FastAPI 后端服务，易于集成
- **CLI 工具**: 命令行快速调用

## 安装

```bash
# 安装 Python 依赖
pip install -e .

# 安装 Web UI 依赖
cd web && npm install
```

## 快速开始

### Web UI

```bash
# 启动后端服务
vs serve

# 启动前端开发服务器 (另一个终端)
cd web && npm run dev

# 访问 http://localhost:5173
```

### CLI 使用

```bash
# 语音转文字
vs stt -i recording.mp3 -o result.json

# 文字转语音 - 云端 (默认，需要联网)
vs tts -t "你好，这是一个测试" -o output.mp3

# 文字转语音 - 本地 (离线可用，首次会自动下载模型)
vs tts -t "你好，这是一个测试" -o output.wav --engine local

# 查看可用音色
vs voices

# 查看本地模型状态
vs voices --local

# 启动 API 服务
vs serve
```

### API 使用

启动服务后访问 http://localhost:8000/docs 查看交互式 API 文档

#### STT 接口

```bash
# 上传音频文件转写
curl -X POST "http://localhost:8000/api/v1/stt/transcribe" \
  -F "file=@test.mp3"
```

#### TTS 接口

```bash
# 云端 TTS (默认)
curl -X POST "http://localhost:8000/api/v1/tts/synthesize?engine=cloud" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "voice": "zh-CN-XiaoxiaoNeural"}' \
  --output speech.mp3

# 本地 TTS (离线)
curl -X POST "http://localhost:8000/api/v1/tts/synthesize?engine=local" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "voice": "zh_CN-huayan"}' \
  --output speech.wav

# 获取可用音色
curl "http://localhost:8000/api/v1/tts/voices?engine=cloud&language=zh"
curl "http://localhost:8000/api/v1/tts/voices?engine=local"
```

## Web UI 功能

### 语音转文字 (STT)
- 拖拽或点击上传音频文件
- 支持多种音频格式 (MP3、WAV、M4A、OGG、FLAC)
- 实时显示转写进度
- 词级时间戳展示
- 导出格式：TXT、SRT、JSON

### 文字转语音 (TTS)
- 云端/本地模式切换
- 音色选择（按语言筛选）
- 语速、音调调节
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

> 首次使用本地引擎时，模型会自动下载到 `~/.voicestudio/models/piper/`

## 配置

环境变量配置 (前缀 `VS_`):

```bash
# 服务配置
VS_HOST=127.0.0.1
VS_PORT=8000
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
├── api.py         # FastAPI 服务
└── cli.py         # CLI 工具

web/
├── src/
│   ├── components/    # Vue 组件
│   │   ├── common/    # 通用组件
│   │   ├── stt/       # STT 相关组件
│   │   └── tts/       # TTS 相关组件
│   ├── views/         # 页面视图
│   ├── api/           # API 调用
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

### 前端
- Vue 3 + TypeScript
- Vite - 构建工具
- Tailwind CSS - 样式
- Lucide Vue Next - 图标

## 许可证

MIT