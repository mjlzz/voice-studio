"""
异常模块测试
"""
import pytest

from voice_studio.exceptions import (
    VoiceStudioError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    EmptyFileError,
    TextTooLongError,
    EmptyTextError,
    InvalidParameterError,
    EngineNotAvailableError,
    TranscriptionError,
    SynthesisError,
)


class TestVoiceStudioError:
    """基础异常测试"""

    def test_basic_error(self):
        """测试基本异常"""
        error = VoiceStudioError(
            code="TEST_ERROR",
            message="测试错误",
            status_code=400
        )

        assert error.code == "TEST_ERROR"
        assert error.message == "测试错误"
        assert error.status_code == 400
        assert error.detail is None

    def test_error_with_detail(self):
        """测试带详情的异常"""
        error = VoiceStudioError(
            code="DETAILED_ERROR",
            message="详细错误",
            status_code=500,
            detail="这是详细信息"
        )

        assert error.detail == "这是详细信息"

    def test_error_is_exception(self):
        """测试继承自 Exception"""
        error = VoiceStudioError(
            code="TEST",
            message="test",
            status_code=400
        )

        assert isinstance(error, Exception)

    def test_error_message_is_str(self):
        """测试 message 作为字符串"""
        error = VoiceStudioError(
            code="TEST",
            message="错误消息",
            status_code=400
        )

        assert str(error) == "错误消息"


class TestFileTooLargeError:
    """文件过大异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = FileTooLargeError(
            actual_size=100 * 1024 * 1024,  # 100MB
            max_size=50 * 1024 * 1024  # 50MB
        )

        assert error.code == "FILE_TOO_LARGE"
        assert error.status_code == 413
        assert "50MB" in error.message
        assert "100.00MB" in error.detail

    def test_error_message_format(self):
        """测试错误消息格式"""
        error = FileTooLargeError(
            actual_size=75 * 1024 * 1024,
            max_size=50 * 1024 * 1024
        )

        assert "最大 50MB" in error.message


class TestUnsupportedFileTypeError:
    """不支持的文件类型异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = UnsupportedFileTypeError(
            file_type=".exe",
            allowed=[".mp3", ".wav", ".flac"]
        )

        assert error.code == "UNSUPPORTED_FILE_TYPE"
        assert error.status_code == 400
        assert ".exe" in error.detail
        assert ".mp3" in error.message

    def test_error_shows_allowed_types(self):
        """测试显示允许的类型"""
        error = UnsupportedFileTypeError(
            file_type=".xyz",
            allowed=[".mp3", ".wav"]
        )

        assert ".mp3" in error.message
        assert ".wav" in error.message


class TestEmptyFileError:
    """空文件异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = EmptyFileError()

        assert error.code == "EMPTY_FILE"
        assert error.status_code == 400
        assert "空" in error.message


class TestTextTooLongError:
    """文本过长异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = TextTooLongError(
            actual_length=10000,
            max_length=5000
        )

        assert error.code == "TEXT_TOO_LONG"
        assert error.status_code == 400
        assert "5000" in error.message
        assert "10000" in error.detail

    def test_error_message_format(self):
        """测试错误消息格式"""
        error = TextTooLongError(
            actual_length=6000,
            max_length=5000
        )

        assert "最大 5000 字符" in error.message


class TestEmptyTextError:
    """空文本异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = EmptyTextError()

        assert error.code == "EMPTY_TEXT"
        assert error.status_code == 400
        assert "不能为空" in error.message


class TestInvalidParameterError:
    """无效参数异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = InvalidParameterError(
            param_name="rate",
            message="格式无效"
        )

        assert error.code == "INVALID_PARAMETER"
        assert error.status_code == 422
        assert "rate" in error.message
        assert "格式无效" in error.message

    def test_error_with_detail(self):
        """测试带详情的异常"""
        error = InvalidParameterError(
            param_name="volume",
            message="必须是 +/-N% 格式",
            detail="实际值: 50%"
        )

        assert error.detail == "实际值: 50%"


class TestEngineNotAvailableError:
    """引擎不可用异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = EngineNotAvailableError("whisper-cloud")

        assert error.code == "ENGINE_NOT_AVAILABLE"
        assert error.status_code == 503
        assert "whisper-cloud" in error.message


class TestTranscriptionError:
    """转写失败异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = TranscriptionError()

        assert error.code == "TRANSCRIPTION_FAILED"
        assert error.status_code == 500
        assert "语音转文字失败" in error.message

    def test_error_with_detail(self):
        """测试带详情的异常"""
        error = TranscriptionError(detail="音频格式不支持")

        assert error.detail == "音频格式不支持"


class TestSynthesisError:
    """合成失败异常测试"""

    def test_error_creation(self):
        """测试创建异常"""
        error = SynthesisError()

        assert error.code == "SYNTHESIS_FAILED"
        assert error.status_code == 500
        assert "文字转语音失败" in error.message

    def test_error_with_detail(self):
        """测试带详情的异常"""
        error = SynthesisError(detail="音色不存在")

        assert error.detail == "音色不存在"


class TestExceptionHierarchy:
    """异常继承关系测试"""

    def test_all_exceptions_inherit_from_base(self):
        """测试所有异常继承自基类"""
        exceptions = [
            FileTooLargeError(100, 50),
            UnsupportedFileTypeError(".exe", [".mp3"]),
            EmptyFileError(),
            TextTooLongError(100, 50),
            EmptyTextError(),
            InvalidParameterError("test", "test"),
            EngineNotAvailableError("test"),
            TranscriptionError(),
            SynthesisError(),
        ]

        for exc in exceptions:
            assert isinstance(exc, VoiceStudioError)
            assert isinstance(exc, Exception)

    def test_exception_can_be_raised(self):
        """测试异常可以被抛出"""
        with pytest.raises(VoiceStudioError) as exc_info:
            raise FileTooLargeError(100, 50)

        assert exc_info.value.code == "FILE_TOO_LARGE"

    def test_exception_can_be_caught_by_base_class(self):
        """测试异常可以被基类捕获"""
        with pytest.raises(VoiceStudioError):
            raise TextTooLongError(100, 50)

    def test_exception_can_be_caught_by_exception(self):
        """测试异常可以被 Exception 捕获"""
        with pytest.raises(Exception):
            raise EmptyTextError()