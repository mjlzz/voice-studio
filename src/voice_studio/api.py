"""
Voice Studio API 服务
"""
import uuid
import aiofiles
import re
import time
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
from .tts_mixed import get_mixed_tts_engine
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


def cleanup_temp_files():
    """清理旧的临时文件"""
    output_dir = settings.output_dir
    if not output_dir.exists():
        return

    # 清理 temp_* 和 audio_* 开头的临时文件
    patterns = ["temp_*", "audio_*"]
    cleaned_count = 0

    for pattern in patterns:
        for file_path in output_dir.glob(pattern):
            try:
                # 只清理超过1小时的临时文件（避免清理正在使用的文件）
                if time.time() - file_path.stat().st_mtime > 3600:
                    file_path.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning("cleanup_failed", file=str(file_path), error=str(e))

    if cleaned_count > 0:
        logger.info("temp_files_cleaned", count=cleaned_count)


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

# 启动时清理临时文件
@app.on_event("startup")
async def startup_event():
    """服务启动时的初始化"""
    cleanup_temp_files()
    logger.info("server_started", output_dir=str(settings.output_dir))

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

def validate_upload_file(file: UploadFile) -> tuple[str, str]:
    """
    验证上传的文件

    Returns:
        (文件扩展名, 文件类型: 'audio' 或 'video')

    Raises:
        EmptyFileError: 空文件
        UnsupportedFileTypeError: 不支持的文件类型
    """
    # 获取文件扩展名
    filename = file.filename or "upload"
    file_ext = Path(filename).suffix.lower()

    # 检查是否为音频文件
    if file_ext in settings.allowed_audio_extensions:
        return file_ext, "audio"

    # 检查是否为视频文件
    if settings.enable_video_stt and file_ext in settings.allowed_video_extensions:
        return file_ext, "video"

    # 不支持的文件类型
    allowed = settings.allowed_audio_extensions + (
        settings.allowed_video_extensions if settings.enable_video_stt else []
    )
    raise UnsupportedFileTypeError(file_ext or "unknown", allowed)


async def save_upload_file(file: UploadFile, file_ext: str, file_type: str = "audio") -> Path:
    """
    保存上传的文件到临时目录

    Args:
        file: 上传的文件
        file_ext: 文件扩展名
        file_type: 文件类型 ('audio' 或 'video')

    Returns:
        临时文件路径

    Raises:
        EmptyFileError: 空文件
        FileTooLargeError: 文件过大
    """
    temp_path = settings.output_dir / f"temp_{uuid.uuid4().hex}{file_ext}"

    # 确定文件大小限制
    max_size = settings.max_video_file_size if file_type == "video" else settings.max_file_size

    async with aiofiles.open(temp_path, "wb") as f:
        content = await file.read()

        # 检查文件大小
        if len(content) == 0:
            raise EmptyFileError()

        if len(content) > max_size:
            raise FileTooLargeError(len(content), max_size)

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


class MixedTTSRequest(BaseModel):
    """中英混合 TTS 请求"""
    text: str
    length_scale: float = 1.0  # 语速，越大越慢
    noise_scale: float = 1.0   # 随机性

    @field_validator('text')
    @classmethod
    def validate_text(cls, v):
        if not v or not v.strip():
            raise ValueError('文本不能为空')
        if len(v) > settings.max_text_length:
            raise ValueError(f'文本长度不能超过 {settings.max_text_length} 字符')
        return v

    @field_validator('length_scale')
    @classmethod
    def validate_length_scale(cls, v):
        if not 0.1 <= v <= 3.0:
            raise ValueError('length_scale 必须在 0.1 到 3.0 之间')
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
    支持的视频格式: mp4, mkv, avi, mov, webm, flv, wmv, m4v
    """
    logger.info("stt_transcribe_started", filename=file.filename, language=language)

    # 验证文件
    file_ext, file_type = validate_upload_file(file)
    temp_path = None
    audio_path = None

    try:
        # 保存文件
        temp_path = await save_upload_file(file, file_ext, file_type)

        # 如果是视频文件，提取音频
        if file_type == "video":
            from .audio_extractor import get_audio_extractor, AudioExtractionError, FFmpegNotAvailableError

            extractor = get_audio_extractor()
            if not extractor.check_available():
                raise FFmpegNotAvailableError()

            audio_path = settings.output_dir / f"audio_{uuid.uuid4().hex}.wav"
            try:
                extractor.extract_audio(temp_path, audio_path)
            except AudioExtractionError as e:
                raise AudioExtractionError(str(e))
        else:
            audio_path = temp_path

        # 转写
        engine = get_stt_engine()
        result = engine.transcribe(
            str(audio_path),
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
        # 清理临时文件
        if temp_path and temp_path.exists():
            temp_path.unlink()
        if audio_path and audio_path != temp_path and audio_path.exists():
            audio_path.unlink()


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


@app.post("/api/v1/tts/synthesize-mixed")
@limiter.limit(settings.rate_limit_tts)
async def synthesize_mixed_speech(
    request: Request,
    tts_request: MixedTTSRequest,
):
    """
    中英混合文字转语音

    基于ONNX模型，支持中英文无缝混合合成
    - text: 要合成的文本（支持中英混合，如 "欢迎使用 voice studio"）
    - length_scale: 语速控制 (0.1-3.0, 默认1.0, 越大越慢)
    - noise_scale: 随机性控制 (默认1.0)
    """
    if not settings.mixed_tts_enabled:
        raise InvalidParameterError("中英混合TTS功能未启用")

    logger.info("tts_mixed_synthesize_started", text_length=len(tts_request.text))

    output_path = settings.output_dir / f"tts_mixed_{uuid.uuid4().hex}.wav"

    try:
        engine = get_mixed_tts_engine()
        await engine.synthesize_async(
            text=tts_request.text,
            output_path=str(output_path),
            noise_scale=tts_request.noise_scale,
            length_scale=tts_request.length_scale,
        )

        logger.info("tts_mixed_synthesize_completed")
        return FileResponse(
            path=output_path,
            media_type="audio/wav",
            filename="speech_mixed.wav"
        )

    except VoiceStudioError:
        raise
    except Exception as e:
        logger.error("tts_mixed_synthesize_failed", error=str(e))
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