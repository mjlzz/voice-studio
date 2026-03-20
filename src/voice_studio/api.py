"""
Voice Studio API 服务
"""
import uuid
import aiofiles
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .config import settings
from .stt import get_stt_engine
from .tts import get_tts_engine, CHINESE_VOICES, ENGLISH_VOICES
from .tts_local import get_local_tts_engine, LOCAL_CHINESE_VOICES, LOCAL_ENGLISH_VOICES, PIPER_MODELS
from .exceptions import (
    VoiceStudioError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    EmptyFileError,
    TextTooLongError,
    EmptyTextError,
    InvalidParameterError,
    TranscriptionError,
    SynthesisError,
)
from .logging_config import setup_logging, get_logger, bind_request_context, clear_request_context

# 初始化日志
setup_logging(json_format=not settings.debug, log_level="DEBUG" if settings.debug else "INFO")
logger = get_logger()


# ----------------------------------------------------------
# 速率限制
# ----------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ----------------------------------------------------------
# 创建 FastAPI 应用
# ----------------------------------------------------------

app = FastAPI(
    title="Voice Studio API",
    description="让声音创作触手可及",
    version="0.1.0",
)

# 速率限制状态
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


# ----------------------------------------------------------
# 中间件：请求追踪
# ----------------------------------------------------------

@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    """请求追踪中间件"""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    bind_request_context(request_id=request_id)

    # 记录请求开始
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client_ip=get_remote_address(request),
    )

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # 记录请求完成
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )
        return response
    finally:
        clear_request_context()


# ----------------------------------------------------------
# 统一错误处理
# ----------------------------------------------------------

class ErrorResponse(BaseModel):
    """标准错误响应"""
    code: str
    message: str
    detail: Optional[str] = None
    request_id: Optional[str] = None


@app.exception_handler(VoiceStudioError)
async def voice_studio_error_handler(request: Request, exc: VoiceStudioError):
    """处理自定义异常"""
    request_id = request.headers.get("X-Request-ID")
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            detail=exc.detail if settings.debug else None,
            request_id=request_id,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """处理未捕获的异常"""
    request_id = request.headers.get("X-Request-ID")
    logger.exception("unhandled_exception", error=str(exc))

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code="INTERNAL_ERROR",
            message="服务器内部错误",
            detail=str(exc) if settings.debug else None,
            request_id=request_id,
        ).model_dump(),
    )


# ----------------------------------------------------------
# 辅助函数
# ----------------------------------------------------------

def validate_upload_file(file: UploadFile) -> tuple[Path, bool]:
    """
    验证上传的文件

    Returns:
        (临时文件路径, 是否有效)

    Raises:
        EmptyFileError: 空文件
        UnsupportedFileTypeError: 不支持的文件类型
    """
    # 获取文件扩展名
    filename = file.filename or "upload"
    file_ext = Path(filename).suffix.lower()

    # 验证扩展名
    if file_ext not in settings.allowed_audio_extensions:
        raise UnsupportedFileTypeError(file_ext or "unknown", settings.allowed_audio_extensions)

    return file_ext, True


async def save_upload_file(file: UploadFile, file_ext: str) -> Path:
    """
    保存上传的文件到临时目录

    Returns:
        临时文件路径

    Raises:
        EmptyFileError: 空文件
        FileTooLargeError: 文件过大
    """
    temp_path = settings.output_dir / f"temp_{uuid.uuid4().hex}{file_ext}"

    async with aiofiles.open(temp_path, "wb") as f:
        content = await file.read()

        # 检查文件大小
        if len(content) == 0:
            raise EmptyFileError()

        if len(content) > settings.max_file_size:
            raise FileTooLargeError(len(content), settings.max_file_size)

        await f.write(content)

    return temp_path


# ----------------------------------------------------------
# 请求/响应模型
# ----------------------------------------------------------

class TTSRequest(BaseModel):
    """TTS 请求"""
    text: str
    voice: Optional[str] = None
    engine: Optional[str] = "cloud"
    rate: str = "+0%"
    volume: str = "+0%"

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('文本不能为空')
        if len(v) > settings.max_text_length:
            raise ValueError(f'文本长度不能超过 {settings.max_text_length} 字符')
        return v

    @field_validator('rate', 'volume')
    @classmethod
    def validate_rate_volume(cls, v):
        if not re.match(r'^[+-]\d+%$', v):
            raise ValueError('格式必须为 +/-N% (如 +50% 或 -20%)')
        return v


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
@limiter.limit("60/minute")
async def health_check(request: Request):
    """健康检查"""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        stt_engine=settings.stt_engine,
        tts_engine=settings.tts_engine
    )


@app.get("/api/v1/engines")
@limiter.limit("60/minute")
async def list_engines(request: Request):
    """获取可用引擎列表"""
    local_engine = get_local_tts_engine()
    local_voices = local_engine.get_available_voices()

    return {
        "stt": {
            "current": settings.stt_engine,
            "available": ["local"],
            "status": "available"
        },
        "tts": {
            "current": settings.tts_engine,
            "available": ["cloud", "local"],
            "status": "available",
            "local_models": local_voices
        }
    }


# ----------------------------------------------------------
# STT 接口
# ----------------------------------------------------------

@app.post("/api/v1/stt/transcribe")
@limiter.limit(settings.rate_limit_stt)
async def transcribe_audio(
    request: Request,
    file: UploadFile = File(...),
    language: Optional[str] = Query(None, description="语言代码，如 zh/en，留空自动检测"),
    word_timestamps: bool = Query(True, description="是否返回词级时间戳")
):
    """
    语音转文字

    支持的音频格式: wav, mp3, m4a, flac, ogg, webm
    """
    logger.info("stt_transcribe_started", filename=file.filename, language=language)

    # 验证文件
    file_ext, _ = validate_upload_file(file)
    temp_path = None

    try:
        # 保存文件
        temp_path = await save_upload_file(file, file_ext)

        # 转写
        engine = get_stt_engine()
        result = engine.transcribe(
            str(temp_path),
            language=language,
            word_timestamps=word_timestamps
        )

        logger.info("stt_transcribe_completed", duration=result.duration, rtf=result.rtf)
        return result

    except VoiceStudioError:
        raise
    except Exception as e:
        logger.error("stt_transcribe_failed", error=str(e))
        raise TranscriptionError(detail=str(e))

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


# ----------------------------------------------------------
# TTS 接口
# ----------------------------------------------------------

@app.get("/api/v1/tts/voices", response_model=VoicesResponse)
@limiter.limit("60/minute")
async def list_voices(
    request: Request,
    language: Optional[str] = Query(None, description="筛选语言，如 zh/en"),
    engine: str = Query("cloud", description="TTS引擎: cloud 或 local")
):
    """获取可用音色列表"""
    if engine == "local":
        local_engine = get_local_tts_engine()
        voices = local_engine.list_voices()
        return {"voices": voices}
    else:
        cloud_engine = get_tts_engine()
        voices = await cloud_engine.list_voices(language)
        return {"voices": [{"name": v.name, "short_name": v.short_name, "gender": v.gender, "locale": v.locale} for v in voices]}


@app.get("/api/v1/tts/presets")
@limiter.limit("60/minute")
async def list_voice_presets(request: Request):
    """获取预设音色列表"""
    return {
        "cloud": {
            "chinese": CHINESE_VOICES,
            "english": ENGLISH_VOICES
        },
        "local": {
            "chinese": LOCAL_CHINESE_VOICES,
            "english": LOCAL_ENGLISH_VOICES,
            "available_models": list(PIPER_MODELS.keys())
        }
    }


@app.post("/api/v1/tts/synthesize")
@limiter.limit(settings.rate_limit_tts)
async def synthesize_speech(
    request: Request,
    tts_request: TTSRequest,
    engine: str = Query("cloud", description="TTS引擎: cloud(edge-tts在线) 或 local(piper离线)")
):
    """
    文字转语音

    - text: 要合成的文本
    - voice: 音色名称
        - cloud: 如 zh-CN-XiaoxiaoNeural
        - local: 如 zh_CN-huayan
    - engine: 引擎选择 (cloud/local)
    - rate: 语速 (-50% to +100%, 仅cloud)
    - volume: 音量 (-50% to +100%, 仅cloud)
    """
    logger.info("tts_synthesize_started", text_length=len(tts_request.text), engine=engine, voice=tts_request.voice)

    # 根据引擎选择输出格式
    if engine == "local":
        output_path = settings.output_dir / f"tts_{uuid.uuid4().hex}.wav"
    else:
        output_path = settings.output_dir / f"tts_{uuid.uuid4().hex}.mp3"

    try:
        if engine == "local":
            local_engine = get_local_tts_engine()
            await local_engine.synthesize_async(
                text=tts_request.text,
                output_path=str(output_path),
                voice=tts_request.voice
            )
            media_type = "audio/wav"
            filename = "speech.wav"
        else:
            cloud_engine = get_tts_engine()
            await cloud_engine.synthesize(
                text=tts_request.text,
                output_path=str(output_path),
                voice=tts_request.voice,
                rate=tts_request.rate,
                volume=tts_request.volume
            )
            media_type = "audio/mpeg"
            filename = "speech.mp3"

        logger.info("tts_synthesize_completed", engine=engine)
        return FileResponse(
            path=output_path,
            media_type=media_type,
            filename=filename
        )

    except VoiceStudioError:
        raise
    except Exception as e:
        logger.error("tts_synthesize_failed", error=str(e))
        raise SynthesisError(detail=str(e))


# ----------------------------------------------------------
# 启动入口
# ----------------------------------------------------------

def run_server():
    """启动服务器"""
    import uvicorn
    logger.info("server_starting", host=settings.host, port=settings.port)
    uvicorn.run(
        "voice_studio.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )