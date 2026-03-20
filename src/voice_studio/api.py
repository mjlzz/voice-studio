"""
Voice Studio API 服务
"""
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import settings
from .stt import get_stt_engine
from .tts import get_tts_engine, CHINESE_VOICES, ENGLISH_VOICES


# 创建 FastAPI 应用
app = FastAPI(
    title="Voice Studio API",
    description="让声音创作触手可及",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------
# 请求/响应模型
# ----------------------------------------------------------

class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str
    voice: Optional[str] = None
    rate: str = "+0%"
    volume: str = "+0%"


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    stt_engine: str
    tts_engine: str


class VoicesResponse(BaseModel):
    """音色列表响应"""
    voices: list


# ----------------------------------------------------------
# API 路由
# ----------------------------------------------------------

@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        stt_engine=settings.stt_engine,
        tts_engine=settings.tts_engine
    )


@app.get("/api/v1/engines")
async def list_engines():
    """获取可用引擎列表"""
    return {
        "stt": {
            "current": settings.stt_engine,
            "available": ["local"],
            "status": "available"
        },
        "tts": {
            "current": settings.tts_engine,
            "available": ["local", "cloud"],
            "status": "available"
        }
    }


# ----------------------------------------------------------
# STT 接口
# ----------------------------------------------------------

@app.post("/api/v1/stt/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="语言代码，如 zh/en，留空自动检测"),
    word_timestamps: bool = Query(True, description="是否返回词级时间戳")
):
    """
    语音转文字

    支持的音频格式: wav, mp3, m4a, flac, ogg 等
    """
    # 保存上传的文件
    file_ext = Path(file.filename).suffix or ".wav"
    temp_path = settings.output_dir / f"temp_{uuid.uuid4().hex}{file_ext}"

    try:
        # 写入临时文件
        async with aiofiles.open(temp_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        # 转写
        engine = get_stt_engine()
        result = engine.transcribe(
            str(temp_path),
            language=language,
            word_timestamps=word_timestamps
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转写失败: {str(e)}")

    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()


# ----------------------------------------------------------
# TTS 接口
# ----------------------------------------------------------

@app.get("/api/v1/tts/voices", response_model=VoicesResponse)
async def list_voices(language: Optional[str] = Query(None, description="筛选语言，如 zh/en")):
    """获取可用音色列表"""
    engine = get_tts_engine()
    voices = await engine.list_voices(language)
    return {"voices": [{"name": v.name, "short_name": v.short_name, "gender": v.gender, "locale": v.locale} for v in voices]}


@app.get("/api/v1/tts/presets")
async def list_voice_presets():
    """获取预设音色列表"""
    return {
        "chinese": CHINESE_VOICES,
        "english": ENGLISH_VOICES
    }


@app.post("/api/v1/tts/synthesize")
async def synthesize_speech(request: TTSRequest):
    """
    文字转语音

    - text: 要合成的文本
    - voice: 音色名称 (如 zh-CN-XiaoxiaoNeural)
    - rate: 语速 (-50% to +100%)
    - volume: 音量 (-50% to +100%)
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    output_path = settings.output_dir / f"tts_{uuid.uuid4().hex}.mp3"

    try:
        engine = get_tts_engine()
        await engine.synthesize(
            text=request.text,
            output_path=str(output_path),
            voice=request.voice,
            rate=request.rate,
            volume=request.volume
        )

        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename=f"speech.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


# ----------------------------------------------------------
# 启动入口
# ----------------------------------------------------------

def run_server():
    """启动服务器"""
    import uvicorn
    uvicorn.run(
        "voice_studio.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )