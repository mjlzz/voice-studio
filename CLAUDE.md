# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice Studio is a hybrid Python (FastAPI backend) + Vue 3 (TypeScript frontend) voice processing application. It provides STT (Speech-to-Text) and TTS (Text-to-Speech) capabilities through a web UI, CLI, and REST API.

**Core Features:**
- Real-time streaming STT with Voice Activity Detection
- Multi-engine TTS: cloud (edge-tts), local (Piper), and mixed Chinese-English (ONNX)
- Desktop floating microphone widget (PyQt6) with two transcription modes:
  - **Batch mode** (default): Record first, transcribe after completion
  - **Streaming mode**: Real-time transcription while speaking
- Multi-language Web UI: Supports Chinese (zh-CN), English (en-US), and Japanese (ja-JP)

## Common Commands

### Python Backend

```bash
pip install -e .              # Install package
pip install -e ".[dev]"       # Install with dev dependencies
pytest                        # Run tests
pytest --cov                  # Run tests with coverage
pytest tests/test_api.py      # Run specific test file
ruff check .                  # Lint
ruff check . --fix            # Lint with auto-fix
mypy .                        # Type check
```

### CLI Commands (via `vs` command)

```bash
vs serve                      # Start API server (backend only)
vs dev                        # Start dev server (frontend + backend)
vs dev --backend-only         # Start only backend
vs dev --frontend-only        # Start only frontend
vs status                     # Check service status
vs stop                       # Stop all services
vs restart                    # Restart services
vs logs -f --backend          # Follow backend logs
vs stt -i audio.wav           # Speech-to-text transcription
vs tts -t "text"              # Text-to-speech synthesis
vs voices                     # List available TTS voices
vs mic                        # Launch floating microphone widget
```

### Frontend (web/)

```bash
npm install                   # Install dependencies
npm run dev                   # Start Vite dev server (port 2345)
npm run build                 # Build for production
```

## Architecture

### Entry Points

| Entry Point | Location | Description |
|-------------|----------|-------------|
| CLI | `src/voice_studio/cli.py` | Exposed as `vs` command |
| API Server | `src/voice_studio/api.py` | FastAPI app with WebSocket support |
| Frontend | `web/src/main.ts` | Vue 3 app entry |
| Floating Mic | `src/voice_studio/floating_mic/main.py` | PyQt6 desktop widget |

### Key Directories

- `src/voice_studio/` - Python backend (STT, TTS, API, CLI)
- `src/voice_studio/streaming/` - Real-time STT engine with VAD
- `src/voice_studio/floating_mic/` - Desktop floating microphone app
  - `state_manager.py` - Coordinates recording modes (batch/streaming)
  - `batch_transcriber.py` - Records audio and transcribes via HTTP API
  - `websocket_client.py` - Streaming mode WebSocket client
- `web/src/` - Vue 3 frontend (views, components, stores, api)
- `web/src/locales/` - i18n translation files (zh-CN, en-US, ja-JP)
- `tests/` - Python tests (pytest)

### Architecture Patterns

- **Dual Engine Strategy:** Cloud (edge-tts) + Local (Piper) TTS engines
- **Dual STT Mode:** Batch (HTTP) + Streaming (WebSocket) for floating mic
- **Real-time Streaming:** WebSocket-based STT with Voice Activity Detection
- **Process Management:** Built-in daemon management for dev server (PID files in `~/.voicestudio/`)
- **Configuration:** pydantic-settings with `VS_` environment variable prefix
- **Internationalization:** vue-i18n with locale persistence in localStorage

## Environment Variables

All configuration uses `VS_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `VS_HOST` | Server host | `127.0.0.1` |
| `VS_PORT` | Server port | `8765` |
| `VS_DEBUG` | Debug mode | `True` |
| `VS_WHISPER_MODEL` | Whisper model size | `base` |
| `VS_WHISPER_DEVICE` | Device for Whisper | `cpu` |
| `VS_TTS_ENGINE` | TTS engine | `local` |
| `VS_DEFAULT_VOICE` | Default TTS voice | `zh-CN-XiaoxiaoNeural` |

## Ports

- Frontend: `http://localhost:2345`
- Backend: `http://localhost:8765`
- API Docs: `http://localhost:8765/docs`

## Data Storage

- `~/.voicestudio/` - Config, models, output, database
- `~/.voicestudio/models/` - Whisper, Piper models (downloaded on first use)
- `~/.voicestudio/floating_mic.json` - Floating mic config (mode, position, language)
- Browser localStorage - UI language preference (`voice-studio-ui-language`)

## Floating Mic Transcription Modes

The floating mic supports two transcription modes, configured in `floating_mic.json`:

| Mode | Config Value | API Used | Use Case |
|------|-------------|----------|----------|
| Batch (default) | `batch` | HTTP POST `/api/v1/stt/transcribe` | Higher accuracy, no real-time feedback needed |
| Streaming | `streaming` | WebSocket `/api/v1/stt/stream` | Real-time feedback, live captioning |

Users can switch modes via system tray menu: Right-click → 转写模式 → Select mode