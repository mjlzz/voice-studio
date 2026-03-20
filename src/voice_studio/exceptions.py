"""
Voice Studio 自定义异常类
"""
from typing import Optional, List


class VoiceStudioError(Exception):
    """Voice Studio 基础异常"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class FileTooLargeError(VoiceStudioError):
    """文件大小超出限制"""

    def __init__(self, actual_size: int, max_size: int):
        max_mb = max_size // (1024 * 1024)
        actual_mb = actual_size / (1024 * 1024)
        super().__init__(
            code="FILE_TOO_LARGE",
            message=f"文件大小超出限制 (最大 {max_mb}MB)",
            status_code=413,
            detail=f"文件大小: {actual_mb:.2f}MB, 最大限制: {max_mb}MB"
        )


class UnsupportedFileTypeError(VoiceStudioError):
    """不支持的文件类型"""

    def __init__(self, file_type: str, allowed: List[str]):
        super().__init__(
            code="UNSUPPORTED_FILE_TYPE",
            message=f"不支持的文件类型，允许: {', '.join(allowed)}",
            status_code=400,
            detail=f"文件类型: {file_type}"
        )


class EmptyFileError(VoiceStudioError):
    """空文件"""

    def __init__(self):
        super().__init__(
            code="EMPTY_FILE",
            message="上传的文件为空",
            status_code=400
        )


class TextTooLongError(VoiceStudioError):
    """文本过长"""

    def __init__(self, actual_length: int, max_length: int):
        super().__init__(
            code="TEXT_TOO_LONG",
            message=f"文本长度超出限制 (最大 {max_length} 字符)",
            status_code=400,
            detail=f"文本长度: {actual_length}, 最大限制: {max_length}"
        )


class EmptyTextError(VoiceStudioError):
    """空文本"""

    def __init__(self):
        super().__init__(
            code="EMPTY_TEXT",
            message="文本不能为空",
            status_code=400
        )


class InvalidParameterError(VoiceStudioError):
    """无效参数"""

    def __init__(self, param_name: str, message: str, detail: Optional[str] = None):
        super().__init__(
            code="INVALID_PARAMETER",
            message=f"参数 '{param_name}' 无效: {message}",
            status_code=422,
            detail=detail
        )


class EngineNotAvailableError(VoiceStudioError):
    """引擎不可用"""

    def __init__(self, engine_name: str):
        super().__init__(
            code="ENGINE_NOT_AVAILABLE",
            message=f"引擎 '{engine_name}' 不可用",
            status_code=503
        )


class TranscriptionError(VoiceStudioError):
    """转写失败"""

    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            code="TRANSCRIPTION_FAILED",
            message="语音转文字失败",
            status_code=500,
            detail=detail
        )


class SynthesisError(VoiceStudioError):
    """合成失败"""

    def __init__(self, detail: Optional[str] = None):
        super().__init__(
            code="SYNTHESIS_FAILED",
            message="文字转语音失败",
            status_code=500,
            detail=detail
        )